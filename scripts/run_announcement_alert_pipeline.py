import argparse

from loguru import logger

from sse_event_radar.logging import setup_logging
from sse_event_radar.network import configure_proxy
from sse_event_radar.services.announcement_alert_pipeline import AnnouncementAlertPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Run announcement alert pipeline.")
    parser.add_argument("--symbol", default="全部", help="AKShare announcement symbol/category.")
    parser.add_argument("--date", default=None, help="Date in YYYYMMDD format. Default: today.")
    parser.add_argument("--dry-run", action="store_true", help="Do not send notifications.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of alerts.")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    configure_proxy()

    args = parse_args()

    pipeline = AnnouncementAlertPipeline(
        symbol=args.symbol,
        date=args.date,
    )

    result = pipeline.run(
        dry_run=args.dry_run,
        limit=args.limit,
    )

    logger.info(f"Pipeline result: {result}")


if __name__ == "__main__":
    main()