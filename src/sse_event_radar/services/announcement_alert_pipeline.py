import json
import hashlib
from pathlib import Path

from loguru import logger

from sse_event_radar.alerts.models import Alert
from sse_event_radar.alerts.service import AlertService
from sse_event_radar.collectors.announcements import AnnouncementCollector
from sse_event_radar.processors.announcement_rules import AnnouncementRuleProcessor


class AnnouncementAlertPipeline:
    def __init__(
        self,
        symbol: str = "全部",
        date: str | None = None,
        dedup_path: str = "data/processed/sent_announcement_alerts.json",
    ):
        self.symbol = symbol
        self.date = date
        self.collector = AnnouncementCollector(symbol=symbol, date=date)
        self.processor = AnnouncementRuleProcessor()
        self.alert_service = AlertService()
        self.dedup_path = Path(dedup_path)

    def run(self, dry_run: bool = False, limit: int | None = None) -> dict:
        logger.info("Running announcement alert pipeline...")

        df = self.collector.collect()
        logger.info(f"Collected announcements: {len(df)}")

        alerts = self.processor.process_dataframe(df)
        logger.info(f"Generated candidate alerts: {len(alerts)}")

        if limit is not None:
            alerts = alerts[:limit]

        sent_hashes = self._load_sent_hashes()
        new_alerts = []

        for alert in alerts:
            alert_hash = self._hash_alert(alert)
            if alert_hash in sent_hashes:
                continue
            new_alerts.append((alert_hash, alert))

        logger.info(f"New alerts after dedup: {len(new_alerts)}")

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
            "announcements": len(df),
            "candidate_alerts": len(alerts),
            "new_alerts": len(new_alerts),
            "sent": sent_count,
            "failed": failed_count,
            "dry_run": dry_run,
        }

    def _load_sent_hashes(self) -> set[str]:
        if not self.dedup_path.exists():
            return set()

        try:
            data = json.loads(self.dedup_path.read_text(encoding="utf-8"))
            return set(data)
        except Exception:
            logger.warning("Failed to load dedup file. Starting with empty dedup set.")
            return set()

    def _save_sent_hashes(self, hashes: set[str]) -> None:
        self.dedup_path.parent.mkdir(parents=True, exist_ok=True)
        data = sorted(hashes)
        self.dedup_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _hash_alert(alert: Alert) -> str:
        stocks = ",".join([stock.code for stock in alert.related_stocks])
        raw = f"{alert.level}|{alert.title}|{alert.source_url}|{stocks}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()