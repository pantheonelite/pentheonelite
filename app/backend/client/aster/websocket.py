"""Mock Aster WebSocket client for backward compatibility."""

import asyncio
from typing import Any


class MockAsterWebSocketClient:
    """Mock Aster WebSocket client."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the mock client."""
        self.config = config or {}
        self.connected = False

    async def connect(self) -> bool:
        """Mock connection."""
        self.connected = True
        return True

    async def disconnect(self):
        """Mock disconnection."""
        self.connected = False

    async def subscribe(self, channel: str) -> bool:
        """Mock subscription."""
        return True

    async def unsubscribe(self, channel: str) -> bool:
        """Mock unsubscription."""
        return True

    async def send_message(self, message: dict[str, Any]) -> bool:
        """Mock sending message."""
        return True

    async def receive_message(self) -> dict[str, Any] | None:
        """Mock receiving message."""
        await asyncio.sleep(0.1)  # Simulate delay
        return {"type": "mock_message", "data": {"message": "Mock data from Aster WebSocket"}}
