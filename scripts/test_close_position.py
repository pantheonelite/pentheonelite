#!/usr/bin/env python3
"""Test closing a position and verifying capital is returned."""

import asyncio

import click

from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.session_manager import session_manager
from app.backend.services.council_trading_service import CouncilTradingService


@click.command()
@click.option("--council-id", type=int, required=True, help="Council ID")
@click.option("--order-id", type=int, required=True, help="Order ID to close")
@click.option("--paper-trading", is_flag=True, help="Paper trading mode")
def main(council_id: int, order_id: int, paper_trading: bool):
    """Test closing a position."""
    asyncio.run(test_close_position(council_id, order_id, paper_trading))


async def test_close_position(council_id: int, order_id: int, paper_trading: bool):
    """Test closing a position and capital return."""
    print("🧪 Testing Position Close")
    print("=" * 60)
    print(f"Council ID: {council_id}")
    print(f"Order ID: {order_id}")
    if paper_trading:
        print("📝 PAPER TRADING MODE")
    print("=" * 60)

    async with session_manager.session(scoped=True) as session:
        repo = CouncilRepository(session)
        trading_service = CouncilTradingService(session, paper_trading=paper_trading)

        # Step 1: Get initial state
        council = await repo.get_council_by_id(council_id)
        initial_capital = float(council.current_capital or council.initial_capital)
        print("\n📊 Initial State:")
        print(f"   Available capital: ${initial_capital:,.2f}")

        # Get order details
        orders = await repo.get_market_orders(council_id, status="open")
        order = next((o for o in orders if o.id == order_id), None)

        if not order:
            print(f"\n❌ Order {order_id} not found")
            return

        position_value = float(order.entry_price * order.quantity)
        print("\n📋 Position to close:")
        print(f"   Order ID: {order.id}")
        print(f"   Symbol: {order.symbol}")
        print(f"   Side: {order.side}")
        print(f"   Quantity: {float(order.quantity)}")
        print(f"   Entry price: ${float(order.entry_price):,.4f}")
        print(f"   Position value: ${position_value:,.2f}")

        # Step 2: Close position
        print("\n💰 Closing position...")
        result = await trading_service.aclose_position(council_id, order_id)

        if not result["success"]:
            print(f"❌ Failed to close: {result['error']}")
            return

        closed_order = result["order"]
        pnl = float(closed_order.pnl) if closed_order.pnl else 0

        print("✅ Position closed!")
        print(f"   Exit price: ${float(closed_order.exit_price):,.4f}")
        print(f"   PnL: ${pnl:,.2f}")
        print(f"   PnL %: {float(closed_order.pnl_percentage or 0):.2f}%")

        # Step 3: Verify capital update
        await session.refresh(council)
        final_capital = float(council.current_capital or council.initial_capital)
        capital_returned = position_value + pnl
        expected_capital = initial_capital + capital_returned

        print("\n📊 Final State:")
        print(f"   Capital returned: ${capital_returned:,.2f}")
        print(f"   Expected capital: ${expected_capital:,.2f}")
        print(f"   Actual capital: ${final_capital:,.2f}")

        if abs(final_capital - expected_capital) < 0.01:
            print("   ✅ Capital tracking CORRECT!")
        else:
            print("   ❌ Capital tracking ERROR!")
            print(f"   Difference: ${abs(final_capital - expected_capital):,.2f}")

        # Step 4: Show all positions
        open_orders = await repo.get_market_orders(council_id, status="open")
        print(f"\n📊 Remaining open positions: {len(open_orders)}")

        if open_orders:
            total_open_value = sum(
                float(o.entry_price * o.quantity) for o in open_orders
            )
            print(f"   Total open value: ${total_open_value:,.2f}")
            for o in open_orders:
                print(
                    f"     - {o.side.upper()} {float(o.quantity)} {o.symbol} @ ${float(o.entry_price):,.4f}"
                )

        print("\n" + "=" * 60)
        print("✅ Test completed!")
        print("=" * 60)


if __name__ == "__main__":
    main()
