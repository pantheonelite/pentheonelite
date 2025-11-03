"""Minimal User model for local testing."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    Minimal User model for local testing.

    This is a placeholder until full authentication is implemented.
    For now, all councils will use user_id=1 (test user).
    """

    __tablename__ = "users"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    email: str = Field(
        sa_column=Column(String(255), nullable=False, unique=True, index=True),
    )
    wallet_address: str | None = Field(
        default=None,
        sa_column=Column(String(255), nullable=True, unique=True, index=True),
    )
    username: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True),
    )
