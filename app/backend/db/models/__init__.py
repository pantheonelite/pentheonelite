from datetime import datetime
from decimal import Decimal

# Import unified Council models
from app.backend.db.models.council import Council, CouncilRun, CouncilRunCycle
from app.backend.db.models.consensus import ConsensusDecision

# Import new position-based models
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.models.spot_holding import SpotHolding
from app.backend.db.models.order import Order
from app.backend.db.models.pnl_snapshot import PnLSnapshot
from app.backend.db.models.wallet import Wallet

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class HedgeFundFlow(SQLModel, table=True):
    """Table to store React Flow configurations (nodes, edges, viewport)."""

    __tablename__ = "hedge_fund_flows"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    name: str = Field(sa_column=Column(String(200), nullable=False))
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    nodes: dict = Field(sa_column=Column(JSON, nullable=False))
    edges: dict = Field(sa_column=Column(JSON, nullable=False))
    viewport: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    is_template: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    tags: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class HedgeFundFlowRun(SQLModel, table=True):
    """Table to track individual execution runs of a hedge fund flow."""

    __tablename__ = "hedge_fund_flow_runs"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    flow_id: int = Field(
        sa_column=Column(Integer, ForeignKey("hedge_fund_flows.id"), nullable=False, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    status: str = Field(
        default="IDLE",
        sa_column=Column(String(50), nullable=False, server_default="IDLE"),
    )
    started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    trading_mode: str = Field(
        default="one-time",
        sa_column=Column(String(50), nullable=False, server_default="one-time"),
    )
    schedule: str | None = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    duration: str | None = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    request_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    initial_portfolio: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    final_portfolio: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    results: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    run_number: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, server_default="1"),
    )


class HedgeFundFlowRunCycle(SQLModel, table=True):
    """Individual analysis cycles within a trading session."""

    __tablename__ = "hedge_fund_flow_run_cycles"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    flow_run_id: int = Field(
        sa_column=Column(Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=False, index=True),
    )
    cycle_number: int = Field(sa_column=Column(Integer, nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    analyst_signals: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    trading_decisions: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    executed_trades: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    portfolio_snapshot: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    performance_metrics: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    status: str = Field(
        default="IN_PROGRESS",
        sa_column=Column(String(50), nullable=False, server_default="IN_PROGRESS"),
    )
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    llm_calls_count: int | None = Field(
        default=0,
        sa_column=Column(Integer, nullable=True, server_default="0"),
    )
    api_calls_count: int | None = Field(
        default=0,
        sa_column=Column(Integer, nullable=True, server_default="0"),
    )
    estimated_cost: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    trigger_reason: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    market_conditions: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class ApiKey(SQLModel, table=True):
    """Table to store API keys for various services."""

    __tablename__ = "api_keys"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    provider: str = Field(
        sa_column=Column(String(100), nullable=False, unique=True, index=True),
    )
    key_value: str = Field(sa_column=Column(Text, nullable=False))
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=True, default=True),
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    last_used: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


# OLD MODELS - DEPRECATED
# Use Council, CouncilRun, CouncilRunCycle from council.py instead
# These tables and models will be removed in a future migration

# class Council(SQLModel, table=True): ...
# class CouncilAgent(SQLModel, table=True): ...
# class AgentDebate(SQLModel, table=True): ...
# class CouncilPerformance(SQLModel, table=True): ...


class CouncilAgent(SQLModel, table=True):
    """Table to store agents that belong to a council."""

    __tablename__ = "council_agents"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    agent_name: str = Field(sa_column=Column(String(200), nullable=False))
    agent_type: str = Field(
        sa_column=Column(String(100), nullable=False),
    )
    role: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    traits: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    specialty: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
    )
    system_prompt: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
    )
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class AgentDebate(SQLModel, table=True):
    """Table to store debate/discussion messages between agents."""

    __tablename__ = "agent_debates"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
    )
    agent_name: str = Field(sa_column=Column(String(200), nullable=False))
    message: str = Field(sa_column=Column(Text, nullable=False))
    message_type: str = Field(
        default="analysis",
        sa_column=Column(String(50), nullable=False, server_default="analysis"),
    )
    sentiment: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )
    market_symbol: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True, index=True),
    )
    confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 2), nullable=True),
    )
    debate_round: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class PortfolioHolding(SQLModel, table=True):
    """Table to store portfolio holdings for spot trading."""

    __tablename__ = "portfolio_holdings"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    quantity: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    average_cost: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    total_cost: Decimal = Field(sa_column=Column(Numeric(20, 2), nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


class MarketOrder(SQLModel, table=True):
    """
    Table to store market orders executed by the council.

    For spot trading: side is 'buy' or 'sell' (not 'long'/'short').
    Each order represents an immediate trade, not a position to be closed later.
    """

    __tablename__ = "market_orders"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    symbol: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    order_type: str = Field(
        sa_column=Column(String(20), nullable=False),
    )
    side: str = Field(
        sa_column=Column(String(10), nullable=False),  # "buy" or "sell" for spot trading
    )
    quantity: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))
    entry_price: Decimal = Field(sa_column=Column(Numeric(20, 8), nullable=False))

    # New fields for spot trading
    confidence: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 4), nullable=True),  # Agent confidence 0.0-1.0
    )
    position_size_pct: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 4), nullable=True),  # Percentage of capital used
    )
    is_paper_trade: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )

    # Legacy fields - kept for backwards compatibility but deprecated for spot trading
    exit_price: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 8), nullable=True),
    )
    stop_loss: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 8), nullable=True),
    )
    take_profit: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 8), nullable=True),
    )
    status: str = Field(
        default="filled",  # Default to "filled" for spot trades
        sa_column=Column(String(20), nullable=False, server_default="filled", index=True),
    )
    opened_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    closed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    pnl: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 2), nullable=True),
    )
    pnl_percentage: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(10, 4), nullable=True),
    )
    notes: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class CouncilPerformance(SQLModel, table=True):
    """Table to store historical performance metrics of a council."""

    __tablename__ = "council_performance"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )
    council_id: int = Field(
        sa_column=Column(Integer, ForeignKey("councils.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    total_value: Decimal = Field(sa_column=Column(Numeric(20, 2), nullable=False))
    pnl: Decimal = Field(sa_column=Column(Numeric(20, 2), nullable=False))
    pnl_percentage: Decimal = Field(sa_column=Column(Numeric(10, 4), nullable=False))
    win_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 2), nullable=True),
    )
    total_trades: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    open_positions: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


# Import unified Council models (already imported at top of file)
# from app.backend.db.models.council import Council, CouncilRun, CouncilRunCycle
from app.backend.db.models.user import User

__all__ = [
    "AgentDebate",
    "ApiKey",
    "ConsensusDecision",
    "Council",
    "CouncilAgent",
    "CouncilPerformance",
    "CouncilRun",
    "CouncilRunCycle",
    "HedgeFundFlow",
    "HedgeFundFlowRun",
    "HedgeFundFlowRunCycle",
    "MarketOrder",
    "PortfolioHolding",
    "User",
    "Wallet",
]
