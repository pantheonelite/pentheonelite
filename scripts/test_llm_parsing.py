"""Test LLM response parsing with mocked council cycle data."""

from datetime import datetime

import structlog

from app.backend.src.agents.crypto_risk_manager import CryptoRiskManagerAgent
from app.backend.src.agents.portfolio_manager import CryptoPortfolioManagerAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
)

logger = structlog.get_logger(__name__)


def create_mock_state() -> CryptoAgentState:
    """
    Create mock state simulating a council cycle.

    Returns
    -------
    CryptoAgentState
        Mock state with portfolio, market data, and model config
    """
    return {
        "messages": [],
        "symbols": ["BTCUSDT"],
        "timeframe": "1h",
        "start_date": datetime(2025, 10, 2),
        "end_date": datetime(2025, 11, 1),
        "model_name": "deepseek/deepseek-chat-v3.1:free",  # Test with deepseek
        "model_provider": "openrouter",
        # Market data
        "price_data": {
            "BTCUSDT": {
                "price": 109705.2,
                "volume": 970.844,
                "change_24h": 57.2,
                "change_percent_24h": 0.052,
            }
        },
        "volume_data": {"BTCUSDT": {"current_volume": 970.844, "avg_volume": 5698.22}},
        "news_data": {"BTCUSDT": {"news_count": 5, "headlines": []}},
        "social_data": {},
        # Analysis signals (mock)
        "technical_signals": {
            "crypto_technical": {
                "BTCUSDT": {
                    "signal": "LONG",
                    "confidence": 0.65,
                    "reasoning": "Bullish technical setup",
                }
            }
        },
        "sentiment_signals": {
            "crypto_sentiment": {
                "BTCUSDT": {
                    "signal": "HOLD",
                    "confidence": 0.55,
                    "reasoning": "Mixed sentiment",
                }
            }
        },
        "persona_signals": {},
        "persona_consensus": {},
        "risk_assessments": {},
        # Trading decisions
        "trading_decisions": {},
        "portfolio_allocations": {},
        # Workflow metadata
        "execution_timestamp": datetime.now(),
        "current_node": "risk_assessment",
        "progress_percentage": 50.0,
        "error_messages": [],
        # Agent reasoning
        "agent_reasoning": {},
        "confidence_scores": {},
        # Portfolio (EMPTY - testing new position scenario)
        "data": {
            "portfolio": {
                "cash": 100000.0,
                "total_value": 100000.0,
                "unrealized_pnl": 0.0,
                "positions": {},  # No existing positions
            }
        },
        "portfolio": {},
        "total_value": 100000.0,
    }


def test_risk_manager_parsing():
    """Test Risk Manager LLM response parsing."""
    print("\n" + "=" * 80)
    print("TEST 1: Risk Manager Agent - LLM Parsing")
    print("=" * 80)

    try:
        agent = CryptoRiskManagerAgent()
        mock_state = create_mock_state()

        print("\n📊 Mock State:")
        print(f"   Symbol: {mock_state['symbols'][0]}")
        print(f"   Model: {mock_state['model_name']}")
        print(
            f"   Portfolio: Empty (${mock_state['data']['portfolio']['cash']:,.0f} cash)"
        )

        print("\n🤖 Running Risk Manager analysis...")
        result = agent.analyze_symbol("BTCUSDT", mock_state)

        print("\n✅ Result:")
        print(f"   Signal: {result.get('signal')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Portfolio Risk: {result.get('portfolio_risk')}")
        print(f"   Position Risk: {result.get('position_risk')}")
        print(f"   Reasoning: {result.get('reasoning', '')[:100]}...")

        # Check for validation errors
        if result.get("error"):
            print(f"\n❌ Error: {result['error']}")
            return False

        # Verify field types
        errors = []
        if not isinstance(result.get("signal"), str):
            errors.append(f"signal is {type(result.get('signal'))}, expected str")
        if result.get("portfolio_risk") is not None and not isinstance(
            result.get("portfolio_risk"), (int, float)
        ):
            errors.append(
                f"portfolio_risk is {type(result.get('portfolio_risk'))}, expected float"
            )

        if errors:
            print("\n❌ Type Validation Errors:")
            for err in errors:
                print(f"   - {err}")
            return False

        print("\n✅ Risk Manager parsing: SUCCESS")
        return True

    except Exception as e:
        logger.exception("Risk Manager test failed")
        print(f"\n❌ FAILED: {e}")
        return False


def test_portfolio_manager_parsing():
    """Test Portfolio Manager LLM response parsing."""
    print("\n" + "=" * 80)
    print("TEST 2: Portfolio Manager Agent - LLM Parsing")
    print("=" * 80)

    try:
        agent = CryptoPortfolioManagerAgent()
        mock_state = create_mock_state()

        # Add analyst and risk signals to state
        mock_state["technical_signals"] = {
            "crypto_technical": {
                "BTCUSDT": {
                    "signal": "LONG",
                    "confidence": 0.7,
                    "reasoning": "Strong bullish setup",
                }
            }
        }
        mock_state["risk_assessments"] = {
            "crypto_risk_manager": {
                "BTCUSDT": {
                    "signal": "buy",
                    "confidence": 0.6,
                    "reasoning": "Acceptable risk",
                }
            }
        }

        print("\n📊 Mock State:")
        print(f"   Symbol: {mock_state['symbols'][0]}")
        print(f"   Model: {mock_state['model_name']}")
        print("   Technical Signal: LONG (0.70)")
        print("   Risk Signal: buy (0.60)")

        print("\n🤖 Running Portfolio Manager analysis...")
        result = agent.run_agent(mock_state)

        decisions = result.get("trading_decisions", {})
        print("\n✅ Result:")
        print(f"   Decisions: {len(decisions)}")

        if "BTCUSDT" in decisions:
            decision = decisions["BTCUSDT"]
            print(f"   Action: {decision.get('action')}")
            print(f"   Quantity: {decision.get('quantity')}")
            print(f"   Confidence: {decision.get('confidence')}")
            print(f"   Direction: {decision.get('direction')}")

            # Check for validation errors
            if not isinstance(decision.get("action"), str):
                print(f"\n❌ action is {type(decision.get('action'))}, expected str")
                return False
            if not isinstance(decision.get("quantity"), (int, float)):
                print(
                    f"\n❌ quantity is {type(decision.get('quantity'))}, expected float"
                )
                return False

        print("\n✅ Portfolio Manager parsing: SUCCESS")
        return True

    except Exception as e:
        logger.exception("Portfolio Manager test failed")
        print(f"\n❌ FAILED: {e}")
        return False


def main():
    """Run all LLM parsing tests."""
    print("\n" + "=" * 80)
    print("LLM RESPONSE PARSING TEST SUITE")
    print("Testing with mocked council cycle data")
    print("=" * 80)

    results = []

    # Test 1: Risk Manager
    results.append(("Risk Manager", test_risk_manager_parsing()))

    # Test 2: Portfolio Manager
    results.append(("Portfolio Manager", test_portfolio_manager_parsing()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - LLM parsing is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - LLM parsing needs fixes")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
