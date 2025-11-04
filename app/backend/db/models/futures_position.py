"""Futures position model - matches Binance Futures API."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FuturesPosition(SQLModel, table=True):
    """
    Futures position model matching Binance/Aster Perpetual API.

    Tracks leveraged LONG/SHORT positions with margin, liquidation, and PnL.
    """

    __tablename__ = "futures_positions"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )

    # Position Identity (Binance/Aster standard)
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    position_side: str = Field(sa_column=Column(String(10), nullable=False, index=True))  # "LONG" | "SHORT" | "BOTH"

    # Position Quantities (Binance: positionAmt)
    position_amt: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))

    # Prices (Binance/Aster standard)
    entry_price: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    mark_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    liquidation_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))

    # Leverage & Margin (Binance/Aster standard)
    leverage: int = Field(default=1, sa_column=Column(Integer, nullable=False, server_default="1"))
    margin_type: str = Field(sa_column=Column(String(10), nullable=False))  # "ISOLATED" | "CROSSED"
    isolated_margin: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))

    # Notional Value (Binance standard)
    notional: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))

    # PnL (Binance: unRealizedProfit)
    unrealized_profit: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))
    realized_pnl: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))

    # Platform Integration
    platform: str = Field(sa_column=Column(String(20), nullable=False))  # "binance" | "aster"
    trading_mode: str = Field(sa_column=Column(String(10), nullable=False))  # "paper" | "real"
    external_position_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))

    # Status & Lifecycle
    status: str = Field(sa_column=Column(String(20), nullable=False, index=True))  # "OPEN" | "CLOSED" | "LIQUIDATED"
    opened_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    closed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    # Metrics
    max_notional: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))
    fees_paid: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    funding_fees: Decimal = Field(
        default=Decimal(0), sa_column=Column(Numeric(20, 2), nullable=False, server_default="0")
    )

    # Agent Decision Context
    confidence: Decimal | None = Field(default=None, sa_column=Column(Numeric(5, 4), nullable=True))
    agent_reasoning: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Exit Plan (Stop Loss & Take Profit)
    stop_loss_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    stop_loss_order_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    take_profit_short: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    take_profit_short_order_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    take_profit_mid: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    take_profit_mid_order_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    take_profit_long: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 8), nullable=True))
    take_profit_long_order_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))

    # Metadata
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
    meta_data: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
