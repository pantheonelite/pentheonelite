"""Web scraping tools migrated to LangChain @tool decorator pattern.

This module provides web scraping functionality for crypto news articles
using the @tool decorator instead of BaseTool classes.
"""

import asyncio
import json
from datetime import datetime

import aiohttp
import structlog
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class WebScrapingInput(BaseModel):
    """Input schema for web scraping tool."""

    url: str = Field(description="Article URL to scrape")


def extract_title(soup: BeautifulSoup) -> str:
    """
    Extract article title from HTML.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML document

    Returns
    -------
    str
        Extracted title or empty string
    """
    title_selectors = [
        "h1",
        ".article-title",
        ".post-title",
        ".entry-title",
        '[class*="title"]',
    ]

    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            return title_elem.get_text().strip()

    if soup.title and soup.title.string:
        return soup.title.string
    return ""


def extract_content(soup: BeautifulSoup) -> str:
    """
    Extract article content from HTML.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML document

    Returns
    -------
    str
        Extracted content or empty string
    """
    content_selectors = [
        ".article-content",
        ".post-content",
        ".entry-content",
        ".content",
        "article",
        '[class*="content"]',
    ]

    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            for script in content_elem(["script", "style"]):
                script.decompose()
            return content_elem.get_text().strip()

    return ""


async def scrape_url(url: str) -> dict:
    """
    Scrape article content from URL.

    Parameters
    ----------
    url : str
        Article URL to scrape

    Returns
    -------
    dict
        Article content and metadata
    """
    try:
        async with aiohttp.ClientSession() as session, session.get(url, timeout=15) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                content = extract_content(soup)

                return {
                    "url": url,
                    "title": extract_title(soup),
                    "content": content,
                    "scraped_at": datetime.now().isoformat(),
                    "word_count": len(content.split()) if content else 0,
                }
            return {"url": url, "error": f"HTTP {response.status}"}
    except Exception as exc:
        logger.exception(
            "Error scraping article",
            url=url,
            error=str(exc),
        )
        return {"url": url, "error": str(exc)}


@tool(args_schema=WebScrapingInput)
def crypto_web_scraper(url: str) -> str:
    """Scrape content from crypto news articles.

    This tool fetches and extracts the main content from cryptocurrency news
    article URLs. It handles various article layouts and extracts the title,
    body content, and metadata. Use this to get full article text for detailed
    analysis when you have article URLs.

    Parameters
    ----------
    url : str
        URL of the crypto news article to scrape

    Returns
    -------
    str
        JSON string containing:
        - url: Article URL
        - title: Extracted article title
        - content: Main article content text
        - scraped_at: Timestamp when scraping occurred
        - word_count: Number of words in content
        - error: Error message if scraping failed
    """
    try:
        content = asyncio.run(scrape_url(url))
        return json.dumps(content, indent=2)
    except Exception as e:
        return json.dumps({"url": url, "error": f"Error scraping article: {e!s}"})
