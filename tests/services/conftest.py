"""Shared fixtures for service tests."""

from decimal import Decimal

import pytest

from app.backend.db.models.council import Council
from app.backend.db.session_manager import session_manager


@pytest.fixture
async def session():
    """Create async database session for testing."""
    async with session_manager.session(scoped=True) as session:
        yield session


@pytest.fixture
async def test_council(session):
    """Create a test council for futures trading."""
    council = Council(
        name="Test Futures Council",
        agents={"agent1": {"type": "analyst"}},
        connections={},
        initial_capital=Decimal(10000),
        trading_mode="paper",
        trading_type="futures",
        status="active",
    )
    session.add(council)
    await session.commit()
    await session.refresh(council)
    yield council

    # Cleanup
    await session.delete(council)
    await session.commit()
