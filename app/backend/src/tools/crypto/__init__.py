"""Crypto data tools using Aster for cryptocurrency exchange integration.

This module provides LangChain-compatible tools for cryptocurrency trading analysis,
including market data, technical indicators, trading strategies, and sentiment analysis.

All tools use the @tool decorator pattern from langchain_core.tools for consistency
and compatibility with LangChain agents and LangGraph workflows.
"""

from .analysis_langchain import (
    crypto_sentiment_analysis,
    price_trend_analysis,
    volume_analysis,
)
from .aster_tools_langchain import (
    aster_get_account,
    aster_get_history,
    aster_get_multi_price,
    aster_get_order_book,
    aster_get_price,
)
from .technical_indicators_langchain import technical_indicators_analysis
from .trading_strategy_langchain import trading_strategy_analysis
from .websocket_client import MockWebSocketClient

__all__ = [
    "MockWebSocketClient",
    "aster_get_account",
    "aster_get_history",
    "aster_get_multi_price",
    "aster_get_order_book",
    "aster_get_price",
    "crypto_sentiment_analysis",
    "price_trend_analysis",
    "technical_indicators_analysis",
    "trading_strategy_analysis",
    "volume_analysis",
]
