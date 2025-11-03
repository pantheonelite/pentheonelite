#!/usr/bin/env python3
"""Create diverse test positions for API testing."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.db.models.council import Council
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.council_metrics_service import CouncilMetricsService
from app.backend.services.unified_trading_service import UnifiedTradingService


async def create_test_positions():
    """Create diverse test positions across multiple symbols and leverage levels."""
    print("=" * 80)
    print("Creating Test Positions")
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

        print(f"\n✅ Using council: {council.name} (ID: {council.id})")

        trading_service = UnifiedTradingService(session, council)
        metrics_service = CouncilMetricsService(session)

        # Test positions to create
        positions_to_create = [
            {
                "symbol": "ETHUSDT",
                "side": "BUY",
                "qty": "0.01",
                "leverage": 10,
                "confidence": 0.80,
            },
            {
                "symbol": "BNBUSDT",
                "side": "SELL",
                "qty": "0.5",
                "leverage": 3,
                "confidence": 0.65,
            },
            {
                "symbol": "SOLUSDT",
                "side": "BUY",
                "qty": "1.0",
                "leverage": 15,
                "confidence": 0.90,
            },
        ]

        created_positions = []

        for pos_config in positions_to_create:
            print(f"\n{'=' * 80}")
            print(f"Creating {pos_config['side']} position for {pos_config['symbol']}")
            print(f"Quantity: {pos_config['qty']}, Leverage: {pos_config['leverage']}x")
            print(f"{'=' * 80}")

            try:
                # Calculate position size in USD (will be adjusted based on wallet)
                position_usd = Decimal("50.00")  # Small position size for testing

                result = await trading_service.aexecute_trade(
                    symbol=pos_config["symbol"],
                    side=pos_config["side"],
                    position_size_usd=position_usd,
                    confidence=Decimal(str(pos_config["confidence"])),
                    leverage=pos_config["leverage"],
                )

                if result["success"]:
                    position_id = result.get("position_id")
                    order_id = result.get("order_id")
                    print(f"✅ Position created: ID {position_id}")
                    print(f"   Order ID: {order_id}")
                    created_positions.append(result)
                else:
                    print(f"❌ Failed: {result.get('error')}")

            except Exception as e:
                print(f"❌ Error creating position: {e}")

        # Update metrics
        print(f"\n{'=' * 80}")
        print("Updating Council Metrics")
        print(f"{'=' * 80}")

        await metrics_service.aupdate_all_metrics(council.id)
        await session.refresh(council)

        print("\n✅ Council Metrics:")
        print(f"   Total Account Value: ${council.total_account_value}")
        print(f"   Available Balance: ${council.available_balance}")
        print(f"   Total Margin Used: ${council.total_margin_used}")
        print(f"   Open Futures: {council.open_futures_count}")
        print(f"   Unrealized Profit: ${council.total_unrealized_profit}")
        print(f"   Average Leverage: {council.average_leverage}x")
        print(f"   Average Confidence: {council.average_confidence}")

        print(f"\n{'=' * 80}")
        print(f"✅ Created {len(created_positions)} test positions")
        print(f"{'=' * 80}")

        return council.id


if __name__ == "__main__":
    council_id = asyncio.run(create_test_positions())
    print(f"\n📝 To test API, use council ID: {council_id}")
    print("\nExample API calls:")
    print(f"  curl http://localhost:8000/api/v1/councils/{council_id}/active-positions")
    print(f"  curl http://localhost:8000/api/v1/councils/{council_id}/metrics")
