import pandas as pd
import structlog
from app.backend.client import AsterClient

logger = structlog.get_logger(__name__)


class BenchmarkCalculator:
    """Calculator for benchmark performance metrics."""

    def __init__(self, client: AsterClient | None = None):
        """Initialize the benchmark calculator with an optional Aster client."""
        self._aster_client = client or AsterClient()

    def get_return_pct(self, symbol: str, start_date: str, end_date: str) -> float | None:
        """Compute simple buy-and-hold return % for crypto symbol from start_date to end_date.

        Return is (last_close / first_close - 1) * 100, or None if unavailable.
        """
        try:
            # Ensure symbol is in Aster format (no slash)
            crypto_symbol = symbol.replace("/", "") if "/" in symbol else symbol

            # Get historical data using Aster
            ohlcv_data = self._aster_client.get_klines(crypto_symbol, "1d", 1000)

            if not ohlcv_data or len(ohlcv_data) < 2:
                return None

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(
                [
                    {
                        "timestamp": data.timestamp,
                        "open": data.open,
                        "high": data.high,
                        "low": data.low,
                        "close": data.close,
                        "volume": data.volume,
                    }
                    for data in ohlcv_data
                ]
            )

            if df.empty:
                return None

            # Filter by date range
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]

            if len(df) < 2:
                return None

            first_close = df.iloc[0]["close"]
            last_close = df.iloc[-1]["close"]

            # Validate data
            if first_close is None or pd.isna(first_close):
                return None

            if last_close is None or pd.isna(last_close):
                # Try last valid close
                last_valid = df["close"].dropna()
                if last_valid.empty:
                    return None
                last_close = float(last_valid.iloc[-1])

            return (float(last_close) / float(first_close) - 1.0) * 100.0
        except Exception:
            return None
