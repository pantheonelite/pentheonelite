"""Test script for new LangChain @tool decorated tools.

This demonstrates:
1. Using individual tools directly
2. Using tools with create_agent()
3. Structured output with agents

Run with: uv run python examples/test_langchain_tools.py
"""

import json

from app.backend.src.tools.crypto.aster_tools_langchain import (
    aster_get_history,
    aster_get_multi_price,
    aster_get_price,
)


def test_individual_tools():
    """Test tools directly without agent."""
    print("=" * 80)
    print("Testing Individual Tools")
    print("=" * 80)

    # Test 1: Get single price
    print("\n1. Testing aster_get_price...")
    result = aster_get_price(symbol="BTCUSDT")
    data = json.loads(result)
    print(f"BTC Price: ${data['price']:,.2f}")
    print(f"24h Change: {data['price_change_percent']}%")

    # Test 2: Get multiple prices
    print("\n2. Testing aster_get_multi_price...")
    result = aster_get_multi_price(symbols="BTCUSDT,ETHUSDT,SOLUSDT")
    data = json.loads(result)
    print("Multiple symbols:")
    for symbol_data in data["symbols"]:
        print(f"  {symbol_data['symbol']}: ${symbol_data['price']:,.2f}")

    # Test 3: Get historical data
    print("\n3. Testing aster_get_history...")
    result = aster_get_history(symbol="BTCUSDT", interval="1h", limit=5)
    data = json.loads(result)
    print(f"Retrieved {len(data['candles'])} candles")
    print("Latest candle:")
    latest = data["candles"][-1]
    print(f"  Open: ${latest['open']:,.2f}")
    print(f"  Close: ${latest['close']:,.2f}")
    print(f"  Volume: {latest['volume']:,.2f}")


def test_with_agent():
    """Test tools with LangChain agent."""
    print("\n" + "=" * 80)
    print("Testing with LangChain Agent")
    print("=" * 80)

    try:
        from langchain.agents import create_agent

        # Create agent with tools
        agent = create_agent(
            model="openai:gpt-4o-mini",
            tools=[aster_get_price, aster_get_history, aster_get_multi_price],
            system_prompt=(
                "You are a crypto trading assistant. Use the provided tools to "
                "analyze market data and provide insights. Be concise and clear."
            ),
        )

        # Test query
        print("\nQuery: Compare BTC and ETH current prices")
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Compare the current prices of BTC and ETH",
                    }
                ]
            }
        )

        print("\nAgent Response:")
        print(result)

    except ImportError as e:
        print(f"\nSkipping agent test (missing dependency): {e}")
        print("Install with: uv add langchain langchain-openai")


def test_structured_output():
    """Test agent with structured output."""
    print("\n" + "=" * 80)
    print("Testing Structured Output")
    print("=" * 80)

    try:
        from langchain.agents import create_agent
        from langchain.agents.structured_output import ToolStrategy
        from pydantic import BaseModel, Field

        class MarketAnalysis(BaseModel):
            """Structured market analysis output."""

            symbol: str = Field(description="Trading symbol")
            current_price: float = Field(description="Current price in USD")
            trend: str = Field(description="Market trend: bullish, bearish, or neutral")
            confidence: float = Field(
                description="Confidence in analysis (0-1)", ge=0.0, le=1.0
            )
            reasoning: str = Field(description="Brief explanation")

        # Create agent with structured output
        agent = create_agent(
            model="openai:gpt-4o-mini",
            tools=[aster_get_price, aster_get_history],
            response_format=ToolStrategy(MarketAnalysis),
            system_prompt=(
                "You are a crypto analyst. Analyze the market data and provide "
                "a structured analysis with trend and confidence."
            ),
        )

        print("\nQuery: Analyze BTC market")
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze the BTC market and give me your assessment",
                    }
                ]
            }
        )

        print("\nStructured Analysis:")
        print(f"Symbol: {result.symbol}")
        print(f"Price: ${result.current_price:,.2f}")
        print(f"Trend: {result.trend}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Reasoning: {result.reasoning}")

    except ImportError as e:
        print(f"\nSkipping structured output test (missing dependency): {e}")
        print("Install with: uv add langchain langchain-openai")


if __name__ == "__main__":
    print("\n🚀 LangChain Tools Migration Test\n")

    # Test 1: Individual tools (always works)
    test_individual_tools()

    # Test 2: Agent integration (requires langchain)
    test_with_agent()

    # Test 3: Structured output (requires langchain)
    test_structured_output()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
