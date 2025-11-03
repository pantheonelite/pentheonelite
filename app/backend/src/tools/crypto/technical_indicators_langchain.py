"""Technical indicators tools migrated to LangChain @tool decorator pattern.

This module provides technical analysis tools using the @tool decorator instead of BaseTool classes.
Includes RSI, MACD, Bollinger Bands, Stochastic Oscillator, ATR, Moving Averages, and more.
"""

import json
from datetime import UTC, datetime

import numpy as np
import talib
from app.backend.client import AsterClient
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Input Schemas
class TechnicalIndicatorsInput(BaseModel):
    """Input schema for technical indicators analysis."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT, ETHUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    period: int = Field(default=100, description="Number of periods to analyze (minimum 20)")
    exchange: str = Field(default="binance", description="Exchange name (default: binance)")


# Helper Functions
def calculate_rsi(closes: np.ndarray) -> dict:
    """Calculate RSI indicator."""
    try:
        rsi_values = talib.RSI(closes, timeperiod=14)
        rsi = float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else None
        if rsi is None:
            return {}
        signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
        return {"value": round(rsi, 2), "signal": signal}
    except Exception as e:
        return {"error": str(e)}


def calculate_macd(closes: np.ndarray) -> dict:
    """Calculate MACD indicator."""
    try:
        macd_line, signal_line, histogram = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
        macd_val = float(macd_line[-1]) if not np.isnan(macd_line[-1]) else None
        signal_val = float(signal_line[-1]) if not np.isnan(signal_line[-1]) else None
        hist_val = float(histogram[-1]) if not np.isnan(histogram[-1]) else None
        if not all(x is not None for x in [macd_val, signal_val, hist_val]):
            return {}
        signal = (
            "bullish"
            if macd_val > signal_val and hist_val > 0
            else "bearish"
            if macd_val < signal_val and hist_val < 0
            else "neutral"
        )
        return {
            "macd": round(macd_val, 4),
            "signal_line": round(signal_val, 4),
            "histogram": round(hist_val, 4),
            "signal": signal,
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_bollinger_bands(closes: np.ndarray) -> dict:
    """Calculate Bollinger Bands indicator."""
    try:
        upper, middle, lower = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)
        upper_val = float(upper[-1]) if not np.isnan(upper[-1]) else None
        middle_val = float(middle[-1]) if not np.isnan(middle[-1]) else None
        lower_val = float(lower[-1]) if not np.isnan(lower[-1]) else None
        if not all(x is not None for x in [upper_val, middle_val, lower_val]):
            return {}
        current_price = closes[-1]
        signal = "overbought" if current_price > upper_val else "oversold" if current_price < lower_val else "neutral"
        return {
            "upper": round(upper_val, 2),
            "middle": round(middle_val, 2),
            "lower": round(lower_val, 2),
            "signal": signal,
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_stochastic(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Calculate Stochastic Oscillator."""
    try:
        slowk, slowd = talib.STOCH(highs, lows, closes, fastk_period=14, slowk_period=3, slowd_period=3)
        k_val = float(slowk[-1]) if not np.isnan(slowk[-1]) else None
        d_val = float(slowd[-1]) if not np.isnan(slowd[-1]) else None
        if k_val is None or d_val is None:
            return {}
        signal = "overbought" if k_val > 80 and d_val > 80 else "oversold" if k_val < 20 and d_val < 20 else "neutral"
        return {"k": round(k_val, 2), "d": round(d_val, 2), "signal": signal}
    except Exception as e:
        return {"error": str(e)}


def calculate_williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Calculate Williams %R."""
    try:
        williams_r = talib.WILLR(highs, lows, closes, timeperiod=14)
        williams_val = float(williams_r[-1]) if not np.isnan(williams_r[-1]) else None
        if williams_val is None:
            return {}
        signal = "overbought" if williams_val > -20 else "oversold" if williams_val < -80 else "neutral"
        return {"value": round(williams_val, 2), "signal": signal}
    except Exception as e:
        return {"error": str(e)}


def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Calculate Average True Range."""
    try:
        atr = talib.ATR(highs, lows, closes, timeperiod=14)
        atr_val = float(atr[-1]) if not np.isnan(atr[-1]) else None
        if atr_val is None:
            return {}
        avg_atr = float(np.mean(atr[-14:]))
        signal = (
            "high_volatility"
            if atr_val > avg_atr * 1.5
            else "low_volatility"
            if atr_val < avg_atr * 0.5
            else "normal_volatility"
        )
        return {"value": round(atr_val, 4), "signal": signal}
    except Exception as e:
        return {"error": str(e)}


def calculate_moving_averages(closes: np.ndarray) -> dict:
    """Calculate Moving Averages."""
    try:
        sma_20 = talib.SMA(closes, timeperiod=20)
        sma_50 = talib.SMA(closes, timeperiod=50)
        ema_12 = talib.EMA(closes, timeperiod=12)
        ema_26 = talib.EMA(closes, timeperiod=26)

        ma_dict = {}
        if not np.isnan(sma_20[-1]):
            ma_dict["sma_20"] = round(float(sma_20[-1]), 2)
        if not np.isnan(sma_50[-1]):
            ma_dict["sma_50"] = round(float(sma_50[-1]), 2)
        if not np.isnan(ema_12[-1]):
            ma_dict["ema_12"] = round(float(ema_12[-1]), 2)
        if not np.isnan(ema_26[-1]):
            ma_dict["ema_26"] = round(float(ema_26[-1]), 2)

        if "sma_20" in ma_dict and "sma_50" in ma_dict:
            ma_dict["trend"] = (
                "bullish"
                if ma_dict["sma_20"] > ma_dict["sma_50"]
                else "bearish"
                if ma_dict["sma_20"] < ma_dict["sma_50"]
                else "neutral"
            )

        return ma_dict
    except Exception as e:
        return {"error": str(e)}


def calculate_volume_indicators(closes: np.ndarray, volumes: np.ndarray) -> dict:
    """Calculate Volume Indicators."""
    try:
        obv = talib.OBV(closes, volumes)
        obv_val = float(obv[-1]) if not np.isnan(obv[-1]) else None
        if obv_val is None:
            return {}
        recent_vol = float(np.mean(volumes[-5:]))
        avg_vol = float(np.mean(volumes))
        signal = (
            "high_volume"
            if recent_vol > avg_vol * 1.5
            else "low_volume"
            if recent_vol < avg_vol * 0.5
            else "normal_volume"
        )
        return {
            "obv": round(obv_val, 2),
            "signal": signal,
            "current_volume": round(volumes[-1], 2),
            "avg_volume": round(avg_vol, 2),
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_fibonacci_levels(highs: np.ndarray, lows: np.ndarray) -> dict:
    """Calculate Fibonacci retracement levels."""
    try:
        recent_high = float(np.max(highs[-20:]))
        recent_low = float(np.min(lows[-20:]))
        range_size = recent_high - recent_low

        return {
            "0%": round(recent_high, 2),
            "23.6%": round(recent_high - (range_size * 0.236), 2),
            "38.2%": round(recent_high - (range_size * 0.382), 2),
            "50%": round(recent_high - (range_size * 0.5), 2),
            "61.8%": round(recent_high - (range_size * 0.618), 2),
            "78.6%": round(recent_high - (range_size * 0.786), 2),
            "100%": round(recent_low, 2),
        }
    except Exception as e:
        return {"error": str(e)}


# Tool Functions
@tool(args_schema=TechnicalIndicatorsInput)
def technical_indicators_analysis(
    symbol: str,
    timeframe: str = "1h",
    period: int = 100,
    exchange: str = "binance",  # noqa: ARG001
) -> str:
    """Calculate comprehensive technical indicators for cryptocurrency analysis.

    This tool calculates multiple technical indicators including RSI, MACD, Bollinger Bands,
    Stochastic Oscillator, Williams %R, ATR, Moving Averages, Volume indicators, and
    Fibonacci levels. Use this for comprehensive technical analysis.

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

    Returns
    -------
    str
        JSON string with all calculated technical indicators and signals
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, period)

            if not klines or len(klines) < 20:
                return json.dumps({"error": f"Insufficient data for {symbol} (need at least 20 candles)"})

            # Extract price data
            highs = np.array([float(kline.high) for kline in klines], dtype=float)
            lows = np.array([float(kline.low) for kline in klines], dtype=float)
            closes = np.array([float(kline.close) for kline in klines], dtype=float)
            volumes = np.array([float(kline.volume) for kline in klines], dtype=float)

            # Calculate indicators using helper functions
            indicators = {
                "rsi": calculate_rsi(closes),
                "macd": calculate_macd(closes),
                "bollinger_bands": calculate_bollinger_bands(closes),
                "stochastic": calculate_stochastic(highs, lows, closes),
                "williams_r": calculate_williams_r(highs, lows, closes),
                "atr": calculate_atr(highs, lows, closes),
                "moving_averages": calculate_moving_averages(closes),
                "volume_indicators": calculate_volume_indicators(closes, volumes),
                "fibonacci_levels": calculate_fibonacci_levels(highs, lows),
            }

            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": "aster",
                "analysis_period": period,
                "current_price": round(closes[-1], 2),
                "analysis_timestamp": datetime.now(UTC).isoformat(),
                "indicators": indicators,
            }

            return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error calculating technical indicators: {e!s}", "symbol": symbol})
