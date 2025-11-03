"""MACD-based crypto trading strategy."""

import pandas as pd

from .base_strategy import BaseCryptoStrategy, Signal, StrategyConfig


class MacdCryptoStrategy(BaseCryptoStrategy):
    """MACD (Moving Average Convergence Divergence) crypto trading strategy."""

    def __init__(self, config: StrategyConfig):
        """Initialize MACD strategy."""
        super().__init__(config)
        self.fast_period = config.parameters.get("fast_period", 12)
        self.slow_period = config.parameters.get("slow_period", 26)
        self.signal_period = config.parameters.get("signal_period", 9)
        self.threshold = config.parameters.get("threshold", 0.0001)

    def get_required_data_points(self) -> int:
        """Get minimum data points needed for MACD calculation."""
        return max(self.slow_period + self.signal_period, 50)

    def calculate_macd(self, prices: pd.Series) -> pd.DataFrame:
        """
        Calculate MACD indicators.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically close prices)

        Returns
        -------
        pd.DataFrame
            DataFrame with MACD, signal, and histogram columns
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=self.fast_period).mean()
        ema_slow = prices.ewm(span=self.slow_period).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_period).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})

    async def generate_signals(self, symbols: list[str], timeframe: str = "1d") -> list[Signal]:
        """
        Generate MACD-based trading signals.

        Parameters
        ----------
        symbols : list[str]
            List of crypto symbols to analyze
        timeframe : str
            Timeframe for analysis

        Returns
        -------
        list[Signal]
            List of trading signals
        """
        signals = []
        required_points = self.get_required_data_points()

        for symbol in symbols:
            try:
                # Get historical data
                df = await self.get_historical_data(symbol, timeframe, required_points + 10)
                if df is None or len(df) < required_points:
                    continue

                # Calculate MACD
                macd_data = self.calculate_macd(df["close"])

                # Get latest values
                latest_macd = macd_data["macd"].iloc[-1]
                latest_signal = macd_data["signal"].iloc[-1]
                latest_histogram = macd_data["histogram"].iloc[-1]
                prev_histogram = macd_data["histogram"].iloc[-2]

                # Generate signal based on MACD crossover
                action = "hold"
                strength = 0.0
                confidence = 0.0
                reasoning = "No clear MACD signal"

                # Bullish signal: MACD crosses above signal line
                if (
                    latest_macd > latest_signal
                    and macd_data["macd"].iloc[-2] <= macd_data["signal"].iloc[-2]
                    and latest_histogram > self.threshold
                ):
                    action = "buy"
                    strength = min(abs(latest_histogram) * 1000, 1.0)  # Scale histogram to 0-1
                    confidence = 0.7
                    reasoning = f"MACD bullish crossover: {latest_macd:.6f} > {latest_signal:.6f}"

                # Bearish signal: MACD crosses below signal line
                elif (
                    latest_macd < latest_signal
                    and macd_data["macd"].iloc[-2] >= macd_data["signal"].iloc[-2]
                    and latest_histogram < -self.threshold
                ):
                    action = "sell"
                    strength = min(abs(latest_histogram) * 1000, 1.0)  # Scale histogram to 0-1
                    confidence = 0.7
                    reasoning = f"MACD bearish crossover: {latest_macd:.6f} < {latest_signal:.6f}"

                # Histogram momentum signals
                elif latest_histogram > prev_histogram and latest_histogram > self.threshold:
                    action = "buy"
                    strength = min(abs(latest_histogram) * 500, 0.8)  # Weaker signal
                    confidence = 0.5
                    reasoning = f"MACD histogram momentum up: {latest_histogram:.6f}"

                elif latest_histogram < prev_histogram and latest_histogram < -self.threshold:
                    action = "sell"
                    strength = min(abs(latest_histogram) * 500, 0.8)  # Weaker signal
                    confidence = 0.5
                    reasoning = f"MACD histogram momentum down: {latest_histogram:.6f}"

                # Create signal
                signal = Signal(
                    symbol=symbol,
                    action=action,
                    strength=strength,
                    confidence=confidence,
                    price=float(df["close"].iloc[-1]),
                    timestamp=df.index[-1].isoformat(),
                    reasoning=reasoning,
                )
                signals.append(signal)

            except Exception as e:
                # Create error signal
                signal = Signal(
                    symbol=symbol,
                    action="hold",
                    strength=0.0,
                    confidence=0.0,
                    price=0.0,
                    timestamp=pd.Timestamp.now().isoformat(),
                    reasoning=f"Error in MACD calculation: {e!s}",
                )
                signals.append(signal)

        return signals
