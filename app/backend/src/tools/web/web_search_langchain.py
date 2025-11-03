"""Web search tools migrated to LangChain @tool decorator pattern.

This module provides web search and crypto sentiment analysis tools using the @tool
decorator instead of BaseTool classes. Uses DuckDuckGo (DDGS) for web search and
RSS feeds for news aggregation.
"""

import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

import feedparser
import structlog
from ddgs import DDGS
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# Input Schemas
class WebSearchInput(BaseModel):
    """Input schema for web search."""

    query: str = Field(description="Search query")
    max_results: int = Field(default=10, description="Maximum number of results to return")


class CryptoNewsSearchInput(BaseModel):
    """Input schema for crypto news search."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTC, ETH, BTCUSDT)")
    max_results: int = Field(default=10, description="Maximum number of news articles to return")
    include_rss: bool = Field(default=True, description="Whether to include RSS feed results")


class CryptoWebSentimentInput(BaseModel):
    """Input schema for crypto web sentiment analysis."""

    symbol: str = Field(description="Cryptocurrency symbol to analyze sentiment for")
    max_results: int = Field(default=10, description="Maximum number of articles to analyze")


class RSSNewsInput(BaseModel):
    """Input schema for RSS news fetching."""

    max_results: int = Field(default=30, description="Maximum number of news items to return")
    hours: int = Field(default=12, description="Number of hours to look back for news")


# Tool Functions
@tool(args_schema=WebSearchInput)
def duckduckgo_web_search(query: str, max_results: int = 10) -> str:
    """Search the web using DuckDuckGo search engine.

    This tool performs web searches using DuckDuckGo without requiring API keys.
    Use this when you need to find current information about any topic from the web.

    Parameters
    ----------
    query : str
        Search query (e.g., "bitcoin price analysis 2024")
    max_results : int
        Maximum number of search results to return (default: 10)

    Returns
    -------
    str
        JSON string with search results including titles, links, snippets, and sources
    """
    try:
        logger.info("Searching DuckDuckGo", query=query)

        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(query=query, max_results=max_results, backend="auto"))

        search_results = [
            {
                "title": result.get("title", ""),
                "link": result.get("href", ""),
                "snippet": result.get("body", ""),
                "source": _extract_domain(result.get("href", "")),
                "date": result.get("date", None),
            }
            for result in results
        ]

        logger.info("DuckDuckGo results", count=len(search_results), query=query)
        return json.dumps(search_results, indent=2)

    except Exception as e:
        logger.exception("DuckDuckGo search failed", error=str(e))
        return json.dumps({"error": f"Search failed: {e!s}"})


@tool(args_schema=CryptoNewsSearchInput)
def crypto_news_search(symbol: str, max_results: int = 10, *, include_rss: bool = True) -> str:
    """Search for cryptocurrency news using DuckDuckGo and RSS feeds.

    This tool finds recent news articles about a specific cryptocurrency using web search
    and crypto news RSS feeds. Use this when you need current news and sentiment about
    a particular crypto asset.

    Parameters
    ----------
    symbol : str
        Cryptocurrency symbol (e.g., "BTC", "ETH", "BTCUSDT", "SOLUSDT")
    max_results : int
        Maximum number of news articles to return (default: 10)
    include_rss : bool
        Whether to include RSS feed results (default: True)

    Returns
    -------
    str
        JSON string with news articles including titles, links, snippets, sources, and dates
    """
    try:
        # Clean up symbol
        clean_symbol = symbol.replace("/USDT", "").replace("USDT", "").replace("/", "").strip()

        # Create crypto-specific search query
        crypto_query = (
            "cryptocurrency news market analysis"
            if len(clean_symbol) < 2
            else f"{clean_symbol} crypto news price analysis"
        )

        logger.info("Searching crypto news", symbol=symbol, clean_symbol=clean_symbol)

        results: list[dict] = []

        # Get DuckDuckGo search results
        ddg_results = json.loads(
            duckduckgo_web_search.invoke({"query": crypto_query, "max_results": max_results // 2})
        )
        if isinstance(ddg_results, list):
            results.extend(ddg_results)

        # Get RSS feed results if requested
        if include_rss:
            rss_news = _fetch_rss_news(max_results // 2, hours=12)

            # Filter RSS results for the symbol
            symbol_lower = clean_symbol.lower()
            for news in rss_news:
                title_lower = news["title"].lower()
                desc_lower = news["description"].lower()

                if symbol_lower in title_lower or symbol_lower in desc_lower:
                    results.append(
                        {
                            "title": news["title"],
                            "link": news["link"],
                            "snippet": news["description"],
                            "source": news["source"],
                            "date": news["published"],
                        }
                    )

        # Remove duplicates based on URL
        seen_urls: set[str] = set()
        unique_results: list[dict] = []
        for result in results:
            if result["link"] not in seen_urls:
                seen_urls.add(result["link"])
                unique_results.append(result)

        logger.info("Crypto news results", count=len(unique_results), symbol=symbol)
        return json.dumps(unique_results[:max_results], indent=2)

    except Exception as e:
        logger.exception("Crypto news search failed", error=str(e))
        return json.dumps({"error": f"Crypto news search failed: {e!s}"})


@tool(args_schema=CryptoWebSentimentInput)
def crypto_web_sentiment(symbol: str, max_results: int = 10) -> str:
    """Analyze cryptocurrency sentiment from web news sources.

    This tool analyzes sentiment of news articles about a cryptocurrency using keyword
    analysis. It provides an overall sentiment score (-1 to 1) and label (positive,
    negative, neutral). Use this to gauge market sentiment from news sources.

    Parameters
    ----------
    symbol : str
        Cryptocurrency symbol to analyze
    max_results : int
        Maximum number of articles to analyze

    Returns
    -------
    str
        JSON string with sentiment score, label, article count, and detailed article sentiments
    """
    try:
        # Get news results
        news_results = json.loads(
            crypto_news_search.invoke({"symbol": symbol, "max_results": max_results, "include_rss": True})
        )

        if "error" in news_results or not isinstance(news_results, list) or len(news_results) == 0:
            return json.dumps(
                {
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "total_articles": 0,
                    "positive_articles": 0,
                    "negative_articles": 0,
                    "neutral_articles": 0,
                    "articles": [],
                }
            )

        # Keyword-based sentiment analysis
        positive_keywords = [
            "bullish",
            "surge",
            "rally",
            "moon",
            "pump",
            "breakthrough",
            "adoption",
            "partnership",
            "upgrade",
            "positive",
            "growth",
            "increase",
            "rise",
            "gain",
            "profit",
        ]

        negative_keywords = [
            "bearish",
            "crash",
            "dump",
            "decline",
            "drop",
            "fall",
            "negative",
            "loss",
            "sell-off",
            "fear",
            "panic",
            "concern",
            "risk",
            "warning",
            "downturn",
        ]

        sentiment_scores: list[float] = []
        articles: list[dict] = []

        for result in news_results:
            text = f"{result['title']} {result['snippet']}".lower()

            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)

            # Calculate sentiment score (-1 to 1)
            if positive_count + negative_count == 0:
                sentiment = 0.0
            else:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)

            sentiment_scores.append(sentiment)

            articles.append(
                {
                    "title": result["title"],
                    "link": result["link"],
                    "source": result["source"],
                    "sentiment": round(sentiment, 3),
                    "date": result.get("date"),
                }
            )

        # Calculate overall sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        # Determine sentiment label
        if avg_sentiment > 0.1:
            sentiment_label = "positive"
        elif avg_sentiment < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        # Count articles by sentiment
        positive_articles = sum(1 for s in sentiment_scores if s > 0.1)
        negative_articles = sum(1 for s in sentiment_scores if s < -0.1)
        neutral_articles = len(sentiment_scores) - positive_articles - negative_articles

        result = {
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": sentiment_label,
            "total_articles": len(articles),
            "positive_articles": positive_articles,
            "negative_articles": negative_articles,
            "neutral_articles": neutral_articles,
            "articles": articles,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.exception("Crypto web sentiment failed", error=str(e))
        return json.dumps({"error": f"Sentiment analysis failed: {e!s}"})


@tool(args_schema=RSSNewsInput)
def rss_news_feed(max_results: int = 30, hours: int = 12) -> str:
    """Fetch latest news from crypto RSS feeds.

    This tool aggregates news from multiple cryptocurrency news RSS feeds including
    Cointelegraph, CoinDesk, Decrypt, and others. Use this to get recent crypto news
    headlines.

    Parameters
    ----------
    max_results : int
        Maximum number of news items to return (default: 30)
    hours : int
        Number of hours to look back for news (default: 12)

    Returns
    -------
    str
        JSON string with news items including titles, links, descriptions, sources, and dates
    """
    try:
        news_items = _fetch_rss_news(max_results, hours)
        return json.dumps(news_items, indent=2)
    except Exception as e:
        logger.exception("RSS news fetch failed", error=str(e))
        return json.dumps({"error": f"RSS feed fetch failed: {e!s}"})


# Helper Functions
def _extract_domain(url: str) -> str | None:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    else:
        return parsed.netloc


def _fetch_rss_news(max_results: int = 30, hours: int = 12) -> list[dict]:
    """Fetch news from RSS feeds."""
    crypto_rss_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "https://cryptonews.com/news/feed/",
        "https://decrypt.co/feed",
        "https://u.today/rss",
        "https://cryptoslate.com/feed/",
    ]

    general_rss_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://feeds.bloomberg.com/markets/news.rss",
    ]

    all_feeds = crypto_rss_feeds + general_rss_feeds

    news_items: list[dict] = []
    cutoff_time = datetime.now(datetime.UTC) - timedelta(hours=hours)

    items_per_feed = max(1, max_results // len(all_feeds))

    for feed_url in all_feeds:
        if len(news_items) >= max_results * 1.2:
            break

        try:
            logger.debug("Fetching RSS feed", feed_url=feed_url)
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning("RSS feed parsing warning", feed_url=feed_url, error=str(feed.bozo_exception))
                continue

            for entry in feed.entries[:items_per_feed]:
                try:
                    # Parse publication date
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=datetime.UTC)
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6], tzinfo=datetime.UTC)

                    # Skip old news
                    if published and published < cutoff_time:
                        continue

                    news_items.append(
                        {
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "description": entry.get("description", ""),
                            "published": published.isoformat() if published else None,
                            "source": _extract_domain(feed_url),
                        }
                    )

                except Exception as e:
                    logger.warning("Error parsing RSS entry", feed_url=feed_url, error=str(e))
                    continue

        except Exception as e:
            logger.warning("Error fetching RSS feed", feed_url=feed_url, error=str(e))
            continue

    # Sort by publication date (newest first) and limit to max_results
    news_items.sort(key=lambda x: x["published"] or "1970-01-01T00:00:00+00:00", reverse=True)
    return news_items[:max_results]


# Export list
