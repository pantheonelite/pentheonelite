"""News crawler tools migrated to LangChain @tool decorator pattern.

This module provides RSS feed crawling and news fetching functionality
using the @tool decorator instead of BaseTool classes.
"""

import asyncio
import json
from datetime import datetime

import aiohttp
import feedparser
import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class NewsCrawlerInput(BaseModel):
    """Input schema for news crawler tool."""

    symbol: str | None = Field(default=None, description="Cryptocurrency symbol to filter news")
    limit: int = Field(default=10, description="Number of news articles to fetch")
    hours: int = Field(default=24, description="Hours of news to fetch")


async def fetch_rss_news(limit: int = 10, hours: int = 24) -> list[dict]:  # noqa: ARG001
    """
    Fetch latest news from RSS feeds (crypto and general).

    Parameters
    ----------
    limit : int
        Maximum number of articles to fetch
    hours : int
        Hours of news to fetch

    Returns
    -------
    list[dict]
        List of news articles
    """
    crypto_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://cryptonews.com/news/feed/",
        "https://bitcoinmagazine.com/rss",
        "https://www.coinbureau.com/feed/",
    ]

    general_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.npr.org/1001/rss.xml",
        "https://feeds.washingtonpost.com/rss/world",
        "https://feeds.nbcnews.com/nbcnews/public/news",
    ]

    all_feeds = crypto_feeds + general_feeds
    all_news = []
    cutoff_time = datetime.now().replace(tzinfo=None)

    async with aiohttp.ClientSession() as session:
        for feed_url in all_feeds:
            try:
                async with session.get(feed_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)

                        for entry in feed.entries:
                            pub_date = parse_date(entry.get("published", ""))

                            if pub_date and pub_date.replace(tzinfo=None) >= cutoff_time:
                                article = {
                                    "title": entry.get("title", ""),
                                    "link": entry.get("link", ""),
                                    "summary": entry.get("summary", ""),
                                    "published": pub_date.isoformat(),
                                    "source": feed.feed.get("title", "Unknown"),
                                    "feed_url": feed_url,
                                }
                                all_news.append(article)

                                if len(all_news) >= limit * 2:
                                    break
            except Exception as exc:
                logger.exception(
                    "Error fetching news feed",
                    feed_url=feed_url,
                    error=str(exc),
                )
                continue

    all_news.sort(key=lambda x: x["published"], reverse=True)
    return all_news[:limit]


def parse_date(date_str: str) -> datetime | None:
    """
    Parse date string to datetime object.

    Parameters
    ----------
    date_str : str
        Date string to parse

    Returns
    -------
    datetime | None
        Parsed datetime or None if parsing failed
    """
    if not date_str:
        return None

    try:
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=None)  # noqa: DTZ007
            except ValueError:
                continue

        parsed = feedparser.parse(f"<item><pubDate>{date_str}</pubDate></item>")
        if parsed.entries:
            return datetime(*parsed.entries[0].published_parsed[:6]).replace(tzinfo=None)  # noqa: DTZ001

    except Exception as exc:
        logger.exception(
            "Error parsing news date",
            date_string=date_str,
            error=str(exc),
        )

    return None


@tool(args_schema=NewsCrawlerInput)
def crypto_news_crawler(symbol: str | None = None, limit: int = 10, hours: int = 24) -> str:
    """Crawl latest cryptocurrency news from RSS feeds.

    This tool fetches recent cryptocurrency and general financial news from multiple
    RSS feed sources. It can optionally filter articles by cryptocurrency symbol.
    Use this when you need current news for sentiment analysis or market context.

    Parameters
    ----------
    symbol : str | None
        Optional crypto symbol to filter news (e.g., "BTC", "ETH", "bitcoin")
    limit : int
        Maximum number of articles to fetch (default 10)
    hours : int
        Time range in hours for articles (default 24)

    Returns
    -------
    str
        JSON string containing:
        - symbol: Filter symbol used (if any)
        - articles_count: Number of articles returned
        - time_range_hours: Time range searched
        - articles: List of articles with title, link, summary, published date, and source
    """
    try:
        news = asyncio.run(fetch_rss_news(limit, hours))

        if symbol:
            symbol_lower = symbol.lower()
            news = [
                article
                for article in news
                if symbol_lower in article["title"].lower() or symbol_lower in article["summary"].lower()
            ]

        result = {
            "symbol": symbol,
            "articles_count": len(news),
            "time_range_hours": hours,
            "articles": news,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error crawling news: {e!s}"})
