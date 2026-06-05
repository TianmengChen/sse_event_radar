import argparse

from loguru import logger

from sse_event_radar.logging import setup_logging
from sse_event_radar.network import configure_proxy
from sse_event_radar.services.event_driven_pipeline import EventDrivenPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Run event-driven stock candidate pipeline.")
    parser.add_argument("--text", required=True, help="News/policy/announcement text.")
    parser.add_argument("--title", default=None, help="Optional title.")
    parser.add_argument("--stock-knowledge", default="config/stock_knowledge.yaml")
    parser.add_argument("--top-n", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    configure_proxy()

    args = parse_args()

    pipeline = EventDrivenPipeline(
        stock_knowledge_path=args.stock_knowledge,
        top_n=args.top_n,
    )

    result = pipeline.run(
        text=args.text,
        title=args.title,
        dry_run=args.dry_run,
    )

    logger.info(f"Pipeline result: {result}")


if __name__ == "__main__":
    main()