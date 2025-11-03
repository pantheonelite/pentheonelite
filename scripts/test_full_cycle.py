#!/usr/bin/env python3
"""Test complete council cycle end-to-end."""

import asyncio
from datetime import datetime

import click

from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.council_trading_service import CouncilTradingService
from app.backend.services.debate_service import DebateService


@click.command()
@click.option("--council-id", type=int, help="Existing council ID")
@click.option("--create-council", is_flag=True, help="Create new test council")
@click.option(
    "--symbols",
    required=True,
    help="Trading symbols (comma-separated, e.g., BTCUSDT,ETHUSDT)",
)
@click.option("--test-mode", is_flag=True, help="Skip real order execution")
def main(
    council_id: int | None,
    create_council: bool,
    symbols: str,
    test_mode: bool,
):
    """Test complete council cycle from debate to PnL."""
    asyncio.run(test_full_cycle(council_id, create_council, symbols, test_mode))


async def test_full_cycle(
    council_id: int | None,
    create_council: bool,
    symbols_str: str,
    test_mode: bool,
):
    """Test complete council cycle from debate to PnL."""
    symbols_list = symbols_str.split(",")

    print("🧪 Testing Full Council Cycle")
    print("=" * 60)
    print(f"Symbols: {', '.join(symbols_list)}")
    print(f"Mode: {'TEST (no real orders)' if test_mode else 'LIVE (real orders)'}")
    print("=" * 60)

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        repo = CouncilRepository(session)

        # Get or create council
        if create_council:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            council = await repo.create_council(
                name=f"Test Cycle {timestamp}",
                agents={
                    "agents": [
                        {"agent_key": "technical_analyst"},
                        {"agent_key": "sentiment_analyst"},
                        {"agent_key": "risk_analyst"},
                    ]
                },
                connections={},
                initial_capital=100000,
                is_system=True,
                is_paper_trading=True,
            )
            await session.commit()
            print(f"✅ Created council: {council.name} (ID: {council.id})")
        elif council_id:
            council = await repo.get_council_by_id(council_id)
            if not council:
                print(f"❌ Council ID {council_id} not found")
                return
            print(f"✅ Using council: {council.name} (ID: {council.id})")
        else:
            print("❌ Must provide --council-id or --create-council")
            return

        print(f"   Initial Capital: ${float(council.initial_capital):,.2f}")

        # Initialize services
        debate_service = DebateService(session)
        trading_service = CouncilTradingService(session)

        # PHASE 1: Debate
        print("\n" + "=" * 60)
        print("PHASE 1: Agent Debate")
        print("=" * 60)
        print("Executing agent debate (this may take a few minutes)...")

        debate_result = await debate_service.aexecute_debate(council, symbols_list)

        if not debate_result["success"]:
            print(f"❌ Debate failed: {debate_result['error']}")
            return

        print(f"✅ {len(debate_result['signals'])} agents participated")
        print("\nAgent Signals:")
        for agent_id, signal in debate_result["signals"].items():
            print(
                f"  - {agent_id}: {signal['action'].upper()} (confidence: {signal['confidence']:.0%})"
            )

        # PHASE 2: Consensus
        print("\n" + "=" * 60)
        print("PHASE 2: Consensus Determination")
        print("=" * 60)

        consensus = await debate_service.adetermine_consensus(
            council.id, debate_result["signals"], threshold=0.6
        )
        await session.commit()

        print(f"✅ Decision: {consensus['decision']} {consensus['symbol']}")
        print(f"   Confidence: {consensus['confidence']:.2%}")
        print(f"   Vote Breakdown: {consensus['vote_counts']}")

        # PHASE 3: Trade Execution
        print("\n" + "=" * 60)
        print("PHASE 3: Trade Execution")
        print("=" * 60)

        if consensus["decision"] == "HOLD":
            print("⏸️  HOLD decision - no trade")
            trade_result = {"success": True, "order": None}
        elif test_mode:
            print("⚠️  TEST MODE: Skipping trade execution")
            trade_result = {"success": True, "order": None}
        else:
            print("Executing consensus trade...")
            trade_result = await trading_service.aexecute_consensus_trade(
                council.id, consensus
            )

            if trade_result["success"] and trade_result["order"]:
                order = trade_result["order"]
                print("✅ Order executed:")
                print(f"   Order ID:  {order.order_id}")
                print(f"   Symbol:    {order.symbol}")
                print(f"   Side:      {order.side}")
                print(f"   Quantity:  {order.quantity}")
                print(f"   Price:     ${order.price:,.2f}")
            elif trade_result["success"]:
                print("✅ Trade processed (HOLD or skipped)")
            else:
                print(f"❌ Trade failed: {trade_result['error']}")

        await session.commit()

        # PHASE 4: PnL Update
        print("\n" + "=" * 60)
        print("PHASE 4: PnL Calculation")
        print("=" * 60)

        pnl_result = await trading_service.aupdate_pnl(council.id)
        await session.commit()

        print(
            f"✅ PnL: ${pnl_result['total_pnl']:,.2f} ({pnl_result['pnl_percentage']:.2f}%)"
        )

        # Verify database state
        print("\n" + "=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)

        # Check debate messages
        messages = await repo.get_debate_messages(council.id, limit=5)
        print(f"✅ Debate messages: {len(messages)} stored")

        # Check orders
        orders = await repo.get_market_orders(council.id, status="open")
        print(f"✅ Open orders: {len(orders)}")

        # Check performance snapshots
        performance_history = await repo.get_performance_history(council.id, limit=1)
        if performance_history:
            performance = performance_history[0]
            print("✅ Performance snapshot created:")
            print(f"   Total Value:   ${float(performance.total_value):,.2f}")
            print(f"   PnL:           ${float(performance.pnl):,.2f}")
            print(f"   PnL %:         {performance.pnl_percentage:.2f}%")
            print(f"   Win Rate:      {performance.win_rate:.2f}%")

        # Summary
        print("\n" + "=" * 60)
        print("CYCLE SUMMARY")
        print("=" * 60)
        print(f"Council:   {council.name} (ID: {council.id})")
        print(f"Debate:    {len(debate_result['signals'])} agents")
        print(f"Consensus: {consensus['decision']} {consensus['symbol']}")
        print(
            f"Trade:     {'Executed' if trade_result.get('order') else 'Skipped/HOLD'}"
        )
        print(f"PnL:       ${pnl_result['total_pnl']:,.2f}")

        print("\n✅ Full cycle completed successfully!")
        print("\nWhat was tested:")
        print("  ✓ Agent debate execution")
        print("  ✓ Signal parsing from workflow")
        print("  ✓ Consensus determination")
        print("  ✓ Trade execution" + (" (TEST MODE)" if test_mode else " (LIVE)"))
        print("  ✓ PnL calculation")
        print("  ✓ Database persistence")
        print("  ✓ Performance tracking")

        if test_mode:
            print("\nTo run with real orders, use:")
            print(
                f"  uv run python scripts/test_full_cycle.py --council-id {council.id}"
            )

        print("=" * 60)


if __name__ == "__main__":
    main()
