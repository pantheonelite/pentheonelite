"""Database configuration helpers."""

from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.pool import NullPool


class DatabaseSettings(BaseSettings):
    """Connection settings for the persistence layer."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_", case_sensitive=False)

    url: str | None = None
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    name: str = "hedge_fund"
    echo: bool = False
    pool_size: int = 20  # Increased from 10 to handle more concurrent requests
    max_overflow: int = 40  # Increased from 20 to prevent connection exhaustion
    connect_timeout: int = 600  # Increased from 10 to 60 for containerized environments
    statement_timeout: int = 60000  # Increased from 20000 to 60000 (60 seconds)
    lock_timeout: int = 30000  # Increased from 10000 to 30000 (30 seconds)
    testing: bool = False
    test_url: str | None = None
    application_name: str = "vibe-trading-backend"
    use_nullpool: bool = False

    @property
    def connection_url(self) -> str:
        """Return the database URL, preferring explicit values."""
        if self.testing and self.test_url:
            return self.test_url
        if self.url:
            return self.url

        # Auto-detect: Use PostgreSQL if host is set (Docker/production), else SQLite (local dev)
        if self.host and self.host != "localhost":
            # Docker or remote PostgreSQL
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        if self.user != "postgres" or self.password != "":
            # Local PostgreSQL with custom credentials
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        # Default to SQLite for local development
        return "sqlite+aiosqlite:///./hedge_fund.db"

    @property
    def engine_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for SQLAlchemy async engine."""
        # Check if using SQLite
        if self.url and "sqlite" in self.url:
            # SQLite configuration
            return {
                "echo": self.echo,
                "connect_args": {"check_same_thread": False},
            }

        # Default SQLite for development
        if not self.url:
            return {
                "echo": self.echo,
                "connect_args": {"check_same_thread": False},
            }

        # PostgreSQL configuration
        kwargs: dict[str, Any] = {
            "echo": self.echo,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_pre_ping": True,  # Test connections before using them
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "connect_args": {
                "timeout": self.connect_timeout,
                "server_settings": {
                    "statement_timeout": str(self.statement_timeout),
                    "lock_timeout": str(self.lock_timeout),
                    "application_name": self.application_name,
                },
            },
        }

        if self.testing:
            kwargs["pool_size"] = kwargs.get("pool_size") or 5
            kwargs["max_overflow"] = kwargs.get("max_overflow") or 0

        if self.testing or self.use_nullpool:
            kwargs.pop("pool_size", None)
            kwargs.pop("max_overflow", None)
            kwargs["poolclass"] = NullPool

        return kwargs


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Load database settings with sane defaults."""
    return DatabaseSettings()
