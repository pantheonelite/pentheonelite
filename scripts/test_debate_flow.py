#!/usr/bin/env python3
"""Test debate flow with real services and database."""

import asyncio

import click

from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.debate_service import DebateService


@click.command()
@click.option(
    "--symbols",
    required=True,
    help="Trading symbols (comma-separated, e.g., BTCUSDT,ETHUSDT)",
)
@click.option("--council-id", type=int, help="Use existing council ID")
@click.option(
    "--threshold", type=float, default=0.6, help="Consensus threshold (0.0-1.0)"
)
def main(symbols: str, council_id: int | None, threshold: float):
    """Test debate execution and consensus determination."""
    asyncio.run(test_debate_flow(symbols, council_id, threshold))


async def test_debate_flow(symbols_str: str, council_id: int | None, threshold: float):
    """Test debate execution and consensus determination."""
    symbols_list = symbols_str.split(",")

    print("🧪 Testing Debate Flow")
    print("=" * 60)
    print(f"Symbols: {', '.join(symbols_list)}")
    print(f"Consensus Threshold: {threshold:.0%}")
    print("=" * 60)

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        repo = CouncilRepository(session)

        # Step 1: Get or create council
        if council_id:
            council = await repo.get_council_by_id(council_id)
            if not council:
                print(f"❌ Council ID {council_id} not found")
                return
            print(f"✅ Using existing council: {council.name} (ID: {council.id})")
        else:
            council = await repo.create_council(
                name="Test Debate Council",
                agents={
                    "agents": [
                        {"agent_key": "technical_analyst"},
                        {"agent_key": "sentiment_analyst"},
                    ]
                },
                connections={},
                initial_capital=100000,
                is_system=True,
                is_paper_trading=True,
            )
            await session.commit()
            print(f"✅ Created test council: {council.name} (ID: {council.id})")

        print(f"   Initial Capital: ${float(council.initial_capital):,.2f}")
        print(f"   Is System: {council.is_system}")

        # Step 2: Run debate
        print("\n📊 Executing agent debate...")
        print("   This may take a few minutes as agents analyze the markets...")
        debate_service = DebateService(session)
        debate_result = await debate_service.aexecute_debate(council, symbols_list)

        if debate_result["success"]:
            print("✅ Debate completed successfully")
            print(f"\n📈 Agent Signals ({len(debate_result['signals'])} agents):")
            for agent_id, signal in debate_result["signals"].items():
                print(f"\n  {agent_id}:")
                print(f"    Symbol:     {signal['symbol']}")
                print(f"    Action:     {signal['action'].upper()}")
                print(f"    Sentiment:  {signal['sentiment']}")
                print(f"    Confidence: {signal['confidence']:.2%}")
                print(f"    Reasoning:  {signal['reasoning'][:150]}...")
        else:
            print(f"❌ Debate failed: {debate_result['error']}")
            return

        # Step 3: Determine consensus
        print("\n🤝 Determining consensus...")
        consensus = await debate_service.adetermine_consensus(
            council.id, debate_result["signals"], threshold=threshold
        )
        await session.commit()

        print(f"\n✅ Consensus Decision: {consensus['decision']}")
        print(f"   Symbol:     {consensus['symbol']}")
        print(f"   Confidence: {consensus['confidence']:.2%}")
        print("\n   Vote Breakdown:")
        print(f"     BUY:  {consensus['vote_counts']['buy']} agents")
        print(f"     SELL: {consensus['vote_counts']['sell']} agents")
        print(f"     HOLD: {consensus['vote_counts']['hold']} agents")

        print("\n   Agent Votes:")
        for agent_name, vote in consensus["agent_votes"].items():
            print(f"     {agent_name}: {vote}")

        # Step 4: Verify database
        print("\n💾 Checking database records...")
        messages = await repo.get_recent_debates(council.id, limit=20)
        print(f"✅ Found {len(messages)} debate messages in database")

        # Show sample messages
        if messages:
            print("\n   Recent debate messages:")
            for msg in messages[-5:]:  # Last 5 messages
                print(
                    f"     - [{msg.message_type}] {msg.agent_name}: "
                    f"{msg.message[:80]}..."
                )

        print("\n" + "=" * 60)
        print("✅ Debate flow test completed successfully!")
        print("\nNext steps:")
        print(
            f"  - Run trading flow: uv run python scripts/test_trading_flow.py --council-id {council.id}"
        )
        print(
            f"  - Run full cycle: uv run python scripts/test_full_cycle.py --council-id {council.id}"
        )
        print("=" * 60)


if __name__ == "__main__":
    main()
