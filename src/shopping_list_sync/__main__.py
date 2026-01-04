"""Command-line interface for Shopping List Sync."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from shopping_list_sync.config import get_config_summary
from shopping_list_sync.sync import ShoppingListSync


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automatically organize Todoist shopping lists using AI",
        epilog="Example: shopping-sync --interval 120 --log-level DEBUG"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Sync interval in seconds (default: from config or 60)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom categories.yaml"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: from config or INFO)"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Path to log file (optional)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run health check and exit"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run sync once and exit (no scheduler)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    args = parser.parse_args()

    # Update config if CLI arguments provided
    if args.log_level:
        from shopping_list_sync.config import settings
        settings.LOG_LEVEL = args.log_level

    if args.log_file:
        from shopping_list_sync.config import settings
        settings.LOG_FILE = args.log_file

    if args.config:
        from shopping_list_sync.config import settings
        settings.CATEGORIES_FILE = str(args.config)

    # Re-setup logging with potentially updated settings
    from shopping_list_sync.logger import setup_logging
    setup_logging()

    # Display startup information
    logger.info("=" * 60)
    logger.info("Shopping List Sync v1.0.0")
    logger.info("=" * 60)
    logger.info(get_config_summary())

    # Initialize sync manager
    try:
        sync = ShoppingListSync(sync_interval=args.interval)
    except Exception as e:
        logger.error(f"Failed to initialize sync manager: {e}")
        logger.exception(e)
        sys.exit(1)

    # Health check mode
    if args.check:
        logger.info("Running health check...")
        if sync.health_check():
            logger.info("✓ Health check passed!")
            sys.exit(0)
        else:
            logger.error("✗ Health check failed!")
            sys.exit(1)

    # One-time sync mode
    if args.once:
        logger.info("Running one-time sync...")
        try:
            sync.check_and_sync()
            logger.info("One-time sync completed successfully")
            sys.exit(0)
        except Exception as e:
            logger.error(f"One-time sync failed: {e}")
            logger.exception(e)
            sys.exit(1)

    # Daemon mode (default)
    logger.info(f"Starting daemon mode with {sync.sync_interval}s interval...")
    logger.info("Press Ctrl+C to stop")
    logger.info("-" * 60)

    try:
        sync.start()
    except Exception as e:
        logger.error(f"Daemon failed: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
