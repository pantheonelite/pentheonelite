"""Wallet model for council API credentials."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class Wallet(SQLModel, table=True):
    """
    Wallet model for storing API credentials per council.
    
    Each council can have one wallet associated with it for trading operations.
    The wallet stores API keys, secret keys, and optionally a contract address.
    """

    __tablename__ = "council_wallets"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )

    # Foreign Key to Council (one-to-one relationship)
    council_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("councils.id", ondelete="CASCADE"),
            nullable=True,
            unique=True,
            index=True,
        ),
    )

    # Wallet name (optional, for display purposes)
    name: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="Wallet name for display purposes",
    )

    # Exchange (e.g., "binance", "aster")
    exchange: str = Field(
        sa_column=Column(String(50), nullable=False),
        description="Exchange name: binance, aster, etc.",
    )

    # API Credentials
    api_key: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    secret_key: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    ca: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="Contract address (optional)",
    )

    # Status
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )

    # Timestamps
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

