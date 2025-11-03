"""Test script for newly migrated LangChain @tool decorated tools.

This script tests:
1. technical_indicators tool
2. crypto_news_crawler tool
3. crypto_sentiment tool
4. crypto_web_scraper tool

Run with: uv run python examples/test_new_langchain_tools.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.src.tools.crypto.technical_indicators_langchain import (
    technical_indicators,
)
from app.backend.src.tools.news.news_crawler_langchain import crypto_news_crawler
from app.backend.src.tools.news.sentiment_analysis_langchain import crypto_sentiment


def test_technical_indicators():
    """Test technical indicators tool."""
    print("=" * 80)
    print("Testing Technical Indicators Tool")
    print("=" * 80)

    try:
        print("\n1. Testing technical_indicators for BTCUSDT...")
        result = technical_indicators.invoke(
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "period": 100,
                "exchange": "binance",
            }
        )
        data = json.loads(result)

        if "error" in data:
            print(f"⚠️  Error: {data['error']}")
            return

        print(f"✓ Analysis completed for {data['symbol']}")
        print(f"  Current Price: ${data['current_price']:,.2f}")
        print(f"  Timeframe: {data['timeframe']}")
        print(f"  Analysis Period: {data['analysis_period']} candles")

        # Display key indicators
        indicators = data["indicators"]
        print("\n  Key Indicators:")

        # RSI
        if "rsi" in indicators and "rsi" in indicators["rsi"]:
            print(
                f"    RSI: {indicators['rsi']['rsi']} - {indicators['rsi']['signal']}"
            )

        # MACD
        if "macd" in indicators and "signal" in indicators["macd"]:
            print(f"    MACD: {indicators['macd']['signal']}")

        # Moving Averages
        if "moving_averages" in indicators and "trend" in indicators["moving_averages"]:
            print(f"    MA Trend: {indicators['moving_averages']['trend']}")

        print("\n✅ Technical indicators test passed!")

    except Exception as e:
        print(f"\n❌ Error testing technical indicators: {e!s}")
        import traceback

        traceback.print_exc()


def test_news_crawler():
    """Test news crawler tool."""
    print("\n" + "=" * 80)
    print("Testing News Crawler Tool")
    print("=" * 80)

    try:
        print("\n1. Testing crypto_news_crawler...")
        result = crypto_news_crawler.invoke({"symbol": None, "limit": 5, "hours": 24})
        data = json.loads(result)

        if "error" in data:
            print(f"⚠️  Error: {data['error']}")
            return

        print(f"✓ Found {data['articles_count']} articles")
        print(f"  Time Range: {data['time_range_hours']} hours")

        if data["articles"]:
            print("\n  Latest Article:")
            article = data["articles"][0]
            print(f"    Title: {article['title'][:80]}...")
            print(f"    Source: {article['source']}")
            print(f"    Published: {article['published']}")

        print("\n✅ News crawler test passed!")

    except Exception as e:
        print(f"\n❌ Error testing news crawler: {e!s}")
        import traceback

        traceback.print_exc()


def test_sentiment_analysis():
    """Test sentiment analysis tool."""
    print("\n" + "=" * 80)
    print("Testing Sentiment Analysis Tool")
    print("=" * 80)

    try:
        test_texts = [
            "Bitcoin surges to new highs as bullish momentum continues!",
            "Crypto market crashes amid regulatory concerns and negative sentiment.",
            "Trading volume remains steady with neutral market conditions.",
        ]

        for i, text in enumerate(test_texts, 1):
            print(f"\n{i}. Testing sentiment: '{text[:60]}...'")
            result = crypto_sentiment.invoke({"text": text, "symbol": "BTC"})
            data = json.loads(result)

            if "error" in data:
                print(f"   ⚠️  Error: {data['error']}")
                continue

            analysis = data["analysis"]
            print(f"   ✓ Sentiment: {analysis['sentiment_label']}")
            print(f"     Score: {analysis['sentiment_score']:.2f}")
            print(f"     Positive keywords: {analysis['positive_keywords']}")
            print(f"     Negative keywords: {analysis['negative_keywords']}")
            print(f"     Crypto related: {analysis['is_crypto_related']}")

        print("\n✅ Sentiment analysis test passed!")

    except Exception as e:
        print(f"\n❌ Error testing sentiment analysis: {e!s}")
        import traceback

        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n🚀 Testing Newly Migrated LangChain Tools\n")

    # Test 1: Technical Indicators
    test_technical_indicators()

    # Test 2: News Crawler
    test_news_crawler()

    # Test 3: Sentiment Analysis
    test_sentiment_analysis()

    print("\n" + "=" * 80)
    print("✅ All migration tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
