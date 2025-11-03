"""Momentum-based crypto trading strategy."""

import pandas as pd

from .base_strategy import BaseCryptoStrategy, Signal, StrategyConfig


class MomentumCryptoStrategy(BaseCryptoStrategy):
    """Momentum-based crypto trading strategy using price and volume analysis."""

    def __init__(self, config: StrategyConfig):
        """Initialize momentum strategy."""
        super().__init__(config)
        self.price_period = config.parameters.get("price_period", 20)
        self.volume_period = config.parameters.get("volume_period", 20)
        self.momentum_threshold = config.parameters.get("momentum_threshold", 0.02)  # 2%
        self.volume_threshold = config.parameters.get("volume_threshold", 1.5)  # 1.5x average

    def get_required_data_points(self) -> int:
        """Get minimum data points needed for momentum calculation."""
        return max(self.price_period, self.volume_period) + 10

    def calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate momentum indicators.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV data

        Returns
        -------
        pd.DataFrame
            DataFrame with momentum indicators
        """
        # Price momentum
        price_momentum = df["close"].pct_change(self.price_period)

        # Volume momentum
        volume_ma = df["volume"].rolling(window=self.volume_period).mean()
        volume_ratio = df["volume"] / volume_ma

        # Price trend (simple moving average)
        price_ma = df["close"].rolling(window=self.price_period).mean()
        price_trend = (df["close"] - price_ma) / price_ma

        # Volatility-adjusted momentum
        volatility = df["close"].rolling(window=self.price_period).std()
        normalized_momentum = price_momentum / volatility

        return pd.DataFrame(
            {
                "price_momentum": price_momentum,
                "volume_ratio": volume_ratio,
                "price_trend": price_trend,
                "normalized_momentum": normalized_momentum,
            }
        )

    async def generate_signals(self, symbols: list[str], timeframe: str = "1d") -> list[Signal]:
        """
        Generate momentum-based trading signals.

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

                # Calculate momentum indicators
                momentum_data = self.calculate_momentum_indicators(df)

                # Get latest values
                latest_momentum = momentum_data["price_momentum"].iloc[-1]
                latest_volume_ratio = momentum_data["volume_ratio"].iloc[-1]
                latest_trend = momentum_data["price_trend"].iloc[-1]
                # latest_normalized = momentum_data["normalized_momentum"].iloc[-1]  # Future use

                # Generate signal based on momentum and volume
                action = "hold"
                strength = 0.0
                confidence = 0.0
                reasoning = "No clear momentum signal"

                # Strong bullish momentum with volume confirmation
                if (
                    latest_momentum > self.momentum_threshold
                    and latest_volume_ratio > self.volume_threshold
                    and latest_trend > 0
                ):
                    action = "buy"
                    strength = min(abs(latest_momentum) * 10, 1.0)  # Scale to 0-1
                    confidence = 0.8
                    reasoning = (
                        f"Strong bullish momentum: {latest_momentum:.3f} with volume {latest_volume_ratio:.1f}x"
                    )

                # Strong bearish momentum with volume confirmation
                elif (
                    latest_momentum < -self.momentum_threshold
                    and latest_volume_ratio > self.volume_threshold
                    and latest_trend < 0
                ):
                    action = "sell"
                    strength = min(abs(latest_momentum) * 10, 1.0)  # Scale to 0-1
                    confidence = 0.8
                    reasoning = (
                        f"Strong bearish momentum: {latest_momentum:.3f} with volume {latest_volume_ratio:.1f}x"
                    )

                # Moderate momentum signals
                elif latest_momentum > self.momentum_threshold * 0.5 and latest_trend > 0:
                    action = "buy"
                    strength = min(abs(latest_momentum) * 5, 0.7)  # Weaker signal
                    confidence = 0.5
                    reasoning = f"Moderate bullish momentum: {latest_momentum:.3f}"

                elif latest_momentum < -self.momentum_threshold * 0.5 and latest_trend < 0:
                    action = "sell"
                    strength = min(abs(latest_momentum) * 5, 0.7)  # Weaker signal
                    confidence = 0.5
                    reasoning = f"Moderate bearish momentum: {latest_momentum:.3f}"

                # Volume breakout without strong momentum
                elif latest_volume_ratio > self.volume_threshold * 1.5:
                    if latest_trend > 0:
                        action = "buy"
                        strength = 0.4
                        confidence = 0.3
                        reasoning = f"Volume breakout up: {latest_volume_ratio:.1f}x volume"
                    elif latest_trend < 0:
                        action = "sell"
                        strength = 0.4
                        confidence = 0.3
                        reasoning = f"Volume breakout down: {latest_volume_ratio:.1f}x volume"

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
                    reasoning=f"Error in momentum calculation: {e!s}",
                )
                signals.append(signal)

        return signals
