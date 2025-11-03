"""Test single council cycle with full error logging."""

import asyncio
import logging

import structlog

from app.backend.services.council_orchestrator import CouncilOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = structlog.get_logger(__name__)


async def main():
    """Run single council cycle."""
    print("\n" + "=" * 80)
    print("TESTING COUNCIL 113 (Crypto Pantheon Elite) - PAPER TRADING")
    print("Symbol: BTCUSDT")
    print("=" * 80 + "\n")

    try:
        orchestrator = CouncilOrchestrator(
            symbols_override=["BTCUSDT"],
            schedule_interval_seconds=3600,
        )

        logger.info("Running single council cycle for ID 113...")

        result = await orchestrator.run_council_cycle(113)

        print("\n" + "=" * 80)
        print("CYCLE RESULTS")
        print("=" * 80)
        print(f"✅ Success: {result.get('success')}")

        if result.get("success"):
            print(f"   Consensuses: {len(result.get('consensuses', []))}")
            print(f"   Trades Executed: {result.get('trades_executed', 0)}")
            print(f"   Trades Skipped: {result.get('trades_skipped', 0)}")

            if result.get("consensuses"):
                print("\n📊 Consensus Decisions:")
                for consensus in result["consensuses"]:
                    print(f"   Symbol: {consensus.get('symbol')}")
                    print(f"   Decision: {consensus.get('decision')}")
                    print(f"   Confidence: {consensus.get('confidence', 0) * 100:.1f}%")
                    print()
        else:
            print(f"❌ Error: {result.get('error')}")

    except Exception as e:
        logger.exception("Test failed", error=str(e))
        print(f"\n❌ FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
