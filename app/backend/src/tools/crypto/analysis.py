"""Crypto analysis tools for price trends and sentiment analysis."""

import json
from datetime import datetime

import numpy as np
from app.backend.client import AsterClient
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class PriceTrendInput(BaseModel):
    """Input schema for price trend analysis tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTC/USDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


class VolumeAnalysisInput(BaseModel):
    """Input schema for volume analysis tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTC/USDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


class CryptoSentimentInput(BaseModel):
    """Input schema for crypto sentiment analysis tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTC/USDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


class PriceTrendTool(BaseTool):
    """Tool to analyze cryptocurrency price trends."""

    name: str = "price_trend"
    description: str = "Analyze cryptocurrency price trends and patterns"
    args_schema: type[BaseModel] = PriceTrendInput

    async def _arun(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: int = 24,
        exchange: str = "binance",
    ) -> str:
        """
        Analyze price trends.

        Args:
            symbol: Trading pair
            timeframe: Analysis timeframe
            period: Number of periods to analyze
            exchange: Exchange name

        Returns
        -------
            JSON string with trend analysis
        """
        try:
            with AsterClient() as client:
                klines = await client.aget_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Convert klines to list format
                data = [
                    {
                        "timestamp": kline.timestamp.isoformat(),
                        "open": kline.open,
                        "high": kline.high,
                        "low": kline.low,
                        "close": kline.close,
                        "volume": kline.volume,
                    }
                    for kline in klines
                ]
                if not data:
                    return f"No klines data available for {symbol}"

                closes = [float(candle["close"]) for candle in data]  # Close price
                highs = [float(candle["high"]) for candle in data]  # High price
                lows = [float(candle["low"]) for candle in data]  # Low price

            # Calculate trend indicators
            sma_short = self._calculate_sma(closes, min(5, len(closes)))
            sma_long = self._calculate_sma(closes, min(20, len(closes)))

            # Price momentum
            price_change = closes[-1] - closes[0] if len(closes) > 1 else 0
            price_change_percent = (price_change / closes[0]) * 100 if closes[0] != 0 else 0

            # Support and resistance levels
            support_levels = self._find_support_levels(lows)
            resistance_levels = self._find_resistance_levels(highs)

            # Trend determination
            trend = self._determine_trend(closes, sma_short, sma_long)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": exchange,
                "analysis_period": period,
                "current_price": closes[-1],
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "trend": trend,
                "sma_short": sma_short[-1] if sma_short else None,
                "sma_long": sma_long[-1] if sma_long else None,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing price trend: {e!s}"

    def _calculate_sma(self, prices: list[float], period: int) -> list[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return []

        return [sum(prices[i - period + 1 : i + 1]) / period for i in range(period - 1, len(prices))]

    def _find_support_levels(self, lows: list[float], num_levels: int = 3) -> list[float]:
        """Find support levels from low prices."""
        if len(lows) < 5:
            return []

        # Find local minima
        support_levels = [
            lows[i]
            for i in range(2, len(lows) - 2)
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 2]
        ]

        # Return top support levels
        return sorted(support_levels)[:num_levels]

    def _find_resistance_levels(self, highs: list[float], num_levels: int = 3) -> list[float]:
        """Find resistance levels from high prices."""
        if len(highs) < 5:
            return []

        # Find local maxima
        resistance_levels = [
            highs[i]
            for i in range(2, len(highs) - 2)
            if (
                highs[i] > highs[i - 1]
                and highs[i] > highs[i + 1]
                and highs[i] > highs[i - 2]
                and highs[i] > highs[i + 2]
            )
        ]

        # Return top resistance levels
        return sorted(resistance_levels, reverse=True)[:num_levels]

    def _determine_trend(self, closes: list[float], sma_short: list[float], sma_long: list[float]) -> str:
        """Determine the overall trend."""
        if not sma_short or not sma_long:
            return "insufficient_data"

        current_price = closes[-1]
        short_sma = sma_short[-1]
        long_sma = sma_long[-1]

        if current_price > short_sma > long_sma:
            return "strong_bullish"
        if current_price > short_sma > long_sma:
            return "bullish"
        if current_price < short_sma < long_sma:
            return "strong_bearish"
        if current_price < short_sma < long_sma:
            return "bearish"
        return "sideways"

    def _run(self, symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
        """Synchronous version using direct sync method calls."""
        try:
            with AsterClient() as client:
                klines = client.get_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Convert klines to list format
                data = [
                    {
                        "timestamp": kline.timestamp.isoformat(),
                        "open": kline.open,
                        "high": kline.high,
                        "low": kline.low,
                        "close": kline.close,
                        "volume": kline.volume,
                    }
                    for kline in klines
                ]
                if not data:
                    return f"No klines data available for {symbol}"

                closes = [float(candle["close"]) for candle in data]  # Close price
                highs = [float(candle["high"]) for candle in data]  # High price
                lows = [float(candle["low"]) for candle in data]  # Low price

                # Calculate trend indicators
                sma_short = self._calculate_sma(closes, min(5, len(closes)))
                sma_long = self._calculate_sma(closes, min(20, len(closes)))

                # Price momentum
                price_change = closes[-1] - closes[0] if len(closes) > 1 else 0
                price_change_percent = (price_change / closes[0]) * 100 if closes[0] != 0 else 0

                # Support and resistance levels
                support_levels = self._find_support_levels(lows)
                resistance_levels = self._find_resistance_levels(highs)

                # Trend determination
                trend = self._determine_trend(closes, sma_short, sma_long)

                result = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "exchange": exchange,
                    "analysis_period": period,
                    "current_price": closes[-1],
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "trend": trend,
                    "sma_short": sma_short[-1] if sma_short else None,
                    "sma_long": sma_long[-1] if sma_long else None,
                    "support_levels": support_levels,
                    "resistance_levels": resistance_levels,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing price trend: {e!s}"


class VolumeAnalysisTool(BaseTool):
    """Tool to analyze trading volume patterns."""

    name: str = "volume_analysis"
    description: str = "Analyze trading volume patterns and market sentiment"
    args_schema: type[BaseModel] = VolumeAnalysisInput

    async def _arun(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: int = 24,
        exchange: str = "binance",
    ) -> str:
        """
        Analyze volume patterns.

        Args:
            symbol: Trading pair
            timeframe: Analysis timeframe
            period: Number of periods to analyze
            exchange: Exchange name

        Returns
        -------
            JSON string with volume analysis
        """
        try:
            with AsterClient() as client:
                klines = await client.aget_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Extract volume and price data
                volumes = [float(kline.volume) for kline in klines]
                closes = [float(kline.close) for kline in klines]

                if not volumes or not closes:
                    return f"No volume/price data available for {symbol}"

                # Calculate volume metrics
                avg_volume = sum(volumes) / len(volumes)
                max_volume = max(volumes)
                min_volume = min(volumes)
                current_volume = volumes[-1]

                # Volume trend
                volume_trend = self._calculate_volume_trend(volumes)

                # Volume-price relationship
                volume_price_correlation = self._calculate_volume_price_correlation(volumes, closes)

                # Volume spikes
                volume_spikes = self._identify_volume_spikes(volumes, avg_volume)

                result = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "exchange": exchange,
                    "analysis_period": period,
                    "volume_metrics": {
                        "current_volume": current_volume,
                        "average_volume": avg_volume,
                        "max_volume": max_volume,
                        "min_volume": min_volume,
                        "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 0,
                    },
                    "volume_trend": volume_trend,
                    "volume_price_correlation": volume_price_correlation,
                    "volume_spikes": volume_spikes,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing volume: {e!s}"

    def _calculate_volume_trend(self, volumes: list[float]) -> str:
        """Calculate volume trend."""
        if len(volumes) < 3:
            return "insufficient_data"

        recent_avg = sum(volumes[-3:]) / 3
        earlier_avg = sum(volumes[:3]) / 3

        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        if recent_avg < earlier_avg * 0.8:
            return "decreasing"
        return "stable"

    def _calculate_volume_price_correlation(self, volumes: list[float], closes: list[float]) -> float:
        """Calculate correlation between volume and price."""
        if len(volumes) != len(closes) or len(volumes) < 2:
            return 0.0

        # Calculate price changes
        price_changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        volumes_adjusted = volumes[1:]  # Match length with price changes

        # Calculate correlation
        if len(price_changes) < 2:
            return 0.0

        correlation = np.corrcoef(price_changes, volumes_adjusted)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0

    def _identify_volume_spikes(self, volumes: list[float], avg_volume: float, threshold: float = 2.0) -> list[dict]:
        """Identify volume spikes."""
        spikes = []
        for i, volume in enumerate(volumes):
            if volume > avg_volume * threshold:
                spikes.append(
                    {
                        "index": i,
                        "volume": volume,
                        "ratio": volume / avg_volume if avg_volume > 0 else 0,
                    }
                )
        return spikes

    def _run(self, symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
        """Synchronous version using direct sync method calls."""
        try:
            with AsterClient() as client:
                klines = client.get_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Extract volume and price data
                volumes = [float(kline.volume) for kline in klines]
                closes = [float(kline.close) for kline in klines]

                if not volumes or not closes:
                    return f"No volume/price data available for {symbol}"

                # Calculate volume metrics
                avg_volume = sum(volumes) / len(volumes)
                max_volume = max(volumes)
                min_volume = min(volumes)
                volume_trend = self._calculate_volume_trend(volumes)

                # Calculate volume-price correlation
                correlation = self._calculate_volume_price_correlation(volumes, closes)

                # Identify volume spikes
                spikes = self._identify_volume_spikes(volumes, avg_volume)

                result = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "exchange": exchange,
                    "analysis_period": period,
                    "average_volume": avg_volume,
                    "max_volume": max_volume,
                    "min_volume": min_volume,
                    "volume_trend": volume_trend,
                    "volume_price_correlation": correlation,
                    "volume_spikes": spikes,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing volume: {e!s}"


class CryptoSentimentTool(BaseTool):
    """Tool to analyze crypto market sentiment."""

    name: str = "crypto_sentiment"
    description: str = "Analyze cryptocurrency market sentiment based on price and volume data"
    args_schema: type[BaseModel] = CryptoSentimentInput

    async def _arun(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: int = 24,
        exchange: str = "binance",
    ) -> str:
        """
        Analyze crypto sentiment.

        Args:
            symbol: Trading pair
            timeframe: Analysis timeframe
            period: Number of periods to analyze
            exchange: Exchange name

        Returns
        -------
            JSON string with sentiment analysis
        """
        try:
            with AsterClient() as client:
                klines = await client.aget_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Extract price and volume data
                closes = [float(kline.close) for kline in klines]
                volumes = [float(kline.volume) for kline in klines]
                highs = [float(kline.high) for kline in klines]
                lows = [float(kline.low) for kline in klines]

                if not closes or not volumes:
                    return f"No price/volume data available for {symbol}"

                # Calculate sentiment indicators
                price_momentum = self._calculate_price_momentum(closes)
                volume_sentiment = self._calculate_volume_sentiment(volumes)
                volatility_sentiment = self._calculate_volatility_sentiment(highs, lows, closes)

                # Overall sentiment score
                weights = {"price": 0.5, "volume": 0.3, "volatility": 0.2}
                sentiment_score = self._calculate_sentiment_score(
                    price_momentum, volume_sentiment, volatility_sentiment, weights
                )
                sentiment_label = self._get_sentiment_label(sentiment_score)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": exchange,
                "analysis_period": period,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "indicators": {
                    "price_momentum": price_momentum,
                    "volume_sentiment": volume_sentiment,
                    "volatility_sentiment": volatility_sentiment,
                },
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing sentiment: {e!s}"

    def _calculate_price_momentum(self, closes: list[float]) -> float:
        """Calculate price momentum sentiment."""
        if len(closes) < 2:
            return 0.0

        # Calculate rate of change
        roc = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0

        # Normalize to -1 to 1 scale
        return max(-1, min(1, roc * 10))  # Scale factor for normalization

    def _calculate_volume_sentiment(self, volumes: list[float]) -> float:
        """Calculate volume-based sentiment."""
        if len(volumes) < 3:
            return 0.0

        recent_avg = sum(volumes[-3:]) / 3
        overall_avg = sum(volumes) / len(volumes)

        # Volume ratio sentiment
        volume_ratio = recent_avg / overall_avg if overall_avg > 0 else 1

        # Normalize to -1 to 1 scale
        if volume_ratio > 1.5:
            return 0.8
        if volume_ratio > 1.2:
            return 0.4
        if volume_ratio < 0.5:
            return -0.8
        if volume_ratio < 0.8:
            return -0.4
        return 0.0

    def _calculate_volatility_sentiment(self, highs: list[float], lows: list[float], closes: list[float]) -> float:
        """Calculate volatility-based sentiment."""
        if len(highs) < 2:
            return 0.0

        # Calculate average true range
        atr_values = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            atr_values.append(tr)

        avg_atr = sum(atr_values) / len(atr_values) if atr_values else 0
        current_price = closes[-1]

        # Volatility as percentage of price
        volatility = (avg_atr / current_price) * 100 if current_price > 0 else 0

        # High volatility can indicate uncertainty (negative sentiment)
        if volatility > 5:
            return -0.6
        if volatility > 3:
            return -0.3
        if volatility < 1:
            return 0.3
        return 0.0

    def _calculate_sentiment_score(
        self,
        price_momentum: float,
        volume_sentiment: float,
        volatility_sentiment: float,
        weights: dict[str, float] | None = None,
    ) -> float:
        """Calculate overall sentiment score."""
        # Weighted combination of indicators
        if weights is None:
            weights = {"price": 0.5, "volume": 0.3, "volatility": 0.2}

        score = (
            price_momentum * weights["price"]
            + volume_sentiment * weights["volume"]
            + volatility_sentiment * weights["volatility"]
        )

        return max(-1, min(1, score))

    def _get_sentiment_label(self, score: float) -> str:
        """Get sentiment label from score."""
        if score > 0.6:
            return "very_bullish"
        if score > 0.2:
            return "bullish"
        if score > -0.2:
            return "neutral"
        if score > -0.6:
            return "bearish"
        return "very_bearish"

    def _run(self, symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
        """Synchronous version using direct sync method calls."""
        try:
            with AsterClient() as client:
                klines = client.get_klines(symbol, timeframe, period)

                if not klines:
                    return f"No data available for {symbol}"

                # Extract price and volume data
                closes = [float(kline.close) for kline in klines]
                volumes = [float(kline.volume) for kline in klines]
                highs = [float(kline.high) for kline in klines]
                lows = [float(kline.low) for kline in klines]

                if not closes or not volumes:
                    return f"No price/volume data available for {symbol}"

                # Calculate sentiment components
                price_momentum = self._calculate_price_momentum(closes)
                volume_sentiment = self._calculate_volume_sentiment(volumes)
                volatility_sentiment = self._calculate_volatility_sentiment(highs, lows, closes)

                # Weighted sentiment score
                weights = {"price": 0.5, "volume": 0.3, "volatility": 0.2}
                sentiment_score = self._calculate_sentiment_score(
                    price_momentum, volume_sentiment, volatility_sentiment, weights
                )

                sentiment_label = self._get_sentiment_label(sentiment_score)

                result = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "exchange": exchange,
                    "analysis_period": period,
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "components": {
                        "price_momentum": price_momentum,
                        "volume_sentiment": volume_sentiment,
                        "volatility_sentiment": volatility_sentiment,
                    },
                    "weights": weights,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing sentiment: {e!s}"
