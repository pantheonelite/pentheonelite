"""Tools package for crypto data, news crawling, and web search.

This module provides both legacy BaseTool classes and new LangChain @tool decorator
implementations for cryptocurrency analysis, news crawling, and web search.
"""

from .crypto import (
    aster_get_account,
    aster_get_history,
    aster_get_multi_price,
    aster_get_order_book,
    aster_get_price,
    crypto_sentiment_analysis,
    price_trend_analysis,
    technical_indicators_analysis,
    trading_strategy_analysis,
    volume_analysis,
)
from .news import (
    crypto_news_crawler,
    crypto_sentiment,
    crypto_web_scraper,
)
from .web import (
    crypto_news_search,
    crypto_web_sentiment,
    duckduckgo_web_search,
    rss_news_feed,
)

__all__ = [
    "aster_get_account",
    "aster_get_history",
    "aster_get_multi_price",
    "aster_get_order_book",
    "aster_get_price",
    "crypto_news_crawler",
    "crypto_news_search",
    "crypto_sentiment",
    "crypto_sentiment_analysis",
    "crypto_web_scraper",
    "crypto_web_sentiment",
    "duckduckgo_web_search",
    "price_trend_analysis",
    "rss_news_feed",
    "technical_indicators_analysis",
    "trading_strategy_analysis",
    "volume_analysis",
]
