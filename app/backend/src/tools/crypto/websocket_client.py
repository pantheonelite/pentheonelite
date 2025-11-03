"""Mock WebSocket Client for crypto data streaming."""

from collections.abc import AsyncGenerator
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MockWebSocketClient:
    """Mock client for crypto WebSocket data streaming."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        """Initialize the mock client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_connected = False
        logger.info("MockWebSocketClient initialized")

    async def connect(self):
        """Mock method to connect to the WebSocket."""
        logger.info("MockWebSocketClient connecting")
        self.is_connected = True
        logger.info("MockWebSocketClient connected")

    async def disconnect(self):
        """Mock method to disconnect from the WebSocket."""
        logger.info("MockWebSocketClient disconnecting")
        self.is_connected = False
        logger.info("MockWebSocketClient disconnected")

    async def subscribe_to_market_data(self, symbols: list[str]) -> bool:
        """Mock method to subscribe to market data."""
        logger.info("MockWebSocketClient subscribing to market data", symbols=symbols)
        return True

    async def unsubscribe_from_market_data(self, symbols: list[str]) -> bool:
        """Mock method to unsubscribe from market data."""
        logger.info("MockWebSocketClient unsubscribing from market data", symbols=symbols)
        return True

    async def receive_messages(self) -> AsyncGenerator[dict[str, Any], None]:
        """Mock method to receive messages."""
        # Simulate receiving some messages
        mock_messages = [
            {"type": "ticker", "symbol": "BTC/USDT", "price": 60000.0, "timestamp": "2024-01-01T12:00:00Z"},
            {
                "type": "trade",
                "symbol": "ETH/USDT",
                "price": 3000.0,
                "quantity": 1.5,
                "timestamp": "2024-01-01T12:00:01Z",
            },
        ]
        for msg in mock_messages:
            yield msg
        # In a real scenario, this would be an infinite loop yielding real-time data
