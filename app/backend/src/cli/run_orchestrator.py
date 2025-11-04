"""CLI entry point for running the council orchestrator daemon."""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import structlog
from app.backend.api.routers.websocket import websocket_manager
from app.backend.services.council_orchestrator import CouncilOrchestrator
from app.backend.services.market_scheduler import MarketScheduler

logger = structlog.get_logger(__name__)


class OrchestratorDaemon:
    """
    Daemon for running council orchestrator.

    Manages the lifecycle of the orchestrator and scheduler.
    """

    def __init__(
        self,
        council_ids: list[int] | None = None,
        schedule_interval_seconds: int | None = None,
        *,
        enable_event_triggers: bool = True,
        paper_trading: bool = False,
        symbols: list[str] | None = None,
    ):
        """
        Initialize orchestrator daemon.

        Parameters
        ----------
        council_ids : list[int] | None
            Specific council IDs to run. If None, runs all system councils.
        schedule_interval_seconds : int | None
            Seconds between cycles. If None, uses default (14400 seconds = 4 hours).
        enable_event_triggers : bool
            Enable price event-based triggers.
        paper_trading : bool
            If True, simulates trades without executing real orders via Aster API
        symbols : list[str] | None
            Override trading symbols for all councils. If None, uses council config.
        """
        self.council_ids = council_ids
        self.schedule_interval_seconds = schedule_interval_seconds
        self.enable_event_triggers = enable_event_triggers
        self.paper_trading = paper_trading
        self.symbols = symbols

        self.orchestrator: CouncilOrchestrator | None = None
        self.scheduler: MarketScheduler | None = None
        self.running = False
        self.shutdown_event = asyncio.Event()

    def _setup_signal_handlers(self):
        """Setup asyncio-compatible signal handlers."""
        loop = asyncio.get_event_loop()

        def signal_handler():
            """Handle shutdown signals gracefully."""
            logger.info("Received shutdown signal (Ctrl+C)")
            self.running = False
            self.shutdown_event.set()

        try:
            # Add signal handlers for both SIGINT (Ctrl+C) and SIGTERM
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
            logger.debug("Signal handlers registered successfully")
        except NotImplementedError:
            # Signal handlers not supported on this platform (e.g., Windows)
            logger.warning("Signal handlers not supported on this platform. Use Ctrl+C to interrupt.")

    async def start(self):
        """Start the orchestrator daemon."""
        logger.info(
            "Starting orchestrator daemon",
            council_ids=self.council_ids,
            schedule_interval_seconds=self.schedule_interval_seconds,
            schedule_interval_hours=(
                self.schedule_interval_seconds / 3600 if self.schedule_interval_seconds else None
            ),
            enable_event_triggers=self.enable_event_triggers,
            paper_trading=self.paper_trading,
            symbols=self.symbols,
        )

        try:
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Initialize orchestrator with schedule interval if provided
            orchestrator_kwargs = {
                "symbols_override": self.symbols,
            }
            if self.schedule_interval_seconds is not None:
                orchestrator_kwargs["schedule_interval_seconds"] = self.schedule_interval_seconds

            self.orchestrator = CouncilOrchestrator(**orchestrator_kwargs)
            self.orchestrator.websocket_manager = websocket_manager

            # Initialize scheduler
            self.scheduler = MarketScheduler(orchestrator=self.orchestrator)

            self.running = True

            # Create orchestrator task
            if self.council_ids:
                # Run specific councils
                orchestrator_task = asyncio.create_task(self.orchestrator.start(council_ids=self.council_ids))
            else:
                # Run all system councils
                orchestrator_task = asyncio.create_task(self.orchestrator.start())

            # Wait for shutdown signal or orchestrator to complete
            await asyncio.wait(
                [orchestrator_task, asyncio.create_task(self.shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # If shutdown event was triggered, cancel the orchestrator task
            if self.shutdown_event.is_set() and not orchestrator_task.done():
                logger.info("Cancelling orchestrator task...")
                orchestrator_task.cancel()
                try:
                    await orchestrator_task
                except asyncio.CancelledError:
                    logger.info("Orchestrator task cancelled successfully")

        except asyncio.CancelledError:
            logger.info("Orchestrator cancelled")
        except Exception:
            logger.exception("Error in orchestrator daemon")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the orchestrator daemon."""
        logger.info("Stopping orchestrator daemon")

        if self.orchestrator:
            await self.orchestrator.stop()

        if self.scheduler:
            await self.scheduler.stop()

        logger.info("Orchestrator daemon stopped")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the council orchestrator daemon for live trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all system councils with default settings (4 hours interval)
  python run_orchestrator.py

  # Run specific councils
  python run_orchestrator.py --councils 1,2,3

  # Override trading symbols for all councils
  python run_orchestrator.py --symbols BTCUSDT,ETHUSDT,SOLUSDT

  # Custom schedule interval (in seconds) - 1 minute for testing
  python run_orchestrator.py --schedule-interval 60

  # Custom schedule interval - 1 hour
  python run_orchestrator.py --schedule-interval 3600

  # Custom schedule interval - 6 hours
  python run_orchestrator.py --schedule-interval 21600

  # Paper trading mode (simulate orders without real execution)
  python run_orchestrator.py --paper-trading

  # Paper trading with specific symbols and 5 minute interval
  python run_orchestrator.py --paper-trading --symbols BTCUSDT,ETHUSDT --schedule-interval 300

  # Disable event triggers (time-based only)
  python run_orchestrator.py --no-event-triggers
        """,
    )

    parser.add_argument(
        "--councils",
        type=str,
        default=None,
        help="Comma-separated list of council IDs to run (default: all system councils)",
    )

    parser.add_argument(
        "--schedule-interval",
        type=int,
        default=None,
        help="Seconds between scheduled cycles (default: 14400 = 4 hours). Use 60 for 1 minute, 3600 for 1 hour.",
    )

    parser.add_argument(
        "--no-event-triggers",
        action="store_true",
        help="Disable price event-based triggers (time-based only)",
    )

    parser.add_argument(
        "--paper-trading",
        action="store_true",
        help="Enable paper trading mode (simulate orders without real execution)",
    )

    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Override trading symbols (comma-separated, e.g., BTCUSDT,ETHUSDT). If not provided, uses council config.",
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

    # Print startup banner FIRST (before any logging)
    sys.stdout.flush()  # Ensure banner prints before logging starts

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
        # Terminal output - use console renderer with colors
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # File/pipe output - use JSON renderer
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

    # Parse council IDs
    council_ids = None
    if args.councils:
        try:
            if args.councils.lower() == "all":
                council_ids = None
            else:
                council_ids = [int(cid.strip()) for cid in args.councils.split(",")]
        except ValueError:
            logger.exception("Invalid council IDs format. Use comma-separated integers.")
            sys.exit(1)

    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
        logger.info("Symbol override enabled", symbols=symbols)

    logger.info("🔧 Configuration loaded", council_ids=council_ids)

    # Create and start daemon
    daemon = OrchestratorDaemon(
        council_ids=council_ids,
        schedule_interval_seconds=args.schedule_interval,
        enable_event_triggers=not args.no_event_triggers,
        paper_trading=args.paper_trading,
        symbols=symbols,
    )

    if args.paper_trading:
        logger.warning("⚠️  PAPER TRADING MODE ENABLED - No real orders will be placed")
    else:
        logger.info("💰 LIVE TRADING MODE - Real orders will be placed")

    logger.info("Initializing orchestrator daemon...")

    try:
        await daemon.start()
    except Exception:
        logger.exception("Fatal error in orchestrator")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Use asyncio.run() which properly handles KeyboardInterrupt
        asyncio.run(main())
    except KeyboardInterrupt:
        # This will catch Ctrl+C if signal handlers don't work
        sys.exit(0)
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
