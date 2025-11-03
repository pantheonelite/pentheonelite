"""Quick script to check available councils."""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.backend.db.models.council import Council  # noqa: E402
from app.backend.db.session_manager import session_manager  # noqa: E402
from app.backend.db.uow import UnitOfWork  # noqa: E402


async def check_councils():
    """Check available councils."""
    async with session_manager.session(scoped=True) as s, UnitOfWork(s) as uow:
        repo = uow.get_repository(Council)
        councils = await repo.get_all_councils()

        print("=" * 80)
        print(f"AVAILABLE COUNCILS: {len(councils)}")
        print("=" * 80)

        for c in councils:
            print(f"\nID: {c.id}")
            print(f"  Name: {c.name}")
            print(f"  Trading Mode: {c.trading_mode}")
            print(f"  Trading Type: {c.trading_type}")
            print(f"  Is System: {c.is_system}")
            print(f"  Initial Capital: ${float(c.initial_capital):,.2f}")
            print(f"  Available Balance: ${float(c.available_balance or 0):,.2f}")


if __name__ == "__main__":
    asyncio.run(check_councils())
