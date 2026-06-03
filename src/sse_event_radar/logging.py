import sys
from pathlib import Path

from loguru import logger

from sse_event_radar.config import settings


def setup_logging() -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    )
    logger.add(
        "logs/app.log",
        rotation="20 MB",
        retention="14 days",
        level=settings.log_level,
        encoding="utf-8",
    )
