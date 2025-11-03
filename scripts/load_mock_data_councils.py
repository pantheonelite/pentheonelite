"""CLI script to load mock crypto council data into the database."""

import argparse
import asyncio
import logging
import sys

import structlog

from app.backend.db.session_manager import session_manager
from app.backend.services.crypto_council_mock_data import CryptoCouncilMockDataService

logger = structlog.get_logger(__name__)


async def load_mock_data(replace_existing: bool = False, count: int | None = None):
    """
    Load crypto council mock data into the database.

    Parameters
    ----------
    replace_existing : bool
        If True, replace existing councils. If False, skip if they exist.
    count : int | None
        Number of councils to load. If None, loads all available councils.

    Returns
    -------
    bool
        True if data was loaded successfully, False otherwise.
    """
    try:
        async with session_manager.session(scoped=True) as session:
            total_councils = len(CryptoCouncilMockDataService.CRYPTO_COUNCIL_CONFIGS)
            if count is not None:
                logger.info(
                    "Loading %d out of %d available councils...", count, total_councils
                )
            else:
                logger.info("Loading all %d available councils...", total_councils)

            success = await CryptoCouncilMockDataService.load_crypto_mock_data(
                session=session, replace_existing=replace_existing, count=count
            )

            if success:
                logger.info("✅ Mock data loaded successfully")
                return True
            logger.warning("Mock data loading was skipped (councils already exist)")
            return True

    except Exception:
        logger.exception("Failed to load mock data")
        return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load crypto council mock data into the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all mock data (skip if exists)
  python load_mock_data_councils.py

  # Load only 3 councils
  python load_mock_data_councils.py --count 3

  # Replace existing mock data
  python load_mock_data_councils.py --replace

  # Load 5 councils and replace existing
  python load_mock_data_councils.py --count 5 --replace

  # With custom log level
  python load_mock_data_councils.py --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing councils (default: skip if they exist)",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of councils to load (default: all available councils)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-format",
        type=str,
        default="console",
        choices=["console", "json"],
        help="Logging format: console (human-readable) or json (machine-parseable)",
    )

    args = parser.parse_args()

    # Configure logging based on output format
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Use console renderer for human-readable output, JSON for machine parsing
    if args.log_format == "console":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(message)s",
    )

    # Load mock data
    success = await load_mock_data(replace_existing=args.replace, count=args.count)

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Mock data loading interrupted by user")
        sys.exit(1)
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
