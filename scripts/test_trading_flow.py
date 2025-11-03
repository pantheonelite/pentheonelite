#!/usr/bin/env python3
"""Test trading flow with real order creation and database logging."""

import asyncio

import click

from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.council_trading_service import CouncilTradingService


@click.command()
@click.option("--council-id", type=int, required=True, help="Council ID")
@click.option(
    "--symbol",
    required=True,
    help="Trading symbol (e.g., BTCUSDT, ETHUSDT)",
)
@click.option(
    "--decision",
    type=click.Choice(["BUY", "SELL", "HOLD"]),
    default="BUY",
    help="Trading decision",
)
@click.option(
    "--paper-trading", is_flag=True, help="Paper trading mode (simulated orders)"
)
def main(council_id: int, symbol: str, decision: str, paper_trading: bool):
    """Test order execution and database logging."""
    asyncio.run(test_trading_flow(council_id, symbol, decision, paper_trading))


async def test_trading_flow(
    council_id: int, symbol: str, decision: str, paper_trading: bool
):
    """Test order execution and database logging."""
    print("🧪 Testing Trading Flow")
    print("=" * 60)
    print(f"Council ID: {council_id}")
    print(f"Symbol: {symbol}")
    print(f"Decision: {decision}")

    if paper_trading:
        print("📝 PAPER TRADING MODE: Orders will be simulated (no real execution)")
    else:
        print("🚨 LIVE TRADING MODE: Real orders will be placed!")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

    print("=" * 60)

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        repo = CouncilRepository(session)

        # Step 1: Get council
        council = await repo.get_council_by_id(council_id)
        if not council:
            print(f"❌ Council {council_id} not found")
            return

        print(f"\n✅ Using council: {council.name}")
        capital = float(council.current_capital or council.initial_capital)
        print(f"   Capital: ${capital:,.2f}")
        print(f"   Status: {council.status}")

        # Step 2: Create consensus
        consensus = {
            "decision": decision,
            "symbol": symbol,
            "confidence": 0.75,
            "agent_votes": {"agent_1": decision},
            "vote_counts": {
                "buy": 1 if decision == "BUY" else 0,
                "sell": 1 if decision == "SELL" else 0,
                "hold": 1 if decision == "HOLD" else 0,
            },
        }
        print(f"\n📊 Consensus: {decision} {symbol} (confidence: 75%)")

        if decision == "HOLD":
            print("⏸️  HOLD decision - no trade needed")
            return

        # Step 3: Execute trade
        print("\n💰 Executing trade...")
        trading_service = CouncilTradingService(
            session, _uow, paper_trading=paper_trading
        )

        try:
            trade_result = await trading_service.aexecute_consensus_trade(
                council_id, consensus
            )

            if trade_result["success"]:
                order = trade_result["order"]
                is_paper = trade_result.get("paper_trading", False)

                if is_paper:
                    print("✅ Paper order simulated successfully!")
                else:
                    print("✅ Real order executed successfully!")

                print(f"   Order ID:  {order.order_id}")
                print(f"   Symbol:    {order.symbol}")
                print(f"   Side:      {order.side}")
                print(f"   Quantity:  {order.quantity}")
                print(f"   Price:     ${order.price:,.2f}")

                if is_paper:
                    print(
                        "\n📝 Note: This is a paper trade - no real execution on Aster"
                    )
            else:
                print(f"❌ Trade failed: {trade_result['error']}")
                return

            await session.commit()

        except Exception as e:
            print(f"❌ Error executing trade: {e}")
            return

        # Step 4: Verify database
        print("\n💾 Checking database records...")
        orders = await repo.get_market_orders(council_id, status="open")
        print(f"✅ Found {len(orders)} open orders in database")

        if orders:
            print("\n   Open Orders:")
            for order in orders[-5:]:  # Show last 5
                print(
                    f"     - {order.side.upper()} {float(order.quantity)} {order.symbol} "
                    f"@ ${float(order.entry_price):,.2f}"
                )

        # Step 5: Update PnL
        print("\n📈 Updating PnL...")
        try:
            pnl_result = await trading_service.aupdate_pnl(council_id)
            await session.commit()
            print(f"✅ PnL updated: {pnl_result}")
            unrealized_pnl = pnl_result.get("unrealized_pnl")
            pnl_pct = pnl_result.get("pnl_percentage")
            print(f"   Unrealized PnL: ${unrealized_pnl:,.2f}")
            print(f"   PnL %:          {pnl_pct:.2f}%")

            holdings_pnl = pnl_result.get("holdings_pnl", {})
            if holdings_pnl:
                print("   Holdings PnL:")
                for symbol, data in holdings_pnl.items():
                    print(f"     {symbol}:")
                    print(f"       PnL:           ${data.get('pnl', 0):,.2f}")
                    print(f"       PnL %:         {data.get('pnl_percentage', 0):.2f}%")
                    print(f"       Current Value: ${data.get('current_value', 0):,.2f}")
                    print(f"       Cost Basis:    ${data.get('cost_basis', 0):,.2f}")
        except Exception as e:
            print(f"⚠️  Error updating PnL: {e}")

        # Step 6: Show performance snapshot
        performance_history = await repo.get_performance_history(council_id, limit=1)
        if performance_history:
            performance = performance_history[0]
            print("\n📊 Latest Performance Snapshot:")
            print(f"   Total Value:   ${float(performance.total_value):,.2f}")
            print(f"   PnL:           ${float(performance.pnl):,.2f}")
            print(f"   Win Rate:      {float(performance.win_rate or 0):.1f}%")
            print(f"   Total Trades:  {performance.total_trades}")
            print(f"   Open Positions: {performance.open_positions}")

        print("\n" + "=" * 60)
        print("✅ Trading flow test completed successfully!")
        print("\nDatabase updated with:")
        print("  - Order record (market_orders table)")
        print("  - Performance history (council_performance table)")
        print("  - Updated council metrics (councils table)")
        print("=" * 60)


if __name__ == "__main__":
    main()
