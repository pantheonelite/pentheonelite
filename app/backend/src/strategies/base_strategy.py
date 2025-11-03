"""Base crypto trading strategy class."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from app.backend.client import AsterClient, AsterConfig
from pydantic import BaseModel


class StrategyConfig(BaseModel):
    """Configuration for trading strategies."""

    name: str
    description: str
    parameters: dict[str, Any] = {}
    enabled: bool = True


class Signal(BaseModel):
    """Trading signal output."""

    symbol: str
    action: str  # "buy", "sell", "hold"
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    price: float
    timestamp: str
    reasoning: str


class BaseCryptoStrategy(ABC):
    """Base class for crypto trading strategies."""

    def __init__(self, config: StrategyConfig):
        """Initialize the strategy with configuration."""
        self.config = config
        aster_config = AsterConfig(
            api_key=None,
            api_secret=None,
            base_url="https://fapi.asterdex.com",
        )
        self.client = AsterClient(aster_config)

    @abstractmethod
    async def generate_signals(self, symbols: list[str], timeframe: str = "1d") -> list[Signal]:
        """
        Generate trading signals for the given symbols.

        Parameters
        ----------
        symbols : list[str]
            List of crypto symbols to analyze
        timeframe : str
            Timeframe for analysis (e.g., "1d", "4h", "1h")

        Returns
        -------
        list[Signal]
            List of trading signals
        """
        raise NotImplementedError

    @abstractmethod
    def get_required_data_points(self) -> int:
        """
        Get the minimum number of data points required for the strategy.

        Returns
        -------
        int
            Minimum number of data points needed
        """
        raise NotImplementedError

    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame | None:
        """
        Get historical OHLCV data for a symbol.

        Parameters
        ----------
        symbol : str
            Crypto symbol (e.g., "BTC/USDT" or "BTCUSDT")
        timeframe : str
            Timeframe (e.g., "1d", "4h", "1h")
        limit : int
            Number of data points to retrieve

        Returns
        -------
        pd.DataFrame | None
            Historical data or None if failed
        """
        try:
            # Convert symbol to Aster format (remove /USDT if present, add USDT suffix)
            aster_symbol = symbol.replace("/", "").replace("USDT", "") + "USDT"

            # Get historical data using Aster client
            ohlcv_data = await self.client.aget_klines(aster_symbol, timeframe, limit)
            if not ohlcv_data:
                return None

            # Convert to DataFrame
            data = [
                {
                    "timestamp": kline.timestamp.timestamp() * 1000,  # Convert to milliseconds
                    "open": kline.open,
                    "high": kline.high,
                    "low": kline.low,
                    "close": kline.close,
                    "volume": kline.volume,
                }
                for kline in ohlcv_data
            ]
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df.set_index("timestamp")
        except Exception:
            return None

    def is_enabled(self) -> bool:
        """Check if the strategy is enabled."""
        return self.config.enabled

    def get_name(self) -> str:
        """Get the strategy name."""
        return self.config.name

    def get_description(self) -> str:
        """Get the strategy description."""
        return self.config.description
