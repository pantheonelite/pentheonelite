"""PnL snapshot model for time-series tracking."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, text
from sqlmodel import Field, SQLModel


class PnLSnapshot(SQLModel, table=True):
    """
    Time-series snapshots of position/holding PnL.

    Used for charting and historical analysis.
    """

    __tablename__ = "pnl_snapshots"

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
        sa_column=Column(Integer, ForeignKey("futures_positions.id", ondelete="CASCADE"), nullable=True, index=True),
    )
    spot_holding_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("spot_holdings.id", ondelete="CASCADE"), nullable=True, index=True),
    )

    # Snapshot Data
    snapshot_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    mark_price: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    notional_value: Decimal | None = Field(default=None, sa_column=Column(Numeric(20, 2), nullable=True))
    unrealized_pnl: Decimal = Field(sa_column=Column(Numeric(20, 2), nullable=False))
    pnl_percentage: Decimal | None = Field(default=None, sa_column=Column(Numeric(10, 4), nullable=True))

    # For futures: liquidation risk
    liquidation_distance_pct: Decimal | None = Field(default=None, sa_column=Column(Numeric(5, 2), nullable=True))
    margin_ratio: Decimal | None = Field(default=None, sa_column=Column(Numeric(5, 4), nullable=True))

    # Metadata
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    )
