"""Consensus decision models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class ConsensusDecision(SQLModel, table=True):
    """
    Consensus decision made by a council.

    Tracks all consensus decisions including BUY, SELL, and HOLD decisions.
    This ensures we have a complete history of all council decisions,
    not just the ones that resulted in trades.
    """

    __tablename__ = "consensus_decisions"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )

    # References
    council_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("councils.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    council_run_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("council_runs_v2.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    council_run_cycle_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("council_run_cycles_v2.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )

    # Timestamp
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            index=True,
        ),
    )

    # Consensus Decision
    decision: str = Field(sa_column=Column(String(20), nullable=False, index=True))  # BUY, SELL, HOLD
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 4), nullable=True),
    )

    # Vote Breakdown
    votes_buy: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    votes_sell: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    votes_hold: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    total_votes: int = Field(sa_column=Column(Integer, nullable=False))

    # Agent Votes (JSON mapping agent_name -> vote)
    agent_votes: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Reasoning
    reasoning: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Market Conditions
    market_price: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 8), nullable=True),
    )
    market_conditions: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Execution Results
    was_executed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    market_order_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("market_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    execution_reason: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )

    # Metadata
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )


__all__ = ["ConsensusDecision"]
