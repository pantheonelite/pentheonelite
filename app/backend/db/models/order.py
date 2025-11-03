"""Order model - matches Binance order status enums."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    """
    Unified order model for futures and spot with exact Binance status enums.

    Matches Binance order response structure.
    """

    __tablename__ = "orders"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )

    # Position/Holding Links
    futures_position_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("futures_positions.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    spot_holding_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("spot_holdings.id", ondelete="SET NULL"), nullable=True, index=True),
    )

    # Order Identity (Binance standard)
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    client_order_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    order_id: int | None = Field(default=None, sa_column=Column(BigInteger, nullable=True, index=True))

    # Order Details (Binance standard)
    side: str = Field(sa_column=Column(String(10), nullable=False))  # "BUY" | "SELL"
    type: str = Field(sa_column=Column(String(30), nullable=False))  # "MARKET" | "LIMIT" | etc.
    position_side: str | None = Field(
        default=None, sa_column=Column(String(10), nullable=True)
    )  # "LONG" | "SHORT" | "BOTH" (futures only)

    # Quantities (Binance: origQty, executedQty)
    orig_qty: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    executed_qty: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 8), nullable=False, server_default="0"),
    )

    # Prices
    price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    stop_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    avg_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))

    # Order Config (Binance standard)
    time_in_force: str | None = Field(
        default=None, sa_column=Column(String(10), nullable=True)
    )  # "GTC" | "IOC" | "FOK"
    reduce_only: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))
    close_position: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))

    # Status (Binance enum exactly)
    # "NEW" | "PARTIALLY_FILLED" | "FILLED" | "CANCELED" | "REJECTED" | "EXPIRED"
    status: str = Field(sa_column=Column(String(30), nullable=False, index=True))

    # Platform Integration
    platform: str = Field(sa_column=Column(String(20), nullable=False))  # "binance" | "aster"
    trading_mode: str = Field(sa_column=Column(String(10), nullable=False))  # "paper" | "real"
    trading_type: str = Field(sa_column=Column(String(10), nullable=False))  # "futures" | "spot"

    # Timing (Binance standard fields)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    transaction_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    update_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    # Fees & Commission
    commission: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    commission_asset: str | None = Field(default=None, sa_column=Column(String(10), nullable=True))

    # Agent Context
    confidence: Decimal | None = Field(default=None, sa_column=Column(Numeric(5, 4), nullable=True))

    # Metadata
    meta_data: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
