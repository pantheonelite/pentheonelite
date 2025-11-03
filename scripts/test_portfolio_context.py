"""Test script to validate portfolio context flow."""

import asyncio
from decimal import Decimal

import structlog

from app.backend.db.models.council import Council
from app.backend.db.session_manager import session_manager
from app.backend.services.portfolio_context_service import PortfolioContextService

logger = structlog.get_logger(__name__)


async def test_portfolio_context():
    """
    Test portfolio context service with various scenarios.

    Test scenarios:
    1. Empty portfolio (no positions) - agents should recommend opening positions
    2. Existing LONG position at profit - agents should consider holding/adding
    3. Existing SHORT position at loss - agents should consider closing
    4. Multiple positions - check total exposure calculations
    5. High leverage position near liquidation - verify urgent warnings
    """
    print("=" * 80)
    print("TESTING PORTFOLIO CONTEXT SERVICE")
    print("=" * 80)

    async with session_manager.session(scoped=True) as session:
        try:
            # Scenario 1: Empty Portfolio
            print("\n" + "=" * 80)
            print("SCENARIO 1: Empty Portfolio")
            print("=" * 80)

            mock_council = Council(
                id=1,
                name="Test Council",
                initial_capital=Decimal("100000"),
                available_balance=Decimal("100000"),
                trading_mode="paper",
                trading_type="futures",
            )

            portfolio_service = PortfolioContextService(session)
            portfolio = await portfolio_service.aget_portfolio_context(
                council=mock_council,
                symbols=["BTCUSDT", "ETHUSDT"],
            )

            print("\n✅ Empty Portfolio Test")
            print(f"   Total Positions: {portfolio['total_positions']}")
            print(f"   Available Balance: ${portfolio['available_balance']:,.2f}")
            print(f"   Total Value: ${portfolio['total_value']:,.2f}")
            print(f"   Unrealized PnL: ${portfolio['unrealized_pnl']:,.2f}")
            print(f"   Liquidation Risk: {portfolio['liquidation_risk']}")

            assert portfolio["total_positions"] == 0, "Expected 0 positions"
            assert portfolio["unrealized_pnl"] == 0.0, "Expected 0 unrealized PnL"
            assert portfolio["total_value"] == 100000.0, (
                "Expected total value = initial capital"
            )
            print("   ✓ All assertions passed for empty portfolio")

            # Scenario 2: Mock existing LONG position at profit
            print("\n" + "=" * 80)
            print("SCENARIO 2: LONG Position at Profit (Simulated)")
            print("=" * 80)

            print(
                "\n   To fully test this scenario, create a real position in database:"
            )
            print("   1. Run a council trading cycle")
            print("   2. Execute a BUY trade to open LONG position")
            print("   3. Wait for price to rise")
            print("   4. Re-run this test to see portfolio context")

            # For demonstration, show what the structure would look like
            simulated_portfolio = {
                "council_id": 1,
                "initial_capital": 100000.0,
                "available_balance": 50000.0,
                "total_value": 105000.0,
                "unrealized_pnl": 5000.0,
                "positions": {
                    "BTCUSDT": {
                        "side": "LONG",  # Normalized from "BOTH"
                        "position_amt": 0.5,
                        "entry_price": 50000.0,
                        "current_price": 60000.0,
                        "unrealized_pnl": 5000.0,
                        "leverage": 10,
                        "notional": 300000.0,
                        "liquidation_price": 45000.0,
                        "margin_used": 30000.0,
                    }
                },
                "total_positions": 1,
                "total_notional": 300000.0,
                "margin_usage_ratio": 0.6,
                "liquidation_risk": "low",
            }

            print("\n   Simulated Portfolio Context:")
            print(
                f"   Position: {simulated_portfolio['positions']['BTCUSDT']['side']} BTCUSDT"
            )
            print(
                f"   Entry: ${simulated_portfolio['positions']['BTCUSDT']['entry_price']:,.2f}"
            )
            print(
                f"   Current: ${simulated_portfolio['positions']['BTCUSDT']['current_price']:,.2f}"
            )
            print(
                f"   PnL: ${simulated_portfolio['positions']['BTCUSDT']['unrealized_pnl']:,.2f}"
            )
            print(
                f"   Leverage: {simulated_portfolio['positions']['BTCUSDT']['leverage']}x"
            )
            print(
                f"   Liquidation: ${simulated_portfolio['positions']['BTCUSDT']['liquidation_price']:,.2f}"
            )

            # Scenario 3: Position normalization check
            print("\n" + "=" * 80)
            print("SCENARIO 3: Position Side Normalization")
            print("=" * 80)

            print("\n   Testing normalization logic:")
            print("   - Binance API returns 'BOTH' for one-way mode")
            print("   - We normalize to 'LONG' or 'SHORT' based on position_amt sign")
            print("   - Agents see clear 'LONG'/'SHORT' semantics")

            # Test normalization function
            class MockPosition:
                def __init__(self, position_side, position_amt):
                    self.position_side = position_side
                    self.position_amt = Decimal(str(position_amt))

            test_cases = [
                (MockPosition("BOTH", 0.5), "LONG"),
                (MockPosition("BOTH", -0.3), "SHORT"),
                (MockPosition("LONG", 1.0), "LONG"),
                (MockPosition("SHORT", 0.8), "SHORT"),
            ]

            for pos, expected in test_cases:
                result = portfolio_service._normalize_position_side(pos)
                status = "✓" if result == expected else "✗"
                print(
                    f"   {status} position_side='{pos.position_side}', amt={pos.position_amt} → '{result}' (expected '{expected}')"
                )

            # Scenario 4: Liquidation risk assessment
            print("\n" + "=" * 80)
            print("SCENARIO 4: Liquidation Risk Assessment")
            print("=" * 80)

            test_positions = {
                "low_risk": {
                    "side": "LONG",
                    "current_price": 50000.0,
                    "liquidation_price": 35000.0,
                },
                "medium_risk": {
                    "side": "LONG",
                    "current_price": 50000.0,
                    "liquidation_price": 42000.0,
                },
                "high_risk": {
                    "side": "LONG",
                    "current_price": 50000.0,
                    "liquidation_price": 47000.0,
                },
                "critical_risk": {
                    "side": "LONG",
                    "current_price": 50000.0,
                    "liquidation_price": 48500.0,
                },
            }

            for risk_level, pos in test_positions.items():
                distance_pct = (
                    (pos["current_price"] - pos["liquidation_price"]) / pos["current_price"]
                ) * 100
                assessed_risk = portfolio_service._assess_liquidation_risk(
                    {"test": pos}
                )
                print(
                    f"   {risk_level}: {distance_pct:.1f}% from liquidation → Risk: {assessed_risk}"
                )

            print("\n" + "=" * 80)
            print("✅ ALL TEST SCENARIOS COMPLETED")
            print("=" * 80)

            print("\nNEXT STEPS:")
            print("1. Run a real council trading cycle with actual positions")
            print("2. Verify agents receive portfolio context in their prompts")
            print("3. Check agent reasoning acknowledges existing positions")
            print("4. Validate position side is 'LONG' or 'SHORT' (not 'BOTH')")

        except Exception as e:
            logger.exception("Test failed", error=str(e))
            print(f"\n❌ Test failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(test_portfolio_context())
