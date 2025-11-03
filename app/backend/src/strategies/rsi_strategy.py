"""RSI-based crypto trading strategy."""

import pandas as pd

from .base_strategy import BaseCryptoStrategy, Signal, StrategyConfig


class RsiCryptoStrategy(BaseCryptoStrategy):
    """RSI (Relative Strength Index) crypto trading strategy."""

    def __init__(self, config: StrategyConfig):
        """Initialize RSI strategy."""
        super().__init__(config)
        self.period = config.parameters.get("period", 14)
        self.overbought = config.parameters.get("overbought", 70)
        self.oversold = config.parameters.get("oversold", 30)
        self.middle = config.parameters.get("middle", 50)

    def get_required_data_points(self) -> int:
        """Get minimum data points needed for RSI calculation."""
        return self.period + 10

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """
        Calculate RSI indicator.

        Parameters
        ----------
        prices : pd.Series
            Price series (typically close prices)

        Returns
        -------
        pd.Series
            RSI values
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses using exponential moving average
        avg_gains = gains.ewm(span=self.period).mean()
        avg_losses = losses.ewm(span=self.period).mean()

        # Calculate relative strength
        rs = avg_gains / avg_losses

        # Calculate RSI
        return 100 - (100 / (1 + rs))

    async def generate_signals(self, symbols: list[str], timeframe: str = "1d") -> list[Signal]:
        """
        Generate RSI-based trading signals.

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

                # Calculate RSI
                rsi = self.calculate_rsi(df["close"])

                # Get latest RSI values
                latest_rsi = rsi.iloc[-1]
                prev_rsi = rsi.iloc[-2]

                # Generate signal based on RSI levels
                action = "hold"
                strength = 0.0
                confidence = 0.0
                reasoning = "RSI in neutral zone"

                # Oversold condition - potential buy signal
                if latest_rsi < self.oversold and prev_rsi >= self.oversold:
                    action = "buy"
                    strength = (self.oversold - latest_rsi) / self.oversold  # 0-1 scale
                    confidence = 0.8
                    reasoning = f"RSI oversold bounce: {latest_rsi:.1f} < {self.oversold}"

                # Overbought condition - potential sell signal
                elif latest_rsi > self.overbought and prev_rsi <= self.overbought:
                    action = "sell"
                    strength = (latest_rsi - self.overbought) / (100 - self.overbought)  # 0-1 scale
                    confidence = 0.8
                    reasoning = f"RSI overbought rejection: {latest_rsi:.1f} > {self.overbought}"

                # RSI momentum signals
                elif latest_rsi > prev_rsi and latest_rsi > self.middle:
                    action = "buy"
                    strength = min(
                        (latest_rsi - self.middle) / (self.overbought - self.middle),
                        0.6,
                    )
                    confidence = 0.4
                    reasoning = f"RSI momentum up: {latest_rsi:.1f} > {prev_rsi:.1f}"

                elif latest_rsi < prev_rsi and latest_rsi < self.middle:
                    action = "sell"
                    strength = min((self.middle - latest_rsi) / (self.middle - self.oversold), 0.6)
                    confidence = 0.4
                    reasoning = f"RSI momentum down: {latest_rsi:.1f} < {prev_rsi:.1f}"

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
                    reasoning=f"Error in RSI calculation: {e!s}",
                )
                signals.append(signal)

        return signals
