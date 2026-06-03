from pathlib import Path

from loguru import logger

from sse_event_radar.db.session import init_db
from sse_event_radar.logging import setup_logging
from sse_event_radar.network import configure_proxy


def run_collector(name, collector, output_name):
    outdir = Path("data/raw")
    outdir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Testing {name}...")

    try:
        df = collector.collect()
        logger.info(f"{name} rows: {len(df)}")
        df.head(50).to_csv(outdir / output_name, index=False, encoding="utf-8-sig")
        logger.success(f"{name} finished. Saved to data/raw/{output_name}")
        return True

    except Exception as exc:
        logger.exception(f"{name} failed: {exc}")
        return False


def main() -> None:
    setup_logging()
    configure_proxy()
    init_db()

    from sse_event_radar.collectors.announcements import AnnouncementCollector
    from sse_event_radar.collectors.quotes import SSEQuoteCollector
    from sse_event_radar.collectors.stock_master import StockMasterCollector

    results = {
        "stock_master": run_collector(
            "Eastmoney SSE stock master collector",
            StockMasterCollector(page_size=100, max_pages=2),
            "stock_master_sample.csv",
        ),
        "quotes": run_collector(
            "Eastmoney SSE quote collector",
            SSEQuoteCollector(page_size=100, max_pages=2),
            "sse_quotes_sample.csv",
        ),
        "announcements": run_collector(
            "AKShare announcement collector",
            AnnouncementCollector(symbol="全部"),
            "announcements_sample.csv",
        ),
    }

    logger.info(f"Smoke test summary: {results}")

    if not any(results.values()):
        raise RuntimeError("All collectors failed.")


if __name__ == "__main__":
    main()