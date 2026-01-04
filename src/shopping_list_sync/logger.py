"""Logging configuration for Shopping List Sync."""

import sys
from pathlib import Path

from loguru import logger

from shopping_list_sync.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    # Remove default handler
    logger.remove()

    # Add stderr handler with appropriate log level
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Add file handler if configured
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            rotation="1 week",
            retention="1 month",
            compression="zip",
            level=settings.LOG_LEVEL
        )


# Configure logging when module is imported
setup_logging()
