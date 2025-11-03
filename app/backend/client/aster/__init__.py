"""Aster trading client integration."""

from app.backend.config.aster import AsterConfig

from .futures import (
    AsterFuturesClient,
    AsterFuturesError,
    AuthenticationError,
    RateLimitError,
)
from .rest import AsterClient, AsterOrder
from .websocket import MockAsterWebSocketClient as AsterWebSocketClient

__all__ = [
    "AsterClient",
    "AsterConfig",
    "AsterFuturesClient",
    "AsterFuturesError",
    "AsterOrder",
    "AsterWebSocketClient",
    "AuthenticationError",
    "RateLimitError",
]
