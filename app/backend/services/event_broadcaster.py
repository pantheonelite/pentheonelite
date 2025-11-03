"""Event broadcaster service - handles WebSocket event broadcasting."""

from datetime import UTC, datetime

import structlog

logger = structlog.get_logger(__name__)


class EventBroadcaster:
    """
    Service for broadcasting council events via WebSocket.

    Handles:
    - Consensus decision broadcasts
    - Trade execution broadcasts
    - Cycle completion broadcasts
    - Event payload formatting
    """

    def __init__(self, websocket_manager):
        """
        Initialize the event broadcaster.

        Parameters
        ----------
        websocket_manager
            WebSocket manager for broadcasting events
        """
        self.websocket_manager = websocket_manager

    async def abroadcast_consensus(self, council, consensus: dict):
        """
        Broadcast consensus decision event.

        Parameters
        ----------
        council : Council
            Council object
        consensus : dict
            Consensus decision with keys:
            - decision: str
            - symbol: str
            - confidence: float
        """
        if not self.websocket_manager:
            return

        try:
            await self.websocket_manager.broadcast(
                "council_trades",
                {
                    "type": "consensus",
                    "council_id": council.id,
                    "council_name": council.name,
                    "decision": consensus["decision"],
                    "symbol": consensus["symbol"],
                    "confidence": consensus["confidence"],
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as e:
            logger.exception(
                "Error broadcasting consensus",
                council_id=council.id,
                error=str(e),
            )

    async def abroadcast_trade(self, council, order):
        """
        Broadcast trade execution event.

        Parameters
        ----------
        council : Council
            Council object
        order : AsterOrder
            Executed order
        """
        if not self.websocket_manager or not order:
            return

        try:
            await self.websocket_manager.broadcast(
                "council_trades",
                {
                    "type": "trade",
                    "council_id": council.id,
                    "council_name": council.name,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": float(order.quantity),
                    "price": float(order.price or 0),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as e:
            logger.exception(
                "Error broadcasting trade",
                council_id=council.id,
                error=str(e),
            )

    async def abroadcast_cycle_complete(
        self,
        council,
        consensus: dict,
        trades_executed: list,
    ):
        """
        Broadcast cycle completion event.

        Broadcasts both consensus and trade events in sequence.

        Parameters
        ----------
        council : Council
            Council object
        consensus : dict
            Consensus decision
        trades_executed : list
            List of executed trades
        """
        if not self.websocket_manager:
            return

        try:
            # Broadcast consensus
            await self.abroadcast_consensus(council, consensus)

            # Broadcast trades
            for trade in trades_executed:
                if trade:
                    await self.abroadcast_trade(council, trade)

        except Exception as e:
            logger.exception(
                "Error broadcasting cycle completion",
                council_id=council.id,
                error=str(e),
            )
