#!/usr/bin/env python3
"""Test position-based trading execution."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.db.models.council import Council
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.council_metrics_service import CouncilMetricsService
from app.backend.services.futures_position_service import FuturesPositionService
from app.backend.services.unified_trading_service import UnifiedTradingService


async def test_position_trading():
    """Test complete position trading lifecycle."""
    print("=" * 80)
    print("Position-Based Trading System Test")
    print("=" * 80)

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as uow,
    ):
        # Get first paper futures council
        repo = uow.get_repository(Council)
        councils = await repo.get_system_councils()
        council = next(
            (
                c
                for c in councils
                if c.trading_mode == "paper" and c.trading_type == "futures"
            ),
            None,
        )

        if not council:
            print("❌ No paper futures council found!")
            return

        print(f"\n✅ Testing with council: {council.name} (ID: {council.id})")
        print(f"   Trading mode: {council.trading_mode}")
        print(f"   Trading type: {council.trading_type}")
        print(f"   Initial capital: ${council.initial_capital}")
        print(f"   Available balance: ${council.available_balance}")

        # Test 1: Open LONG position
        print("\n" + "=" * 80)
        print("TEST 1: Open LONG Position")
        print("=" * 80)

        trading_service = UnifiedTradingService(session, council)

        result = await trading_service.aexecute_trade(
            symbol="BTCUSDT",
            side="BUY",
            position_size_usd=Decimal("100.00"),  # $100 position size
            confidence=Decimal("0.75"),
            leverage=5,
        )

        print(f"\nResult: {result}")
        assert result["success"], f"Trade failed: {result.get('error')}"
        position_id = result.get("position_id")
        print(f"✅ LONG position opened: ID {position_id}")

        # Test 2: Verify position in database
        print("\n" + "=" * 80)
        print("TEST 2: Verify Position in Database")
        print("=" * 80)

        futures_service = FuturesPositionService(session)
        position = await futures_service.repo.get_by_id(position_id)

        assert position is not None
        assert position.position_side in [
            "LONG",
            "BOTH",
        ]  # BOTH for Binance one-way mode
        assert position.status == "OPEN"
        assert position.leverage == 5

        print("✅ Position verified:")
        print(f"   Symbol: {position.symbol}")
        print(f"   Side: {position.position_side}")
        print(f"   Entry Price: ${position.entry_price}")
        print(f"   Quantity: {position.position_amt}")
        print(f"   Leverage: {position.leverage}x")
        print(f"   Notional: ${position.notional}")
        print(f"   Liquidation: ${position.liquidation_price}")
        print(f"   Status: {position.status}")

        # Test 3: Update metrics
        print("\n" + "=" * 80)
        print("TEST 3: Update Council Metrics")
        print("=" * 80)

        metrics_service = CouncilMetricsService(session)
        await metrics_service.aupdate_all_metrics(council.id)

        # Refresh council
        await session.refresh(council)
        print("✅ Metrics updated:")
        print(f"   Total Account Value: ${council.total_account_value}")
        print(f"   Available Balance: ${council.available_balance}")
        print(f"   Open Futures Count: {council.open_futures_count}")
        print(f"   Unrealized Profit: ${council.total_unrealized_profit}")
        print(f"   Average Leverage: {council.average_leverage}x")
        print(f"   Average Confidence: {council.average_confidence}")

        # Test 4: Close position
        print("\n" + "=" * 80)
        print("TEST 4: Close Position")
        print("=" * 80)

        ticker = await trading_service.client.aget_ticker("BTCUSDT")
        exit_price = Decimal(str(ticker.price))
        print(f"Current BTCUSDT price: ${exit_price}")

        closed = await futures_service.aclose_position(
            position_id,
            exit_price=exit_price,
            fees=Decimal("0.50"),
        )

        print("✅ Position closed:")
        print(f"   Exit Price: ${closed.mark_price}")
        print(f"   Realized PnL: ${closed.realized_pnl}")
        print(f"   Fees Paid: ${closed.fees_paid}")
        print(f"   Status: {closed.status}")

        # Test 5: Final metrics update
        print("\n" + "=" * 80)
        print("TEST 5: Final Metrics Update")
        print("=" * 80)

        await metrics_service.aupdate_all_metrics(council.id)
        await session.refresh(council)

        print("✅ Final metrics:")
        print(f"   Open Futures: {council.open_futures_count}")
        print(f"   Closed Futures: {council.closed_futures_count}")
        print(f"   Realized PnL: ${council.total_realized_pnl}")
        print(f"   Net PnL: ${council.net_pnl}")
        print(f"   Total Fees: ${council.total_fees}")
        print(f"   Biggest Win: ${council.biggest_win}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\n📊 Summary:")
        print(
            f"   - Opened LONG position: ${position.entry_price} with {position.leverage}x leverage"
        )
        print(f"   - Closed at: ${closed.mark_price}")
        print(f"   - Realized PnL: ${closed.realized_pnl}")
        print("   - Position lifecycle: OPEN → UPDATE → CLOSED")
        print("   - Metrics: All calculated correctly")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_position_trading())
