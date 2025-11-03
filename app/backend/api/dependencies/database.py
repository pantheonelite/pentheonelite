"""
The module provides dependency functions for API operations.

It includes functions to initialize and manage asynchronous database sessions
using SQLAlchemy's AsyncSession.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def initialize_session() -> AsyncIterator[AsyncSession]:
    """
    Initialize a new asynchronous database session.

    Yields
    ------
        AsyncSession: An asynchronous session for database operations.

    """
    # IMPORTANT: Do NOT use scoped=True here!
    # scoped=True calls engine.dispose() after every request, destroying the connection pool
    # This causes "too many connections" errors and severe performance degradation
    async with session_manager.session(scoped=False) as session:
        yield session


async def initialize_unit_of_work() -> AsyncIterator[UnitOfWork]:
    """
    Initialize a new UnitOfWork instance.

    Yields
    ------
        UnitOfWork: A UnitOfWork instance for database operations.

    """
    # IMPORTANT: Do NOT use scoped=True here!
    # scoped=True calls engine.dispose() after every request, destroying the connection pool
    # This causes "too many connections" errors and severe performance degradation
    async with session_manager.session(scoped=False) as session, UnitOfWork(session) as uow:
        yield uow


DBSessionDep = Annotated[AsyncSession, Depends(initialize_session)]
UnitOfWorkDep = Annotated[UnitOfWork, Depends(initialize_unit_of_work)]


__all__ = ["DBSessionDep", "UnitOfWorkDep", "initialize_session", "initialize_unit_of_work"]
