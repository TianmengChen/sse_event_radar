import argparse

from loguru import logger

from sse_event_radar.logging import setup_logging
from sse_event_radar.network import configure_proxy
from sse_event_radar.services.buy_signal_pipeline import BuySignalPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Run buy signal pipeline.")
    parser.add_argument("--watchlist", default="config/watchlist.yaml")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    configure_proxy()

    args = parse_args()

    pipeline = BuySignalPipeline(watchlist_path=args.watchlist)
    result = pipeline.run(dry_run=args.dry_run)

    logger.info(f"Pipeline result: {result}")


if __name__ == "__main__":
    main()