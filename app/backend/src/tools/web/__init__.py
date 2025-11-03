"""Web search and crawling tools for crypto sentiment analysis.

This module provides LangChain-compatible tools for web search and news analysis,
including DuckDuckGo search, RSS feeds, and crypto sentiment analysis.

All tools use the @tool decorator pattern from langchain_core.tools for consistency
and compatibility with LangChain agents and LangGraph workflows.
"""

from .web_search_langchain import (
    crypto_news_search,
    crypto_web_sentiment,
    duckduckgo_web_search,
    rss_news_feed,
)

__all__ = [
    "crypto_news_search",
    "crypto_web_sentiment",
    "duckduckgo_web_search",
    "rss_news_feed",
]
