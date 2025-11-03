"""Database Session Manager."""

import contextlib
from collections.abc import AsyncIterator
from typing import Any

from app.backend.config import get_database_settings
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


class DatabaseSessionManager:
    """Database Session Manager class."""

    def __init__(
        self,
        db_host: str,
        kwargs: dict[str, Any],
        *,
        testing: bool = False,
    ) -> None:
        extra_kwargs = kwargs if kwargs else {}
        if testing:
            extra_kwargs.update({"poolclass": NullPool})
            # Remove pool-related parameters when using NullPool
            extra_kwargs.pop("pool_size", None)
            extra_kwargs.pop("max_overflow", None)

        self._engine = create_async_engine(
            db_host,
            **extra_kwargs,
        )
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            expire_on_commit=False,
            bind=self._engine,
        )

    def _validate_engine(self):
        """Ensure `self._engine` is not None."""
        if self._engine is None:
            raise RuntimeError(
                "DatabaseSessionManager is not initialized.",
            )

    async def close(self):
        """Close database connection."""
        if self._engine is None:
            return

        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Get async database connection."""
        self._validate_engine()

        async with self._engine.begin() as conn:
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise

    @contextlib.asynccontextmanager  # type: ignore[arg-type]
    async def session(self, *, scoped: bool = False) -> AsyncIterator[AsyncSession]:
        """Get async database session."""
        self._validate_engine()

        session = self._sessionmaker()

        try:
            yield session
        except Exception:
            # TODO: Add sentry integration when available
            await session.rollback()
            raise
        finally:
            await session.close()
            if scoped:
                await self._engine.dispose()


db_settings = get_database_settings()
# initialize session manager from app settings
session_manager = DatabaseSessionManager(
    str(db_settings.connection_url),
    {
        "echo": getattr(db_settings, "echo_sql", False),
        "pool_size": getattr(db_settings, "pool_size", 20),  # Increased from 5
        "max_overflow": getattr(db_settings, "max_overflow", 40),  # Increased from 10
        "pool_pre_ping": True,  # Test connections before using them to detect stale connections
        "pool_recycle": 3600,  # Recycle connections after 1 hour to prevent stale connections
        "connect_args": {
            "server_settings": {
                "lock_timeout": str(getattr(db_settings, "lock_timeout", 30)),
                "statement_timeout": str(getattr(db_settings, "statement_timeout", 30)),
            },
            "timeout": getattr(db_settings, "connect_timeout", 30),
        },
    },
    testing=getattr(db_settings, "testing", False),
)
