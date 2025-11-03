"""Sentiment analysis tools migrated to LangChain @tool decorator pattern.

This module provides crypto sentiment analysis functionality
using the @tool decorator instead of BaseTool classes.
"""

import json
from datetime import datetime

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class SentimentAnalysisInput(BaseModel):
    """Input schema for sentiment analysis tool."""

    text: str = Field(description="Text to analyze for sentiment")
    symbol: str | None = Field(default=None, description="Cryptocurrency symbol for context")


def analyze_crypto_sentiment(text: str, symbol: str | None = None) -> dict:  # noqa: ARG001
    """
    Analyze sentiment of crypto-related text.

    Parameters
    ----------
    text : str
        Text to analyze
    symbol : str | None
        Optional crypto symbol for context

    Returns
    -------
    dict
        Sentiment analysis results
    """
    positive_keywords = [
        "bullish",
        "moon",
        "pump",
        "surge",
        "rally",
        "breakthrough",
        "adoption",
        "partnership",
        "upgrade",
        "innovation",
        "growth",
        "positive",
        "optimistic",
        "strong",
        "gains",
        "increase",
    ]

    negative_keywords = [
        "bearish",
        "crash",
        "dump",
        "decline",
        "fall",
        "drop",
        "regulation",
        "ban",
        "hack",
        "scam",
        "fraud",
        "negative",
        "pessimistic",
        "weak",
        "losses",
        "decrease",
        "concern",
    ]

    crypto_keywords = [
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "crypto",
        "cryptocurrency",
        "blockchain",
        "defi",
        "nft",
        "altcoin",
        "trading",
        "market",
    ]

    text_lower = text.lower()

    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

    total_keywords = positive_count + negative_count
    sentiment_score = 0.0 if total_keywords == 0 else (positive_count - negative_count) / total_keywords

    if sentiment_score > 0.3:
        sentiment_label = "positive"
    elif sentiment_score < -0.3:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    crypto_relevance = sum(1 for keyword in crypto_keywords if keyword in text_lower)
    is_crypto_related = crypto_relevance > 0

    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "positive_keywords": positive_count,
        "negative_keywords": negative_count,
        "crypto_relevance": crypto_relevance,
        "is_crypto_related": is_crypto_related,
        "analysis_timestamp": datetime.now().isoformat(),
    }


@tool(args_schema=SentimentAnalysisInput)
def crypto_sentiment(text: str, symbol: str | None = None) -> str:
    """Analyze sentiment of crypto-related text content.

    This tool performs sentiment analysis on text to determine if it's positive,
    negative, or neutral towards cryptocurrencies. It counts relevant keywords
    and calculates a sentiment score. Use this to gauge market sentiment from
    news articles, social media, or other text sources.

    Parameters
    ----------
    text : str
        Text content to analyze (news article, tweet, etc.)
    symbol : str | None
        Optional crypto symbol for additional context (e.g., "BTC", "ETH")

    Returns
    -------
    str
        JSON string containing:
        - text_preview: Preview of analyzed text
        - symbol: Symbol context (if provided)
        - analysis: Sentiment analysis results including:
          * sentiment_score: Numeric score (-1.0 to 1.0)
          * sentiment_label: Classification (positive/negative/neutral)
          * positive_keywords: Count of positive keywords found
          * negative_keywords: Count of negative keywords found
          * crypto_relevance: Number of crypto-related keywords
          * is_crypto_related: Boolean indicating crypto relevance
          * analysis_timestamp: When analysis was performed
    """
    try:
        analysis = analyze_crypto_sentiment(text, symbol)

        result = {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "symbol": symbol,
            "analysis": analysis,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error analyzing sentiment: {e!s}"})
