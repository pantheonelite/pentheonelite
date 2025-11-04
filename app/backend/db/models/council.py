"""Unified Council models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class Council(SQLModel, table=True):
    """
    Unified Council model.

    A council represents a group of AI agents working together with a specific
    strategy. Councils can be:
    - System councils: Pre-made templates by Crypto Pantheon (is_system=true)
    - User councils: Custom councils created by users (is_system=false)

    Users can fork any council (system or public user council) to create
    their own customized version.

    """

    __tablename__ = "councils"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )

    # Ownership & Visibility
    user_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
    )
    wallet_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("council_wallets.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        description="Reference to wallet for API credentials",
    )
    is_system: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false", index=True),
    )
    is_public: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false", index=True),
    )
    is_template: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    is_paper_trading: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true", index=True),
    )

    # Basic Info
    name: str = Field(sa_column=Column(String(200), nullable=False))
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    strategy: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )
    tags: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(String), nullable=True),
    )

    # Configuration (from hedge_fund_flows)
    # agents: Array of agent configurations
    # Example: [{"id": "warren_buffett", "type": "value_investor", "role": "fundamental_analysis"}, ...]
    agents: dict = Field(sa_column=Column(JSONB, nullable=False))

    # connections: How agents are connected/collaborate
    # Example: [{"source": "warren_buffett", "target": "portfolio_manager"}, ...]
    connections: dict = Field(sa_column=Column(JSONB, nullable=False))

    # workflow_config: Execution rules, voting thresholds, etc.
    workflow_config: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # visual_layout: UI rendering info (viewport, node positions for React Flow)
    visual_layout: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Trading Settings
    initial_capital: Decimal = Field(
        default=Decimal(100000),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="100000"),
    )
    risk_settings: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Trading Configuration
    trading_mode: str = Field(
        default="paper",
        sa_column=Column(String(10), nullable=False, server_default="paper"),
    )  # "paper" | "real"
    trading_type: str = Field(
        default="futures",
        sa_column=Column(String(10), nullable=False, server_default="futures"),
    )  # "futures" | "spot"

    # Account Metrics
    total_account_value: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    available_balance: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    used_balance: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )

    # Futures-Specific
    total_margin_used: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    total_unrealized_profit: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )

    # Position/Holding Counts
    open_futures_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    closed_futures_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    active_spot_holdings: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )

    # PnL Tracking
    total_realized_pnl: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    net_pnl: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    total_fees: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    total_funding_fees: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )

    # Trading Statistics
    average_leverage: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(5, 2), nullable=False, server_default="0"),
    )
    average_confidence: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(5, 4), nullable=False, server_default="0"),
    )
    biggest_win: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )
    biggest_loss: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(20, 2), nullable=False, server_default="0"),
    )

    # Hold Time Statistics
    long_hold_pct: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(5, 2), nullable=False, server_default="0"),
    )
    short_hold_pct: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(5, 2), nullable=False, server_default="0"),
    )
    flat_hold_pct: Decimal = Field(
        default=Decimal(100),
        sa_column=Column(Numeric(5, 2), nullable=False, server_default="100"),
    )

    # Legacy Performance Fields (keep for backwards compatibility)
    current_capital: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 2), nullable=True),
    )
    total_pnl: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(20, 2), nullable=True),
    )
    total_pnl_percentage: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(10, 4), nullable=True),
    )
    win_rate: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(5, 2), nullable=True),
    )
    total_trades: int | None = Field(
        default=0,
        sa_column=Column(Integer, nullable=True, server_default="0"),
    )

    # Status
    status: str = Field(
        default="draft",
        sa_column=Column(String(50), nullable=False, server_default="draft"),
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )

    # Metadata
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    last_executed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Analytics
    view_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    fork_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    forked_from_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("councils.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    # Additional metadata
    meta_data: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )


class CouncilRun(SQLModel, table=True):
    """
    Council execution run.

    Tracks individual executions of a council (backtest, paper trading, live trading).

    Note: Uses council_runs_v2 table name for now (will be renamed to council_runs in migration).
    """

    __tablename__ = "council_runs_v2"

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
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )

    # Execution Config
    trading_mode: str = Field(
        default="backtest",
        sa_column=Column(String(50), nullable=False, server_default="backtest", index=True),
    )
    symbols: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(String), nullable=True),
    )
    start_date: datetime | None = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    end_date: datetime | None = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    schedule: str | None = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    duration: str | None = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )

    # Status
    status: str = Field(
        default="IDLE",
        sa_column=Column(String(50), nullable=False, server_default="IDLE", index=True),
    )
    started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Results
    request_data: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    initial_portfolio: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    final_portfolio: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    performance_metrics: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    results: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Metadata
    run_number: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, server_default="1"),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


class CouncilRunCycle(SQLModel, table=True):
    """
    Individual analysis cycle within a council run.

    Represents a single decision-making cycle where agents analyze,
    debate, and make trading decisions.

    Note: Uses council_run_cycles_v2 table name for now (will be renamed to council_run_cycles in migration).
    """

    __tablename__ = "council_run_cycles_v2"

    # Primary Key
    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, index=True),
    )

    # References
    council_run_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("council_runs_v2.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    cycle_number: int = Field(sa_column=Column(Integer, nullable=False))

    # Timing
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

    # Data
    analyst_signals: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    trading_decisions: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    executed_trades: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    portfolio_snapshot: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    performance_metrics: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    market_conditions: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Status
    status: str = Field(
        default="IN_PROGRESS",
        sa_column=Column(String(50), nullable=False, server_default="IN_PROGRESS", index=True),
    )
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    trigger_reason: str | None = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )

    # Metrics
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


__all__ = ["Council", "CouncilRun", "CouncilRunCycle"]
