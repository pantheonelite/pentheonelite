"""Market event scheduler for triggering council debate cycles."""

import asyncio
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


class MarketScheduler:
    """
    Hybrid scheduler for council cycles.

    Triggers council debate cycles based on:
    1. Time-based schedule (e.g., every 4 hours)
    2. Market events (e.g., price change >1%)
    """

    def __init__(self, orchestrator=None):
        """
        Initialize market scheduler.

        Parameters
        ----------
        orchestrator : CouncilOrchestrator | None
            Orchestrator to trigger
        """
        self.orchestrator = orchestrator
        # Default settings
        self.schedule_interval = 14400  # 4 hours in seconds
        self.price_change_threshold = 0.01  # 1% price change
        self.min_trigger_interval = 1800  # 30 minutes minimum between triggers

        # Track last trigger times per council to implement debouncing
        self.last_trigger_times: dict[int, datetime] = {}

        # Track price changes for event triggering
        self.price_history: dict[str, list[tuple[datetime, float]]] = defaultdict(list)

        # WebSocket client for price monitoring (optional for Phase 1)
        self.ws_client = None

        logger.info("Market scheduler initialized", websocket_available=False)

    async def schedule_time_based(
        self,
        council_id: int,
        interval_seconds: int | None = None,
    ):
        """
        Schedule time-based cycles for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        interval_seconds : int | None
            Interval in seconds. If None, uses settings default.
        """
        if interval_seconds is None:
            interval_seconds = self.schedule_interval

        logger.info(
            "Starting time-based schedule",
            council_id=council_id,
            interval_seconds=interval_seconds,
        )

        while True:
            try:
                # Check if enough time has passed since last trigger
                if await self._should_trigger_cycle(council_id, "time_based"):
                    logger.info("Triggering time-based cycle", council_id=council_id)

                    if self.orchestrator:
                        await self.orchestrator.run_council_cycle(council_id)

                    self.last_trigger_times[council_id] = datetime.now(UTC)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(
                    "Error in time-based schedule",
                    council_id=council_id,
                    error=str(e),
                    exc_info=True,
                )
                # Wait before retrying
                await asyncio.sleep(60)

    async def monitor_price_events(
        self,
        symbols: list[str],
        council_ids: list[int],
    ):
        """
        Monitor price changes and trigger cycles on significant events.

        Parameters
        ----------
        symbols : list[str]
            Symbols to monitor (e.g., ["BTCUSDT", "ETHUSDT"])
        council_ids : list[int]
            Council IDs to trigger
        """
        logger.info(
            "Starting price event monitoring",
            symbols=symbols,
            council_count=len(council_ids),
        )

        logger.warning(
            "WebSocket price monitoring not implemented yet - using time-based scheduling only",
            note="Phase 1: Event triggers will be added in future update",
        )

        # For Phase 1: Just keep the scheduler alive without WebSocket monitoring
        # This will be implemented when full ASTER WebSocket integration is complete
        try:
            while True:
                await asyncio.sleep(60)  # Keep alive

        except Exception as e:
            logger.error(
                "Error in price event monitoring",
                error=str(e),
                exc_info=True,
            )

    async def _handle_price_update(
        self,
        ticker_data,
        council_ids: list[int],
    ):
        """
        Handle price update and check for significant changes.

        Parameters
        ----------
        ticker_data : dict
            Ticker data from WebSocket
        council_ids : list[int]
            Council IDs to potentially trigger
        """
        try:
            symbol = ticker_data.get("symbol")
            price = ticker_data.get("price")

            if not symbol or not price:
                return

            # Add to price history
            now = datetime.now(UTC)
            self.price_history[symbol].append((now, price))

            # Keep only recent history (last 10 minutes)
            cutoff_time = now - timedelta(minutes=10)
            self.price_history[symbol] = [(ts, p) for ts, p in self.price_history[symbol] if ts > cutoff_time]

            # Check for significant price change
            if await self._is_significant_price_change(symbol):
                logger.info(
                    "Significant price change detected",
                    symbol=symbol,
                    current_price=price,
                )

                # Trigger cycles for all councils if debounce allows
                for council_id in council_ids:
                    if await self._should_trigger_cycle(council_id, "price_event"):
                        logger.info(
                            "Triggering price event cycle",
                            council_id=council_id,
                            symbol=symbol,
                        )

                        if self.orchestrator:
                            # Run cycle in background
                            asyncio.create_task(self.orchestrator.run_council_cycle(council_id))

                        self.last_trigger_times[council_id] = now

        except Exception as e:
            logger.error(
                "Error handling price update",
                error=str(e),
                exc_info=True,
            )

    async def _is_significant_price_change(self, symbol: str) -> bool:
        """
        Check if price has changed significantly.

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        bool
            True if price change exceeds threshold
        """
        if len(self.price_history[symbol]) < 2:
            return False

        # Get price from 5 minutes ago
        now = datetime.now(UTC)
        five_min_ago = now - timedelta(minutes=5)

        recent_prices = [price for ts, price in self.price_history[symbol] if ts >= five_min_ago]

        if len(recent_prices) < 2:
            return False

        # Calculate percentage change
        old_price = recent_prices[0]
        current_price = recent_prices[-1]
        pct_change = abs((current_price - old_price) / old_price)

        threshold = self.price_change_threshold

        return pct_change >= threshold

    async def _should_trigger_cycle(
        self,
        council_id: int,
        trigger_type: str,
    ) -> bool:
        """
        Check if cycle should be triggered based on debouncing rules.

        Parameters
        ----------
        council_id : int
            Council ID
        trigger_type : str
            Type of trigger ("time_based" or "price_event")

        Returns
        -------
        bool
            True if cycle should be triggered
        """
        # Check last trigger time
        if council_id not in self.last_trigger_times:
            return True

        last_trigger = self.last_trigger_times[council_id]
        now = datetime.now(UTC)
        time_since_last = (now - last_trigger).total_seconds()

        # For event-based triggers, enforce minimum interval
        if trigger_type == "price_event":
            min_interval = self.min_trigger_interval
            if time_since_last < min_interval:
                logger.debug(
                    "Skipping trigger due to min interval",
                    council_id=council_id,
                    time_since_last=time_since_last,
                    min_interval=min_interval,
                )
                return False

        return True

    async def stop(self):
        """Stop the scheduler and close WebSocket connections."""
        logger.info("Stopping market scheduler")

        if self.ws_client:
            try:
                await self.ws_client.close()
            except Exception as e:
                logger.warning("Error closing WebSocket client", error=str(e))
