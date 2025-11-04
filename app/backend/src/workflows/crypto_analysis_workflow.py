"""LangGraph workflow for crypto analysis using simplified tools without external APIs."""

import asyncio
import json
from datetime import datetime
from typing import Any, TypedDict

import structlog
from app.backend.src.tools.crypto.analysis_langchain import (
    crypto_sentiment_analysis,
    price_trend_analysis,
    volume_analysis,
)
from app.backend.src.tools.crypto.aster_tools_langchain import (
    aster_get_history,
    aster_get_price,
)
from app.backend.src.tools.news import crypto_news_crawler, crypto_sentiment
from langgraph.graph import END, StateGraph

logger = structlog.get_logger(__name__)


class CryptoAnalysisState(TypedDict):
    """State for crypto analysis workflow."""

    symbol: str
    analysis_type: str
    price_data: dict[str, Any] | None
    historical_data: dict[str, Any] | None
    news_data: list[dict[str, Any]] | None
    trend_analysis: dict[str, Any] | None
    volume_analysis: dict[str, Any] | None
    sentiment_analysis: dict[str, Any] | None
    final_analysis: str | None
    error: str | None


def fetch_crypto_price(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Fetch real-time crypto price data."""
    try:
        symbol = state["symbol"]
        result = aster_get_price(symbol, "aster")
        price_data = json.loads(result)
        return {**state, "price_data": price_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Error fetching price data: {e!s}"}


def fetch_historical_data(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Fetch historical crypto data."""
    try:
        symbol = state["symbol"]
        result = aster_get_history(symbol, "1h", 24, "aster")
        historical_data = json.loads(result)
        return {**state, "historical_data": historical_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Error fetching historical data: {e!s}"}


def fetch_crypto_news(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Fetch crypto news."""
    try:
        symbol = state["symbol"]
        result = crypto_news_crawler(symbol, 5, 24)
        news_data = json.loads(result)

        return {**state, "news_data": news_data.get("articles", []), "error": None}
    except Exception as e:
        return {**state, "error": f"Error fetching news: {e!s}"}


def analyze_price_trend(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Analyze price trends."""
    try:
        symbol = state["symbol"]
        result = price_trend_analysis(symbol, "1h", 24, "aster")
        trend_analysis = json.loads(result)
        return {**state, "trend_analysis": trend_analysis, "error": None}
    except Exception as e:
        return {**state, "error": f"Error analyzing price trend: {e!s}"}


def analyze_volume(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Analyze trading volume."""
    try:
        symbol = state["symbol"]
        result = volume_analysis(symbol, "1h", 24, "aster")
        volume_analysis_data = json.loads(result)
        return {**state, "volume_analysis": volume_analysis_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Error analyzing volume: {e!s}"}


def analyze_sentiment(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Analyze crypto sentiment."""
    try:
        symbol = state["symbol"]
        result = crypto_sentiment_analysis(symbol, "1h", 24, "aster")
        sentiment_analysis_data = json.loads(result)
        return {**state, "sentiment_analysis": sentiment_analysis_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Error analyzing sentiment: {e!s}"}


def generate_final_analysis(state: CryptoAnalysisState) -> CryptoAnalysisState:
    """Generate final comprehensive analysis."""
    try:
        symbol = state["symbol"]
        analysis_type = state["analysis_type"]

        # Compile all analysis results
        analysis_summary = {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "price_data": state.get("price_data"),
            "trend_analysis": state.get("trend_analysis"),
            "volume_analysis": state.get("volume_analysis"),
            "sentiment_analysis": state.get("sentiment_analysis"),
            "news_count": len(state.get("news_data", [])),
        }

        # Generate summary text
        # Extract data safely
        price_data = analysis_summary.get("price_data", {})
        trend_data = analysis_summary.get("trend_analysis", {})
        volume_data = analysis_summary.get("volume_analysis", {})
        sentiment_data = analysis_summary.get("sentiment_analysis", {})

        current_price = price_data.get("price", "N/A") if price_data else "N/A"
        price_change_24h = price_data.get("change_percent_24h", "N/A") if price_data else "N/A"
        trend = trend_data.get("trend", "N/A") if trend_data else "N/A"
        trend_change = trend_data.get("price_change_percent", "N/A") if trend_data else "N/A"
        volume_trend = volume_data.get("volume_trend", "N/A") if volume_data else "N/A"
        volume_ratio = volume_data.get("volume_metrics", {}).get("volume_ratio", "N/A") if volume_data else "N/A"
        sentiment_label = sentiment_data.get("sentiment_label", "N/A") if sentiment_data else "N/A"
        sentiment_score = sentiment_data.get("sentiment_score", "N/A") if sentiment_data else "N/A"

        summary_text = f"""
Crypto Analysis Report for {symbol}

Price Data:
- Current Price: ${current_price}
- 24h Change: {price_change_24h}%

Trend Analysis:
- Trend: {trend}
- Price Change: {trend_change}%

Volume Analysis:
- Volume Trend: {volume_trend}
- Volume Ratio: {volume_ratio}

Sentiment Analysis:
- Sentiment: {sentiment_label}
- Sentiment Score: {sentiment_score}

News Coverage:
- Articles Found: {analysis_summary["news_count"]}

Analysis completed at: {analysis_summary["timestamp"]}
        """.strip()

        return {**state, "final_analysis": summary_text, "error": None}
    except Exception as e:
        return {**state, "error": f"Error generating final analysis: {e!s}"}


def should_continue_analysis(state: CryptoAnalysisState) -> str:
    """Determine if analysis should continue based on errors."""
    if state.get("error"):
        return "end"
    return "continue"


def create_crypto_analysis_workflow():
    """Create the crypto analysis workflow."""
    workflow = StateGraph(CryptoAnalysisState)

    # Add nodes
    workflow.add_node("fetch_price", fetch_crypto_price)
    workflow.add_node("fetch_history", fetch_historical_data)
    workflow.add_node("fetch_news", fetch_crypto_news)
    workflow.add_node("analyze_trend", analyze_price_trend)
    workflow.add_node("analyze_volume", analyze_volume)
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("generate_analysis", generate_final_analysis)

    # Define the workflow
    workflow.set_entry_point("fetch_price")

    # Parallel execution of data fetching
    workflow.add_edge("fetch_price", "fetch_history")
    workflow.add_edge("fetch_history", "fetch_news")

    # Parallel analysis after data fetching
    workflow.add_edge("fetch_news", "analyze_trend")
    workflow.add_edge("analyze_trend", "analyze_volume")
    workflow.add_edge("analyze_volume", "analyze_sentiment")

    # Final analysis
    workflow.add_edge("analyze_sentiment", "generate_analysis")
    workflow.add_edge("generate_analysis", END)

    return workflow.compile()


def create_news_sentiment_workflow():
    """Create a workflow focused on news sentiment analysis."""

    class NewsSentimentState(TypedDict):
        symbol: str
        news_data: list[dict[str, Any]] | None
        sentiment_results: list[dict[str, Any]] | None
        final_sentiment: str | None
        error: str | None

    def fetch_news_only(state: NewsSentimentState) -> NewsSentimentState:
        """Fetch news for sentiment analysis."""
        try:
            symbol = state["symbol"]
            result = crypto_news_crawler(symbol, 10, 48)  # More news, longer timeframe
            news_data = json.loads(result)

            return {**state, "news_data": news_data.get("articles", []), "error": None}
        except Exception as e:
            return {**state, "error": f"Error fetching news: {e!s}"}

    def analyze_news_sentiment(state: NewsSentimentState) -> NewsSentimentState:
        """Analyze sentiment of news articles."""
        try:
            sentiment_results = []

            for article in state.get("news_data", []):
                text = f"{article.get('title', '')} {article.get('summary', '')}"
                result = crypto_sentiment(text, state["symbol"])
                sentiment_data = json.loads(result)
                sentiment_results.append({"article": article, "sentiment": sentiment_data})

            return {**state, "sentiment_results": sentiment_results, "error": None}
        except Exception as e:
            return {**state, "error": f"Error analyzing sentiment: {e!s}"}

    def generate_sentiment_summary(state: NewsSentimentState) -> NewsSentimentState:
        """Generate sentiment summary."""
        try:
            sentiment_results = state.get("sentiment_results", [])

            if not sentiment_results:
                return {
                    **state,
                    "final_sentiment": "No news articles found for sentiment analysis.",
                    "error": None,
                }

            # Calculate overall sentiment
            sentiment_scores = [result["sentiment"]["analysis"]["sentiment_score"] for result in sentiment_results]

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

            # Count sentiment labels
            sentiment_labels = [result["sentiment"]["analysis"]["sentiment_label"] for result in sentiment_results]

            positive_count = sentiment_labels.count("positive")
            negative_count = sentiment_labels.count("negative")
            neutral_count = sentiment_labels.count("neutral")

            summary = f"""
News Sentiment Analysis for {state["symbol"]}

Overall Sentiment Score: {avg_sentiment:.2f}
Articles Analyzed: {len(sentiment_results)}

Sentiment Distribution:
- Positive: {positive_count} articles
- Negative: {negative_count} articles
- Neutral: {neutral_count} articles

Average Sentiment: {"Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"}

Analysis completed at: {datetime.now().isoformat()}
            """.strip()

            return {**state, "final_sentiment": summary, "error": None}
        except Exception as e:
            return {**state, "error": f"Error generating sentiment summary: {e!s}"}

    # Create workflow
    workflow = StateGraph(NewsSentimentState)

    workflow.add_node("fetch_news", fetch_news_only)
    workflow.add_node("analyze_sentiment", analyze_news_sentiment)
    workflow.add_node("generate_summary", generate_sentiment_summary)

    workflow.set_entry_point("fetch_news")
    workflow.add_edge("fetch_news", "analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "generate_summary")
    workflow.add_edge("generate_summary", END)

    return workflow.compile()


# Example usage functions
async def run_crypto_analysis(symbol: str, analysis_type: str = "comprehensive") -> dict[str, Any]:
    """Run comprehensive crypto analysis."""
    workflow = create_crypto_analysis_workflow()

    initial_state = {
        "symbol": symbol,
        "analysis_type": analysis_type,
        "price_data": None,
        "historical_data": None,
        "news_data": None,
        "trend_analysis": None,
        "volume_analysis": None,
        "sentiment_analysis": None,
        "final_analysis": None,
        "error": None,
    }

    return await workflow.ainvoke(initial_state)


async def run_news_sentiment_analysis(symbol: str) -> dict[str, Any]:
    """Run news sentiment analysis."""
    workflow = create_news_sentiment_workflow()

    initial_state = {
        "symbol": symbol,
        "news_data": None,
        "sentiment_results": None,
        "final_sentiment": None,
        "error": None,
    }

    return await workflow.ainvoke(initial_state)


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        # Run crypto analysis
        logger.info("Running crypto analysis for BTC/USDT...")
        result = await run_crypto_analysis("BTC/USDT")
        logger.info("Analysis Result:")
        logger.info(result.get("final_analysis", "No analysis generated"))

        logger.info("\n%s\n", "=" * 50)

        # Run news sentiment analysis
        logger.info("Running news sentiment analysis for BTC...")
        sentiment_result = await run_news_sentiment_analysis("BTC")
        logger.info("Sentiment Analysis Result:")
        logger.info(sentiment_result.get("final_sentiment", "No sentiment analysis generated"))

    asyncio.run(main())
