from loguru import logger

from sse_event_radar.alerts.models import Alert, RelatedStock
from sse_event_radar.alerts.service import AlertService
from sse_event_radar.collectors.quotes import fetch_single_quote
from sse_event_radar.models.news import make_news_item_from_text
from sse_event_radar.processors.event_extractor import SimpleEventExtractor
from sse_event_radar.processors.stock_mapper import StockMapper


class EventDrivenPipeline:
    def __init__(
        self,
        stock_knowledge_path: str = "config/stock_knowledge.yaml",
        top_n: int = 8,
    ):
        self.extractor = SimpleEventExtractor()
        self.mapper = StockMapper(stock_knowledge_path)
        self.alert_service = AlertService()
        self.top_n = top_n

    def run(
        self,
        text: str,
        title: str | None = None,
        dry_run: bool = False,
    ) -> dict:
        logger.info("Running event-driven pipeline...")

        news = make_news_item_from_text(text=text, title=title)
        event = self.extractor.extract(news)

        logger.info(f"Integrated event: {event.model_dump()}")

        candidates = self.mapper.map_event_to_candidates(event, top_n=self.top_n)
        logger.info(f"Mapped candidates: {len(candidates)}")

        if not candidates:
            logger.warning("No candidate stocks matched this event.")
            return {
                "event": event.model_dump(),
                "candidate_count": 0,
                "sent": 0,
                "dry_run": dry_run,
            }

        quote_rows = []
        related_stocks = []
        risk_flags = [
            "这是事件驱动候选，不是自动买入指令。",
            "需要人工确认新闻真实性、政策强度、板块环境和分时走势。",
        ]

        for candidate in candidates:
            quote = None
            try:
                quote = fetch_single_quote(candidate.code)
                quote_rows.append(quote)
                logger.info(
                    f"Fetched quote {candidate.code} {quote.get('name')} "
                    f"pct_chg={quote.get('pct_chg')} amount={quote.get('amount')}"
                )
            except Exception as exc:
                logger.warning(f"Failed to fetch quote for {candidate.code}: {exc}")

            reason = candidate.reason

            if quote:
                pct_chg = quote.get("pct_chg")
                amount = quote.get("amount")
                price = quote.get("price")

                reason += f"；当前价格 {price}，涨幅 {pct_chg}%"

                if amount is not None:
                    reason += f"，成交额约 {amount / 100000000:.2f} 亿"

                # Hard risk filters
                if candidate.security_type == "etf":
                    if pct_chg is not None and pct_chg > 4:
                        risk_flags.append(f"{candidate.code} ETF 涨幅已超过 4%，注意追高。")
                else:
                    if pct_chg is not None and pct_chg > 7:
                        risk_flags.append(f"{candidate.code} 股票涨幅已超过 7%，注意追高。")

            related_stocks.append(
                RelatedStock(
                    code=candidate.code,
                    name=candidate.name,
                    reason=reason,
                    relevance_score=candidate.match_score,
                )
            )

        direction = "positive" if event.direction_hint == "positive" else "uncertain"

        alert = Alert(
            level="B" if direction == "positive" else "C",
            title=f"事件驱动候选：{event.title[:50]}",
            summary=(
                f"事件摘要：{event.summary}\n\n"
                f"事件类型：{event.event_type}\n"
                f"方向提示：{event.direction_hint}\n"
                f"影响行业：{', '.join(event.affected_industries) or '未识别'}\n"
                f"关键词：{', '.join(event.keywords) or '未识别'}"
            ),
            direction=direction,
            market="SSE",
            event_type="event_driven_candidate",
            time_horizon="intraday / 1-5 trading days",
            source=event.source,
            source_url=event.source_url,
            related_stocks=related_stocks,
            risk_flags=risk_flags,
            confidence=event.confidence,
        )

        if dry_run:
            logger.info("[DRY RUN] Alert generated but not sent.")
            logger.info(alert.model_dump())
            return {
                "event": event.model_dump(),
                "candidate_count": len(candidates),
                "quote_count": len(quote_rows),
                "sent": 0,
                "dry_run": True,
            }

        ok = self.alert_service.send_alert(alert)

        return {
            "event": event.model_dump(),
            "candidate_count": len(candidates),
            "quote_count": len(quote_rows),
            "sent": 1 if ok else 0,
            "dry_run": False,
        }