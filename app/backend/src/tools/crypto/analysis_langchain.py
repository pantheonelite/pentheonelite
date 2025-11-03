"""Crypto analysis tools migrated to LangChain @tool decorator pattern.

This module provides price trend and volume analysis tools using the @tool decorator
instead of BaseTool classes.
"""

import json
from datetime import UTC, datetime

import numpy as np
from app.backend.client import AsterClient
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Input Schemas
class PriceTrendInput(BaseModel):
    """Input schema for price trend analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT, ETHUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    period: int = Field(default=24, description="Number of periods to analyze (minimum 5)")
    exchange: str = Field(default="binance", description="Exchange name (default: binance)")


class VolumeAnalysisInput(BaseModel):
    """Input schema for volume analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT, ETHUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    period: int = Field(default=24, description="Number of periods to analyze (minimum 5)")
    exchange: str = Field(default="binance", description="Exchange name (default: binance)")


class CryptoSentimentInput(BaseModel):
    """Input schema for crypto sentiment analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT, ETHUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    period: int = Field(default=24, description="Number of periods to analyze (minimum 5)")
    exchange: str = Field(default="binance", description="Exchange name (default: binance)")


# Tool Functions
@tool(args_schema=PriceTrendInput)
def price_trend_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 24,
    exchange: str = "binance",  # noqa: ARG001
) -> str:
    """Analyze cryptocurrency price trends and patterns.

    This tool examines price movements, calculates moving averages, identifies support
    and resistance levels, and determines overall trend direction. Use this when you
    need to understand the price action and trend of a cryptocurrency.

    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
    timeframe : str
        Analysis timeframe (e.g., "1h", "4h", "1d")
    period : int
        Number of candles to analyze (minimum 5)
    exchange : str
        Exchange name (default "binance")

    Returns
    -------
    str
        JSON string with trend analysis including current price, price change, trend direction,
        moving averages, and support/resistance levels
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines or len(klines) < 5:
                return json.dumps({"error": f"Insufficient data for {symbol} (need at least 5 candles)"})

            closes = [float(kline.close) for kline in klines]
            highs = [float(kline.high) for kline in klines]
            lows = [float(kline.low) for kline in klines]

            # Calculate trend indicators
            sma_short = calculate_sma(closes, min(5, len(closes)))
            sma_long = calculate_sma(closes, min(20, len(closes)))

            # Price momentum
            price_change = closes[-1] - closes[0] if len(closes) > 1 else 0
            price_change_percent = (price_change / closes[0]) * 100 if closes[0] != 0 else 0

            # Support and resistance
            support_levels = find_support_levels(lows)
            resistance_levels = find_resistance_levels(highs)

            # Trend determination
            trend = determine_trend(closes, sma_short, sma_long)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": "aster",
                "analysis_period": period,
                "current_price": round(closes[-1], 2),
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "trend": trend,
                "sma_short": round(sma_short[-1], 2) if sma_short else None,
                "sma_long": round(sma_long[-1], 2) if sma_long else None,
                "support_levels": [round(x, 2) for x in support_levels],
                "resistance_levels": [round(x, 2) for x in resistance_levels],
                "analysis_timestamp": datetime.now(UTC).isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing price trend: {e!s}", "symbol": symbol})


@tool(args_schema=VolumeAnalysisInput)
def volume_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 24,
    exchange: str = "binance",  # noqa: ARG001
) -> str:
    """Analyze trading volume patterns and market sentiment.

    This tool examines volume trends, calculates volume-price correlation, and identifies
    volume spikes that may indicate significant market moves. Use this to understand
    the strength behind price movements.

    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
    timeframe : str
        Analysis timeframe (e.g., "1h", "4h", "1d")
    period : int
        Number of candles to analyze (minimum 5)
    exchange : str
        Exchange name (default "binance")

    Returns
    -------
    str
        JSON string with volume metrics, trend, volume-price correlation, and volume spikes
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines or len(klines) < 5:
                return json.dumps({"error": f"Insufficient data for {symbol} (need at least 5 candles)"})

            volumes = [float(kline.volume) for kline in klines]
            closes = [float(kline.close) for kline in klines]

            # Calculate volume metrics
            avg_volume = sum(volumes) / len(volumes)
            max_volume = max(volumes)
            min_volume = min(volumes)
            current_volume = volumes[-1]

            # Volume trend
            volume_trend = calculate_volume_trend(volumes)

            # Volume-price correlation
            correlation = calculate_volume_price_correlation(volumes, closes)

            # Volume spikes
            spikes = identify_volume_spikes(volumes, avg_volume)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": "aster",
                "analysis_period": period,
                "volume_metrics": {
                    "current_volume": round(current_volume, 2),
                    "average_volume": round(avg_volume, 2),
                    "max_volume": round(max_volume, 2),
                    "min_volume": round(min_volume, 2),
                    "volume_ratio": round(current_volume / avg_volume, 2) if avg_volume > 0 else 0,
                },
                "volume_trend": volume_trend,
                "volume_price_correlation": round(correlation, 3),
                "volume_spikes": [
                    {"index": s["index"], "volume": round(s["volume"], 2), "ratio": round(s["ratio"], 2)}
                    for s in spikes
                ],
                "analysis_timestamp": datetime.now(UTC).isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing volume: {e!s}", "symbol": symbol})


@tool(args_schema=CryptoSentimentInput)
def crypto_sentiment_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 24,
) -> str:
    """Analyze cryptocurrency market sentiment based on price and volume data.

    This tool calculates sentiment scores from price momentum, volume patterns, and
    volatility. Use this to gauge the overall market sentiment (bullish, bearish,
    or neutral) for a cryptocurrency.

    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
    timeframe : str
        Analysis timeframe (e.g., "1h", "4h", "1d")
    period : int
        Number of candles to analyze (minimum 5)
    exchange : str
        Exchange name (default "binance")

    Returns
    -------
    str
        JSON string with sentiment score, label (very_bullish/bullish/neutral/bearish/very_bearish),
        and component scores
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines or len(klines) < 5:
                return json.dumps({"error": f"Insufficient data for {symbol} (need at least 5 candles)"})

            closes = [float(kline.close) for kline in klines]
            volumes = [float(kline.volume) for kline in klines]
            highs = [float(kline.high) for kline in klines]
            lows = [float(kline.low) for kline in klines]

            # Calculate sentiment components
            price_momentum = calculate_price_momentum(closes)
            volume_sentiment = calculate_volume_sentiment(volumes)
            volatility_sentiment = calculate_volatility_sentiment(highs, lows, closes)

            # Weighted sentiment score
            weights = {"price": 0.5, "volume": 0.3, "volatility": 0.2}
            sentiment_score = (
                price_momentum * weights["price"]
                + volume_sentiment * weights["volume"]
                + volatility_sentiment * weights["volatility"]
            )
            sentiment_score = max(-1, min(1, sentiment_score))

            # Sentiment label
            if sentiment_score > 0.6:
                label = "very_bullish"
            elif sentiment_score > 0.2:
                label = "bullish"
            elif sentiment_score > -0.2:
                label = "neutral"
            elif sentiment_score > -0.6:
                label = "bearish"
            else:
                label = "very_bearish"

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": "aster",
                "analysis_period": period,
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": label,
                "components": {
                    "price_momentum": round(price_momentum, 3),
                    "volume_sentiment": round(volume_sentiment, 3),
                    "volatility_sentiment": round(volatility_sentiment, 3),
                },
                "weights": weights,
                "analysis_timestamp": datetime.now(UTC).isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing sentiment: {e!s}", "symbol": symbol})


# Helper Functions
def calculate_sma(prices: list[float], period: int) -> list[float]:
    """Calculate Simple Moving Average.

    Parameters
    ----------
    prices : list[float]
        Price data
    period : int
        SMA period

    Returns
    -------
    list[float]
        SMA values
    """
    if len(prices) < period:
        return []
    return [sum(prices[i - period + 1 : i + 1]) / period for i in range(period - 1, len(prices))]


def find_support_levels(lows: list[float], num_levels: int = 3) -> list[float]:
    """Find support levels from low prices.

    Parameters
    ----------
    lows : list[float]
        Low prices
    num_levels : int
        Number of levels to return

    Returns
    -------
    list[float]
        Support levels
    """
    if len(lows) < 5:
        return []
    support = [
        lows[i]
        for i in range(2, len(lows) - 2)
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 2]
    ]
    return sorted(support)[:num_levels]


def find_resistance_levels(highs: list[float], num_levels: int = 3) -> list[float]:
    """Find resistance levels from high prices.

    Parameters
    ----------
    highs : list[float]
        High prices
    num_levels : int
        Number of levels to return

    Returns
    -------
    list[float]
        Resistance levels
    """
    if len(highs) < 5:
        return []
    resistance = [
        highs[i]
        for i in range(2, len(highs) - 2)
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 2]
    ]
    return sorted(resistance, reverse=True)[:num_levels]


def determine_trend(closes: list[float], sma_short: list[float], sma_long: list[float]) -> str:
    """Determine overall trend.

    Parameters
    ----------
    closes : list[float]
        Close prices
    sma_short : list[float]
        Short SMA
    sma_long : list[float]
        Long SMA

    Returns
    -------
    str
        Trend label
    """
    if not sma_short or not sma_long:
        return "insufficient_data"

    current_price = closes[-1]
    short_sma = sma_short[-1]
    long_sma = sma_long[-1]

    if current_price > short_sma > long_sma:
        return "strong_bullish"
    if current_price > short_sma:
        return "bullish"
    if current_price < short_sma < long_sma:
        return "strong_bearish"
    if current_price < short_sma:
        return "bearish"
    return "sideways"


def calculate_volume_trend(volumes: list[float]) -> str:
    """Calculate volume trend.

    Parameters
    ----------
    volumes : list[float]
        Volume data

    Returns
    -------
    str
        Volume trend label
    """
    if len(volumes) < 3:
        return "insufficient_data"
    recent_avg = sum(volumes[-3:]) / 3
    earlier_avg = sum(volumes[:3]) / 3
    if recent_avg > earlier_avg * 1.2:
        return "increasing"
    if recent_avg < earlier_avg * 0.8:
        return "decreasing"
    return "stable"


def calculate_volume_price_correlation(volumes: list[float], closes: list[float]) -> float:
    """Calculate correlation between volume and price.

    Parameters
    ----------
    volumes : list[float]
        Volume data
    closes : list[float]
        Close prices

    Returns
    -------
    float
        Correlation coefficient
    """
    if len(volumes) != len(closes) or len(volumes) < 2:
        return 0.0
    price_changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    volumes_adjusted = volumes[1:]
    if len(price_changes) < 2:
        return 0.0
    correlation = np.corrcoef(price_changes, volumes_adjusted)[0, 1]
    return correlation if not np.isnan(correlation) else 0.0


def identify_volume_spikes(volumes: list[float], avg_volume: float, threshold: float = 2.0) -> list[dict]:
    """Identify volume spikes.

    Parameters
    ----------
    volumes : list[float]
        Volume data
    avg_volume : float
        Average volume
    threshold : float
        Spike threshold multiplier

    Returns
    -------
    list[dict]
        Volume spikes with index, volume, and ratio
    """
    spikes = []
    for i, volume in enumerate(volumes):
        if volume > avg_volume * threshold:
            spikes.append({"index": i, "volume": volume, "ratio": volume / avg_volume if avg_volume > 0 else 0})
    return spikes


def calculate_price_momentum(closes: list[float]) -> float:
    """Calculate price momentum sentiment.

    Parameters
    ----------
    closes : list[float]
        Close prices

    Returns
    -------
    float
        Momentum score (-1 to 1)
    """
    if len(closes) < 2:
        return 0.0
    roc = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0
    return max(-1, min(1, roc * 10))


def calculate_volume_sentiment(volumes: list[float]) -> float:
    """Calculate volume-based sentiment.

    Parameters
    ----------
    volumes : list[float]
        Volume data

    Returns
    -------
    float
        Volume sentiment score (-1 to 1)
    """
    if len(volumes) < 3:
        return 0.0
    recent_avg = sum(volumes[-3:]) / 3
    overall_avg = sum(volumes) / len(volumes)
    volume_ratio = recent_avg / overall_avg if overall_avg > 0 else 1

    if volume_ratio > 1.5:
        return 0.8
    if volume_ratio > 1.2:
        return 0.4
    if volume_ratio < 0.5:
        return -0.8
    if volume_ratio < 0.8:
        return -0.4
    return 0.0


def calculate_volatility_sentiment(highs: list[float], lows: list[float], closes: list[float]) -> float:
    """Calculate volatility-based sentiment.

    Parameters
    ----------
    highs : list[float]
        High prices
    lows : list[float]
        Low prices
    closes : list[float]
        Close prices

    Returns
    -------
    float
        Volatility sentiment score (-1 to 1)
    """
    if len(highs) < 2:
        return 0.0
    atr_values = []
    for i in range(1, len(highs)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        atr_values.append(tr)

    avg_atr = sum(atr_values) / len(atr_values) if atr_values else 0
    current_price = closes[-1]
    volatility = (avg_atr / current_price) * 100 if current_price > 0 else 0

    if volatility > 5:
        return -0.6
    if volatility > 3:
        return -0.3
    if volatility < 1:
        return 0.3
    return 0.0
