import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml
from loguru import logger

from sse_event_radar.alerts.models import Alert
from sse_event_radar.alerts.service import AlertService
from sse_event_radar.processors.buy_signal_rules import BuySignalRuleProcessor
from sse_event_radar.collectors.quotes import fetch_single_quote


class BuySignalPipeline:
    def __init__(
        self,
        watchlist_path: str = "config/watchlist.yaml",
        dedup_path: str = "data/processed/sent_buy_signal_alerts.json",
    ):
        self.watchlist_path = Path(watchlist_path)
        self.dedup_path = Path(dedup_path)
        self.alert_service = AlertService()

        watchlist_config = self._load_watchlist()
        settings = watchlist_config.get("settings", {})

        self.watchlist = watchlist_config.get("stocks", [])
        self.watch_codes = {str(item["code"]).zfill(6) for item in self.watchlist}

        self.processor = BuySignalRuleProcessor(
            min_pct_chg=float(settings.get("min_pct_chg", 1.0)),
            max_pct_chg_main=float(settings.get("max_pct_chg_main", 6.0)),
            max_pct_chg_star=float(settings.get("max_pct_chg_star", 12.0)),
            max_pct_chg_etf=float(settings.get("max_pct_chg_etf", 5.0)),
            min_amount=float(settings.get("min_amount", 100_000_000)),
        )

    def run(self, dry_run: bool = False) -> dict:
        logger.info("Running buy signal pipeline...")
        
        quotes = []

        for code in sorted(self.watch_codes):
            try:
                quote = fetch_single_quote(code)
                quotes.append(quote)
                logger.info(f"Fetched quote for {code}: {quote.get('name')} {quote.get('pct_chg')}")
            except Exception as exc:
                logger.exception(f"Failed to fetch quote for {code}: {exc}")

        watch_df = pd.DataFrame(quotes)
        logger.info(f"Watchlist quote rows: {len(watch_df)}")

        candidate_alerts: list[Alert] = []

        for _, row in watch_df.iterrows():
            quote = row.to_dict()
            result = self.processor.evaluate_quote(quote)
            logger.info(f"{quote.get('code')} {quote.get('name')} => {result.action}: {result.reason}")

            alert = self.processor.build_alert(quote, result)
            if alert is not None:
                candidate_alerts.append(alert)

        sent_hashes = self._load_sent_hashes()
        new_alerts: list[tuple[str, Alert]] = []

        for alert in candidate_alerts:
            alert_hash = self._hash_alert(alert)
            if alert_hash in sent_hashes:
                continue
            new_alerts.append((alert_hash, alert))

        logger.info(f"Candidate buy alerts: {len(candidate_alerts)}")
        logger.info(f"New buy alerts after dedup: {len(new_alerts)}")

        sent_count = 0
        failed_count = 0

        for alert_hash, alert in new_alerts:
            if dry_run:
                logger.info(f"[DRY RUN] {alert.level} | {alert.title}")
                continue

            ok = self.alert_service.send_alert(alert)
            if ok:
                sent_hashes.add(alert_hash)
                sent_count += 1
            else:
                failed_count += 1

        if not dry_run:
            self._save_sent_hashes(sent_hashes)

        return {
            "watchlist_size": len(self.watch_codes),
            "watchlist_quotes": len(watch_df),
            "candidate_buy_alerts": len(candidate_alerts),
            "new_alerts": len(new_alerts),
            "sent": sent_count,
            "failed": failed_count,
            "dry_run": dry_run,
        }

    def _load_watchlist(self) -> dict:
        if not self.watchlist_path.exists():
            raise FileNotFoundError(f"Watchlist not found: {self.watchlist_path}")

        return yaml.safe_load(self.watchlist_path.read_text(encoding="utf-8")) or {}

    def _load_sent_hashes(self) -> set[str]:
        if not self.dedup_path.exists():
            return set()

        try:
            data = json.loads(self.dedup_path.read_text(encoding="utf-8"))
            return set(data)
        except Exception:
            logger.warning("Failed to load buy signal dedup file. Starting empty.")
            return set()

    def _save_sent_hashes(self, hashes: set[str]) -> None:
        self.dedup_path.parent.mkdir(parents=True, exist_ok=True)
        self.dedup_path.write_text(
            json.dumps(sorted(hashes), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _hash_alert(alert: Alert) -> str:
        from datetime import datetime

        stocks = ",".join([stock.code for stock in alert.related_stocks])

        now = datetime.now()
        dedup_window = f"{now:%Y%m%d_%H}"

        raw = f"{dedup_window}|{alert.event_type}|{alert.level}|{alert.title}|{stocks}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()