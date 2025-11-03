#!/usr/bin/env python3
"""Reset council data script for local testing.

This script deletes all council-related data including:
- Councils
- Market orders/trades
- Portfolio holdings
- Council runs and cycles
- Agent debates
- Council performance snapshots

WARNING: This is DESTRUCTIVE and should only be used for local testing!
"""

import asyncio
import sys

import structlog
from sqlalchemy import delete, select

from app.backend.db.models import (
    AgentDebate,
    Council,
    CouncilPerformance,
    MarketOrder,
    PortfolioHolding,
)
from app.backend.db.models.council import CouncilRun, CouncilRunCycle
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.models.order import Order
from app.backend.db.models.pnl_snapshot import PnLSnapshot
from app.backend.db.models.spot_holding import SpotHolding
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork

logger = structlog.get_logger(__name__)


async def confirm_reset():
    """Ask user to confirm the destructive operation."""
    print("\n" + "=" * 70)
    print("⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️")
    print("=" * 70)
    print("\nThis will DELETE ALL council-related data including:")
    print("  - All councils (system and user)")
    print("  - All futures positions (NEW)")
    print("  - All spot holdings (NEW)")
    print("  - All orders (NEW)")
    print("  - All PnL snapshots (NEW)")
    print("  - All market orders/trades (DEPRECATED)")
    print("  - All portfolio holdings (DEPRECATED)")
    print("  - All council runs and cycles")
    print("  - All agent debates")
    print("  - All council performance snapshots")
    print("\n" + "=" * 70)

    response = input("\nType 'DELETE ALL' to confirm: ")

    if response != "DELETE ALL":
        print("\n❌ Reset cancelled - no data was deleted")
        return False

    return True


async def get_data_counts(session):
    """Get counts of all data to be deleted."""
    counts = {}

    # Helper function to safely count
    async def safe_count(model, name):
        try:
            result = await session.execute(select(model))
            return len(result.scalars().all())
        except Exception:
            # Table doesn't exist (might be deprecated or not created yet)
            return 0

    # Count councils
    counts["councils"] = await safe_count(Council, "councils")

    # Count NEW tables
    counts["futures_positions"] = await safe_count(FuturesPosition, "futures_positions")
    counts["spot_holdings"] = await safe_count(SpotHolding, "spot_holdings")
    counts["orders"] = await safe_count(Order, "orders")
    counts["pnl_snapshots"] = await safe_count(PnLSnapshot, "pnl_snapshots")

    # Count DEPRECATED tables (might not exist or be renamed)
    counts["market_orders_deprecated"] = await safe_count(MarketOrder, "market_orders")
    counts["portfolio_holdings_deprecated"] = await safe_count(
        PortfolioHolding, "portfolio_holdings"
    )

    # Count other tables
    counts["council_runs"] = await safe_count(CouncilRun, "council_runs")
    counts["council_run_cycles"] = await safe_count(
        CouncilRunCycle, "council_run_cycles"
    )
    counts["agent_debates"] = await safe_count(AgentDebate, "agent_debates")
    counts["council_performance"] = await safe_count(
        CouncilPerformance, "council_performance"
    )

    return counts


async def delete_all_council_data():
    """Delete all council-related data."""
    logger.info("🗑️  Starting council data deletion...")

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        try:
            # Get counts before deletion
            counts = await get_data_counts(session)

            print("\n📊 Current data counts:")
            for table, count in counts.items():
                print(f"  - {table}: {count}")

            if sum(counts.values()) == 0:
                print("\n✅ No data to delete - database is already clean")
                return

            print("\n🗑️  Deleting data...")

            # Helper function to safely delete
            async def safe_delete(model, name):
                try:
                    result = await session.execute(delete(model))
                    await (
                        session.commit()
                    )  # Commit after each delete to avoid transaction issues
                    count = result.rowcount
                    logger.info(f"Deleted {count} {name}")
                    return count
                except Exception as e:
                    await session.rollback()  # Rollback on error
                    logger.info(f"Skipped {name} (error: {str(e)[:100]})")
                    return 0

            # Delete in reverse order of dependencies
            await safe_delete(PnLSnapshot, "PnL snapshots")
            await safe_delete(Order, "orders")
            await safe_delete(FuturesPosition, "futures positions")
            await safe_delete(SpotHolding, "spot holdings")
            deleted_cycles = await safe_delete(CouncilRunCycle, "council run cycles")
            deleted_runs = await safe_delete(CouncilRun, "council runs")
            deleted_debates = await safe_delete(AgentDebate, "agent debates")
            deleted_performance = await safe_delete(
                CouncilPerformance, "council performance"
            )
            deleted_orders = await safe_delete(
                MarketOrder, "market orders (deprecated)"
            )
            deleted_holdings = await safe_delete(
                PortfolioHolding, "portfolio holdings (deprecated)"
            )
            deleted_councils = await safe_delete(Council, "councils")

            # Commit all deletions
            await session.commit()

            # Print summary
            print("\n✅ Deletion complete!")
            print("\n📊 Deleted records:")
            print(f"  - Council run cycles: {deleted_cycles}")
            print(f"  - Council runs: {deleted_runs}")
            print(f"  - Agent debates: {deleted_debates}")
            print(f"  - Performance snapshots: {deleted_performance}")
            print(f"  - Market orders: {deleted_orders}")
            print(f"  - Portfolio holdings: {deleted_holdings}")
            print(f"  - Councils: {deleted_councils}")
            print(
                f"\n  Total records deleted: {deleted_cycles + deleted_runs + deleted_debates + deleted_performance + deleted_orders + deleted_holdings + deleted_councils}"
            )

        except Exception as e:
            logger.error(f"Error during deletion: {e}", exc_info=True)
            await session.rollback()
            raise


async def delete_specific_councils(council_ids: list[int]):
    """Delete specific councils by ID."""
    logger.info(f"🗑️  Deleting councils: {council_ids}")

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        try:
            deleted_count = 0
            for council_id in council_ids:
                # Check if council exists
                result = await session.execute(
                    select(Council).where(Council.id == council_id)
                )
                council = result.scalar_one_or_none()

                if not council:
                    print(f"⚠️  Council {council_id} not found - skipping")
                    continue

                # Delete council (cascades to related data)
                await session.delete(council)
                deleted_count += 1

                print(f"✅ Deleted council {council_id} ({council.name})")

            await session.commit()

            print(f"\n✅ Successfully deleted {deleted_count} council(s)")

        except Exception as e:
            logger.error(f"Error during deletion: {e}", exc_info=True)
            await session.rollback()
            raise


async def delete_system_councils_only():
    """Delete only system councils (is_system=true)."""
    logger.info("🗑️  Deleting system councils only...")

    async with (
        session_manager.session(scoped=True) as session,
        UnitOfWork(session) as _uow,
    ):
        try:
            # Get system councils
            result = await session.execute(
                select(Council).where(Council.is_system == True)  # noqa: E712
            )
            system_councils = result.scalars().all()

            if not system_councils:
                print("✅ No system councils to delete")
                return

            print(f"\n📊 Found {len(system_councils)} system councils:")
            for council in system_councils:
                print(f"  - {council.id}: {council.name}")

            # Delete system councils (cascades to related data)
            result = await session.execute(
                delete(Council).where(Council.is_system == True)  # noqa: E712
            )
            deleted_count = result.rowcount

            await session.commit()

            print(
                f"\n✅ Deleted {deleted_count} system council(s) and their related data"
            )

        except Exception as e:
            logger.error(f"Error during deletion: {e}", exc_info=True)
            await session.rollback()
            raise


async def main():
    """Main function with command-line options."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reset council data for local testing",
        epilog="WARNING: This is a destructive operation! Use only for local testing.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete all council data (requires confirmation)",
    )
    parser.add_argument(
        "--councils",
        nargs="+",
        type=int,
        metavar="ID",
        help="Delete specific councils by ID (e.g., --councils 1 2 3)",
    )
    parser.add_argument(
        "--system-only",
        action="store_true",
        help="Delete only system councils (is_system=true)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)",
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any([args.all, args.councils, args.system_only]):
        parser.print_help()
        print("\n💡 Examples:")
        print("  # Delete all council data (with confirmation)")
        print("  python scripts/reset_council_data.py --all")
        print("\n  # Delete specific councils")
        print("  python scripts/reset_council_data.py --councils 1 2 3")
        print("\n  # Delete only system councils")
        print("  python scripts/reset_council_data.py --system-only")
        print("\n  # Delete all without confirmation (dangerous!)")
        print("  python scripts/reset_council_data.py --all --yes")
        return

    try:
        # Confirmation for destructive operations
        if not args.yes:
            if args.all:
                if not await confirm_reset():
                    return
            elif args.system_only:
                response = input("\n⚠️  Delete all system councils? (y/N): ")
                if response.lower() != "y":
                    print("❌ Cancelled")
                    return
            elif args.councils:
                response = input(f"\n⚠️  Delete councils {args.councils}? (y/N): ")
                if response.lower() != "y":
                    print("❌ Cancelled")
                    return

        # Execute deletion
        if args.all:
            await delete_all_council_data()
        elif args.councils:
            await delete_specific_councils(args.councils)
        elif args.system_only:
            await delete_system_councils_only()

        print("\n✅ Operation completed successfully")

    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
