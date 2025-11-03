"""Trading strategy tools migrated to LangChain @tool decorator pattern.

This module provides trading strategy analysis using the @tool decorator instead of BaseTool classes.
Includes momentum, mean reversion, breakout, and comprehensive strategy analysis.
"""

import json
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .technical_indicators_langchain import technical_indicators_analysis


class StrategyInput(BaseModel):
    """Input schema for trading strategy analysis tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    period: int = Field(default=100, description="Number of periods to analyze")
    exchange: str = Field(default="binance", description="Exchange name")
    strategy_type: str = Field(
        default="comprehensive",
        description="Strategy type: comprehensive, momentum, mean_reversion, breakout",
    )


def analyze_momentum_strategy(indicators: dict[str, Any]) -> dict[str, Any]:
    """Analyze momentum-based trading strategy."""
    signals = []
    confidence_score = 0

    # RSI momentum
    rsi_data = indicators.get("rsi", {})
    if rsi_data.get("value"):
        rsi = rsi_data["value"]
        if rsi < 30:  # Oversold - potential buy
            signals.append("RSI oversold - potential momentum reversal")
            confidence_score += 20
        elif rsi > 70:  # Overbought - potential sell
            signals.append("RSI overbought - potential momentum reversal")
            confidence_score -= 20

    # MACD momentum
    macd_data = indicators.get("macd", {})
    if macd_data.get("signal") == "bullish":
        signals.append("MACD bullish crossover")
        confidence_score += 25
    elif macd_data.get("signal") == "bearish":
        signals.append("MACD bearish crossover")
        confidence_score -= 25

    # Moving average momentum
    ma_data = indicators.get("moving_averages", {})
    if ma_data.get("trend") == "bullish":
        signals.append("Price above moving averages - bullish momentum")
        confidence_score += 15
    elif ma_data.get("trend") == "bearish":
        signals.append("Price below moving averages - bearish momentum")
        confidence_score -= 15

    # Volume confirmation
    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume confirms momentum")
        confidence_score += 10

    # Determine overall signal
    if confidence_score > 30:
        signal = "BUY"
    elif confidence_score < -30:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "confidence": min(abs(confidence_score), 100),
        "signals": signals,
        "strategy": "momentum",
    }


def analyze_mean_reversion_strategy(indicators: dict[str, Any]) -> dict[str, Any]:
    """Analyze mean reversion trading strategy."""
    signals = []
    confidence_score = 0

    # Bollinger Bands mean reversion
    bb_data = indicators.get("bollinger_bands", {})
    if bb_data.get("signal") == "oversold":
        signals.append("Price below lower Bollinger Band - oversold")
        confidence_score += 30
    elif bb_data.get("signal") == "overbought":
        signals.append("Price above upper Bollinger Band - overbought")
        confidence_score -= 30

    # Stochastic mean reversion
    stoch_data = indicators.get("stochastic", {})
    if stoch_data.get("signal") == "oversold":
        signals.append("Stochastic oversold - mean reversion opportunity")
        confidence_score += 20
    elif stoch_data.get("signal") == "overbought":
        signals.append("Stochastic overbought - mean reversion opportunity")
        confidence_score -= 20

    # Williams %R mean reversion
    williams_data = indicators.get("williams_r", {})
    if williams_data.get("signal") == "oversold":
        signals.append("Williams %R oversold")
        confidence_score += 15
    elif williams_data.get("signal") == "overbought":
        signals.append("Williams %R overbought")
        confidence_score -= 15

    # Determine overall signal
    if confidence_score > 25:
        signal = "BUY"
    elif confidence_score < -25:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "confidence": min(abs(confidence_score), 100),
        "signals": signals,
        "strategy": "mean_reversion",
    }


def analyze_breakout_strategy(indicators: dict[str, Any], current_price: float) -> dict[str, Any]:
    """Analyze breakout trading strategy."""
    signals = []
    confidence_score = 0

    # Bollinger Bands breakout
    bb_data = indicators.get("bollinger_bands", {})
    if bb_data.get("upper") and current_price > bb_data["upper"]:
        signals.append("Price breaking above upper Bollinger Band")
        confidence_score += 25
    elif bb_data.get("lower") and current_price < bb_data["lower"]:
        signals.append("Price breaking below lower Bollinger Band")
        confidence_score -= 25

    # Volume confirmation for breakout
    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume confirms breakout")
        confidence_score += 20

    # ATR for volatility
    atr_data = indicators.get("atr", {})
    if atr_data.get("signal") == "high_volatility":
        signals.append("High volatility supports breakout")
        confidence_score += 15

    # MACD momentum confirmation
    macd_data = indicators.get("macd", {})
    if macd_data.get("signal") == "bullish":
        signals.append("MACD bullish - breakout momentum")
        confidence_score += 10
    elif macd_data.get("signal") == "bearish":
        signals.append("MACD bearish - breakdown momentum")
        confidence_score -= 10

    # Determine overall signal
    if confidence_score > 20:
        signal = "BUY"
    elif confidence_score < -20:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "confidence": min(abs(confidence_score), 100),
        "signals": signals,
        "strategy": "breakout",
    }


def analyze_comprehensive_strategy(indicators: dict[str, Any]) -> dict[str, Any]:
    """Analyze comprehensive trading strategy combining multiple approaches."""
    signals = []
    confidence_score = 0

    # Define indicator scoring rules: (name, value_getter, [(condition, signal_text, score)])
    score_rules = [
        (
            "rsi",
            lambda d: d.get("value", 0),
            [(("<", 30), "RSI oversold", 15), ((">", 70), "RSI overbought", -15)],
        ),
        (
            "macd",
            lambda d: d.get("signal"),
            [("bullish", "MACD bullish", 20), ("bearish", "MACD bearish", -20)],
        ),
        (
            "bollinger_bands",
            lambda d: d.get("signal"),
            [("oversold", "Bollinger Bands oversold", 15), ("overbought", "Bollinger Bands overbought", -15)],
        ),
        (
            "moving_averages",
            lambda d: d.get("trend"),
            [("bullish", "Bullish MA trend", 10), ("bearish", "Bearish MA trend", -10)],
        ),
        (
            "stochastic",
            lambda d: d.get("signal"),
            [("oversold", "Stochastic oversold", 10), ("overbought", "Stochastic overbought", -10)],
        ),
    ]

    # Apply scoring rules
    for indicator_name, value_fn, rules in score_rules:
        data = indicators.get(indicator_name, {})
        value = value_fn(data)
        for condition, signal_text, score in rules:
            if isinstance(condition, str) and value == condition:
                signals.append(signal_text)
                confidence_score += score
            elif isinstance(condition, tuple) and len(condition) == 2:
                op, threshold = condition
                if (
                    op in ("<", ">")
                    and isinstance(value, (int, float))
                    and ((op == "<" and value < threshold) or (op == ">" and value > threshold))
                ):
                    signals.append(signal_text)
                    confidence_score += score

    # Volume analysis (special case)
    volume_data = indicators.get("volume_indicators", {})
    if volume_data.get("signal") == "high_volume":
        signals.append("High volume activity")
        confidence_score += 10

    # Determine overall signal
    if confidence_score > 40:
        signal = "BUY"
    elif confidence_score < -40:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "confidence": min(abs(confidence_score), 100),
        "signals": signals,
        "strategy": "comprehensive",
    }


@tool(args_schema=StrategyInput)
def trading_strategy_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 100,
    exchange: str = "binance",
    strategy_type: str = "comprehensive",
) -> str:
    """Analyze trading strategies using technical indicators and generate buy/sell signals.

    This tool analyzes trading strategies using technical indicators and provides
    buy/sell signals with confidence scores for momentum, mean reversion, breakout,
    and comprehensive strategies.

    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
    timeframe : str
        Analysis timeframe (e.g., "1h", "4h", "1d")
    period : int
        Number of candles to analyze (minimum 20)
    exchange : str
        Exchange name (default "binance")
    strategy_type : str
        Strategy type to use: "momentum", "mean_reversion", "breakout", or "comprehensive"

    Returns
    -------
    str
        JSON string with strategy analysis, signals, and confidence scores
    """
    try:
        # Get technical indicators
        indicators_result = technical_indicators_analysis(symbol, timeframe, period, exchange)
        indicators_data = json.loads(indicators_result)

        if "error" in indicators_data:
            return json.dumps({"error": indicators_data["error"]})

        indicators = indicators_data["indicators"]
        current_price = indicators_data["current_price"]

        # Analyze based on strategy type
        if strategy_type == "momentum":
            analysis = analyze_momentum_strategy(indicators)
        elif strategy_type == "mean_reversion":
            analysis = analyze_mean_reversion_strategy(indicators)
        elif strategy_type == "breakout":
            analysis = analyze_breakout_strategy(indicators, current_price)
        else:  # comprehensive
            analysis = analyze_comprehensive_strategy(indicators)

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
            "strategy_type": strategy_type,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "current_price": current_price,
            "strategy_analysis": analysis,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {
                "error": f"Error analyzing strategy: {e!s}",
                "symbol": symbol,
                "strategy_type": strategy_type,
            }
        )
