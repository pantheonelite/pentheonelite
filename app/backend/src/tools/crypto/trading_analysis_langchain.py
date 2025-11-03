"""Trading strategy and analysis tools migrated to LangChain @tool decorator pattern.

This module provides trading strategy analysis and price/volume analysis tools using
the @tool decorator instead of BaseTool classes.
"""

import json
from datetime import datetime

import numpy as np
from app.backend.client import AsterClient
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .technical_indicators_langchain import technical_indicators


# Input Schemas
class TradingStrategyInput(BaseModel):
    """Input schema for trading strategy analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=100, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")
    strategy_type: str = Field(
        default="comprehensive", description="Strategy type: comprehensive, momentum, mean_reversion, breakout"
    )


class PriceTrendInput(BaseModel):
    """Input schema for price trend analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


class VolumeAnalysisInput(BaseModel):
    """Input schema for volume analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


class CryptoSentimentInput(BaseModel):
    """Input schema for crypto sentiment analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=24, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")


# Tool Functions
@tool(args_schema=TradingStrategyInput)
def trading_strategy_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 100,
    exchange: str = "binance",
    strategy_type: str = "comprehensive",
) -> str:
    """Analyze trading strategies and generate buy/sell signals using technical indicators.

    This tool evaluates different trading strategies (momentum, mean reversion, breakout,
    or comprehensive) and provides trading signals with confidence scores. Use this when
    you need to make trading decisions based on technical analysis.

    Strategy Types:
    - comprehensive: Combines multiple indicators for balanced analysis
    - momentum: Focuses on price momentum and trend following
    - mean_reversion: Identifies overbought/oversold conditions
    - breakout: Detects price breakouts from volatility bands

    The tool analyzes RSI, MACD, Bollinger Bands, moving averages, volume, and other
    indicators to generate BUY/SELL/HOLD signals with confidence scores.

    Parameters
    ----------
    symbol : str
        Trading pair (e.g., "BTCUSDT")
    timeframe : str
        Analysis timeframe (e.g., "1h", "4h")
    period : int
        Number of candles to analyze
    exchange : str
        Exchange name
    strategy_type : str
        Strategy type to use

    Returns
    -------
    str
        JSON with strategy analysis, signal (BUY/SELL/HOLD), confidence score, and reasoning
    """
    try:
        # Get technical indicators
        indicators_result = technical_indicators.invoke(
            {"symbol": symbol, "timeframe": timeframe, "period": period, "exchange": exchange}
        )
        indicators_data = json.loads(indicators_result)

        if "error" in indicators_data:
            return json.dumps({"error": indicators_data["error"]})

        indicators = indicators_data["indicators"]
        current_price = indicators_data["current_price"]

        # Analyze based on strategy type
        if strategy_type == "momentum":
            analysis = _analyze_momentum_strategy(indicators, current_price)
        elif strategy_type == "mean_reversion":
            analysis = _analyze_mean_reversion_strategy(indicators, current_price)
        elif strategy_type == "breakout":
            analysis = _analyze_breakout_strategy(indicators, current_price)
        else:  # comprehensive
            analysis = _analyze_comprehensive_strategy(indicators, current_price)

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
            "strategy_type": strategy_type,
            "analysis_timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "strategy_analysis": analysis,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error analyzing strategy: {e!s}"})


@tool(args_schema=PriceTrendInput)
def price_trend_analysis(symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
    """Analyze cryptocurrency price trends and patterns.

    This tool examines price movements, calculates moving averages, identifies support
    and resistance levels, and determines overall trend direction. Use this when you
    need to understand the price action and trend of a cryptocurrency.

    Parameters
    ----------
    symbol : str
        Trading pair
    timeframe : str
        Analysis timeframe
    period : int
        Number of periods to analyze
    exchange : str
        Exchange name

    Returns
    -------
    str
        JSON with trend analysis including current price, price change, trend direction,
        moving averages, and support/resistance levels
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines:
                return json.dumps({"error": f"No data available for {symbol}"})

            closes = [float(kline.close) for kline in klines]
            highs = [float(kline.high) for kline in klines]
            lows = [float(kline.low) for kline in klines]

            # Calculate trend indicators
            sma_short = _calculate_sma(closes, min(5, len(closes)))
            sma_long = _calculate_sma(closes, min(20, len(closes)))

            # Price momentum
            price_change = closes[-1] - closes[0] if len(closes) > 1 else 0
            price_change_percent = (price_change / closes[0]) * 100 if closes[0] != 0 else 0

            # Support and resistance
            support_levels = _find_support_levels(lows)
            resistance_levels = _find_resistance_levels(highs)

            # Trend determination
            trend = _determine_trend(closes, sma_short, sma_long)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": exchange,
                "analysis_period": period,
                "current_price": closes[-1],
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "trend": trend,
                "sma_short": round(sma_short[-1], 2) if sma_short else None,
                "sma_long": round(sma_long[-1], 2) if sma_long else None,
                "support_levels": [round(x, 2) for x in support_levels],
                "resistance_levels": [round(x, 2) for x in resistance_levels],
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing price trend: {e!s}"})


@tool(args_schema=VolumeAnalysisInput)
def volume_analysis(symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
    """Analyze trading volume patterns and market sentiment.

    This tool examines volume trends, calculates volume-price correlation, and identifies
    volume spikes that may indicate significant market moves. Use this to understand
    the strength behind price movements.

    Parameters
    ----------
    symbol : str
        Trading pair
    timeframe : str
        Analysis timeframe
    period : int
        Number of periods to analyze
    exchange : str
        Exchange name

    Returns
    -------
    str
        JSON with volume metrics, trend, volume-price correlation, and volume spikes
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines:
                return json.dumps({"error": f"No data available for {symbol}"})

            volumes = [float(kline.volume) for kline in klines]
            closes = [float(kline.close) for kline in klines]

            if not volumes or not closes:
                return json.dumps({"error": "No volume/price data available"})

            # Calculate volume metrics
            avg_volume = sum(volumes) / len(volumes)
            max_volume = max(volumes)
            min_volume = min(volumes)
            current_volume = volumes[-1]

            # Volume trend
            volume_trend = _calculate_volume_trend(volumes)

            # Volume-price correlation
            correlation = _calculate_volume_price_correlation(volumes, closes)

            # Volume spikes
            spikes = _identify_volume_spikes(volumes, avg_volume)

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": exchange,
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
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing volume: {e!s}"})


@tool(args_schema=CryptoSentimentInput)
def crypto_sentiment_analysis(symbol: str, timeframe: str = "1h", period: int = 24, exchange: str = "binance") -> str:
    """Analyze cryptocurrency market sentiment based on price and volume data.

    This tool calculates sentiment scores from price momentum, volume patterns, and
    volatility. Use this to gauge the overall market sentiment (bullish, bearish,
    or neutral) for a cryptocurrency.

    Parameters
    ----------
    symbol : str
        Trading pair
    timeframe : str
        Analysis timeframe
    period : int
        Number of periods to analyze
    exchange : str
        Exchange name

    Returns
    -------
    str
        JSON with sentiment score, label (very_bullish/bullish/neutral/bearish/very_bearish),
        and component scores
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines:
                return json.dumps({"error": f"No data available for {symbol}"})

            closes = [float(kline.close) for kline in klines]
            volumes = [float(kline.volume) for kline in klines]
            highs = [float(kline.high) for kline in klines]
            lows = [float(kline.low) for kline in klines]

            if not closes or not volumes:
                return json.dumps({"error": "No price/volume data available"})

            # Calculate sentiment components
            price_momentum = _calculate_price_momentum(closes)
            volume_sentiment = _calculate_volume_sentiment(volumes)
            volatility_sentiment = _calculate_volatility_sentiment(highs, lows, closes)

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
                "exchange": exchange,
                "analysis_period": period,
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": label,
                "components": {
                    "price_momentum": round(price_momentum, 3),
                    "volume_sentiment": round(volume_sentiment, 3),
                    "volatility_sentiment": round(volatility_sentiment, 3),
                },
                "weights": weights,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing sentiment: {e!s}"})


# Helper functions (not exported as tools)
def _analyze_momentum_strategy(indicators: dict, current_price: float) -> dict:
    """Analyze momentum-based trading strategy."""
    signals = []
    confidence = 0

    rsi_data = indicators.get("rsi", {})
    if rsi_data.get("rsi"):
        rsi = rsi_data["rsi"]
        if rsi < 30:
            signals.append("RSI oversold - potential momentum reversal")
            confidence += 20
        elif rsi > 70:
            signals.append("RSI overbought - potential momentum reversal")
            confidence -= 20

    macd_data = indicators.get("macd", {})
    if macd_data.get("signal") == "bullish":
        signals.append("MACD bullish crossover")
        confidence += 25
    elif macd_data.get("signal") == "bearish":
        signals.append("MACD bearish crossover")
        confidence -= 25

    ma_data = indicators.get("moving_averages", {})
    if ma_data.get("trend") == "bullish":
        signals.append("Price above moving averages - bullish momentum")
        confidence += 15
    elif ma_data.get("trend") == "bearish":
        signals.append("Price below moving averages - bearish momentum")
        confidence -= 15

    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume confirms momentum")
        confidence += 10

    signal = "BUY" if confidence > 30 else "SELL" if confidence < -30 else "HOLD"
    return {"signal": signal, "confidence": min(abs(confidence), 100), "signals": signals, "strategy": "momentum"}


def _analyze_mean_reversion_strategy(indicators: dict, current_price: float) -> dict:
    """Analyze mean reversion trading strategy."""
    signals = []
    confidence = 0

    bb_data = indicators.get("bollinger_bands", {})
    if bb_data.get("signal") == "oversold":
        signals.append("Price below lower Bollinger Band - oversold")
        confidence += 30
    elif bb_data.get("signal") == "overbought":
        signals.append("Price above upper Bollinger Band - overbought")
        confidence -= 30

    stoch_data = indicators.get("stochastic", {})
    if stoch_data.get("signal") == "oversold":
        signals.append("Stochastic oversold - mean reversion opportunity")
        confidence += 20
    elif stoch_data.get("signal") == "overbought":
        signals.append("Stochastic overbought - mean reversion opportunity")
        confidence -= 20

    williams_data = indicators.get("williams_r", {})
    if williams_data.get("signal") == "oversold":
        signals.append("Williams %R oversold")
        confidence += 15
    elif williams_data.get("signal") == "overbought":
        signals.append("Williams %R overbought")
        confidence -= 15

    signal = "BUY" if confidence > 25 else "SELL" if confidence < -25 else "HOLD"
    return {
        "signal": signal,
        "confidence": min(abs(confidence), 100),
        "signals": signals,
        "strategy": "mean_reversion",
    }


def _analyze_breakout_strategy(indicators: dict, current_price: float) -> dict:
    """Analyze breakout trading strategy."""
    signals = []
    confidence = 0

    bb_data = indicators.get("bollinger_bands", {})
    if bb_data.get("upper") and current_price > bb_data["upper"]:
        signals.append("Price breaking above upper Bollinger Band")
        confidence += 25
    elif bb_data.get("lower") and current_price < bb_data["lower"]:
        signals.append("Price breaking below lower Bollinger Band")
        confidence -= 25

    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume confirms breakout")
        confidence += 20

    atr_data = indicators.get("atr", {})
    if atr_data.get("signal") == "high_volatility":
        signals.append("High volatility supports breakout")
        confidence += 15

    macd_data = indicators.get("macd", {})
    if macd_data.get("signal") == "bullish":
        signals.append("MACD bullish - breakout momentum")
        confidence += 10
    elif macd_data.get("signal") == "bearish":
        signals.append("MACD bearish - breakdown momentum")
        confidence -= 10

    signal = "BUY" if confidence > 20 else "SELL" if confidence < -20 else "HOLD"
    return {"signal": signal, "confidence": min(abs(confidence), 100), "signals": signals, "strategy": "breakout"}


def _analyze_comprehensive_strategy(indicators: dict, current_price: float) -> dict:
    """Analyze comprehensive trading strategy combining multiple approaches."""
    signals = []
    confidence = 0

    rsi_data = indicators.get("rsi", {})
    if rsi_data.get("rsi"):
        rsi = rsi_data["rsi"]
        if rsi < 30:
            signals.append("RSI oversold")
            confidence += 15
        elif rsi > 70:
            signals.append("RSI overbought")
            confidence -= 15

    macd_data = indicators.get("macd", {})
    if macd_data.get("signal") == "bullish":
        signals.append("MACD bullish")
        confidence += 20
    elif macd_data.get("signal") == "bearish":
        signals.append("MACD bearish")
        confidence -= 20

    bb_data = indicators.get("bollinger_bands", {})
    if bb_data.get("signal") == "oversold":
        signals.append("Bollinger Bands oversold")
        confidence += 15
    elif bb_data.get("signal") == "overbought":
        signals.append("Bollinger Bands overbought")
        confidence -= 15

    ma_data = indicators.get("moving_averages", {})
    if ma_data.get("trend") == "bullish":
        signals.append("Bullish moving average trend")
        confidence += 10
    elif ma_data.get("trend") == "bearish":
        signals.append("Bearish moving average trend")
        confidence -= 10

    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume activity")
        confidence += 10

    stoch_data = indicators.get("stochastic", {})
    if stoch_data.get("signal") == "oversold":
        signals.append("Stochastic oversold")
        confidence += 10
    elif stoch_data.get("signal") == "overbought":
        signals.append("Stochastic overbought")
        confidence -= 10

    signal = "BUY" if confidence > 40 else "SELL" if confidence < -40 else "HOLD"
    return {"signal": signal, "confidence": min(abs(confidence), 100), "signals": signals, "strategy": "comprehensive"}


def _calculate_sma(prices: list[float], period: int) -> list[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return []
    return [sum(prices[i - period + 1 : i + 1]) / period for i in range(period - 1, len(prices))]


def _find_support_levels(lows: list[float], num_levels: int = 3) -> list[float]:
    """Find support levels from low prices."""
    if len(lows) < 5:
        return []
    support = [
        lows[i]
        for i in range(2, len(lows) - 2)
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 2]
    ]
    return sorted(support)[:num_levels]


def _find_resistance_levels(highs: list[float], num_levels: int = 3) -> list[float]:
    """Find resistance levels from high prices."""
    if len(highs) < 5:
        return []
    resistance = [
        highs[i]
        for i in range(2, len(highs) - 2)
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 2]
    ]
    return sorted(resistance, reverse=True)[:num_levels]


def _determine_trend(closes: list[float], sma_short: list[float], sma_long: list[float]) -> str:
    """Determine overall trend."""
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


def _calculate_volume_trend(volumes: list[float]) -> str:
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


def _calculate_volume_price_correlation(volumes: list[float], closes: list[float]) -> float:
    """Calculate correlation between volume and price."""
    if len(volumes) != len(closes) or len(volumes) < 2:
        return 0.0
    price_changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    volumes_adjusted = volumes[1:]
    if len(price_changes) < 2:
        return 0.0
    correlation = np.corrcoef(price_changes, volumes_adjusted)[0, 1]
    return correlation if not np.isnan(correlation) else 0.0


def _identify_volume_spikes(volumes: list[float], avg_volume: float, threshold: float = 2.0) -> list[dict]:
    """Identify volume spikes."""
    spikes = []
    for i, volume in enumerate(volumes):
        if volume > avg_volume * threshold:
            spikes.append({"index": i, "volume": volume, "ratio": volume / avg_volume if avg_volume > 0 else 0})
    return spikes


def _calculate_price_momentum(closes: list[float]) -> float:
    """Calculate price momentum sentiment."""
    if len(closes) < 2:
        return 0.0
    roc = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0
    return max(-1, min(1, roc * 10))


def _calculate_volume_sentiment(volumes: list[float]) -> float:
    """Calculate volume-based sentiment."""
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


def _calculate_volatility_sentiment(highs: list[float], lows: list[float], closes: list[float]) -> float:
    """Calculate volatility-based sentiment."""
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


# Export list
