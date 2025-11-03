"""Binance Futures client module."""

from app.backend.client.binance.exceptions import (
    BinanceAPIException,
    BinanceAuthenticationError,
    BinanceInsufficientBalanceError,
    BinanceInvalidSymbolError,
    BinanceOrderError,
    BinanceRateLimitError,
    BinanceRequestException,
    BinanceServerError,
    BinanceTimeoutError,
)
from app.backend.client.binance.rate_limiter import OrderRateLimiter, RateLimiter
from app.backend.client.binance.rest import (
    BinanceClient,
    BinanceFuturesAccount,
    BinanceFuturesOrder,
    BinanceFuturesPosition,
    BinanceOHLCV,
    BinanceTicker,
)
from app.backend.config.binance import BinanceConfig

__all__ = [
    "BinanceAPIException",
    "BinanceAuthenticationError",
    "BinanceClient",
    "BinanceConfig",
    "BinanceFuturesAccount",
    "BinanceFuturesOrder",
    "BinanceFuturesPosition",
    "BinanceInsufficientBalanceError",
    "BinanceInvalidSymbolError",
    "BinanceOHLCV",
    "BinanceOrderError",
    "BinanceRateLimitError",
    "BinanceRequestException",
    "BinanceServerError",
    "BinanceTicker",
    "BinanceTimeoutError",
    "OrderRateLimiter",
    "RateLimiter",
]
