"""Spot holding model - matches Binance Spot API."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class SpotHolding(SQLModel, table=True):
    """
    Spot asset holding model matching Binance Spot API.

    Tracks asset balances without leverage (simple buy/sell).
    """

    __tablename__ = "spot_holdings"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )

    # Asset Identity
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    base_asset: str = Field(sa_column=Column(String(10), nullable=False))  # e.g., "BTC"
    quote_asset: str = Field(sa_column=Column(String(10), nullable=False))  # e.g., "USDT"

    # Holding Quantities (Binance Spot standard)
    free: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))  # Available balance
    locked: Decimal = Field(
        default=Decimal(0), sa_column=Column(Numeric(20, 8), nullable=False, server_default="0")
    )  # Locked in orders
    total: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))  # Total = free + locked

    # Cost Basis
    average_cost: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    total_cost: Decimal = Field(sa_column=Column(Numeric(20, 2), nullable=False))

    # Current Value
    current_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    current_value: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))
    unrealized_pnl: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))

    # Platform Integration
    platform: str = Field(sa_column=Column(String(20), nullable=False))  # "binance" | "aster"
    trading_mode: str = Field(sa_column=Column(String(10), nullable=False))  # "paper" | "real"

    # Status
    status: str = Field(
        default="ACTIVE", sa_column=Column(String(20), nullable=False, server_default="ACTIVE", index=True)
    )  # "ACTIVE" | "CLOSED"

    # Lifecycle
    first_acquired_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    last_updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    closed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    # Metadata
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    meta_data: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
