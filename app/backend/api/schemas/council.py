"""API schemas for unified Council operations (v2)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CouncilCreateRequest(BaseModel):
    """Request to create a new council."""

    name: str = Field(..., description="Council name")
    description: str | None = Field(None, description="Council description")
    agents: dict = Field(..., description="Agent configuration")
    connections: dict = Field(..., description="Agent connections")
    workflow_config: dict | None = Field(None, description="Execution rules")
    visual_layout: dict | None = Field(None, description="UI layout info")
    strategy: str | None = Field(None, description="Trading strategy")
    tags: list[str] | None = Field(None, description="Tags for categorization")
    initial_capital: float = Field(100000, description="Starting capital")
    risk_settings: dict | None = Field(None, description="Risk management")
    is_public: bool = Field(False, description="Make publicly visible")
    is_template: bool = Field(False, description="Can be used as template")
    # Wallet fields (optional)
    exchange: str | None = Field(None, description="Exchange name (e.g., 'binance', 'aster')")
    api_key: str | None = Field(None, description="API key for wallet")
    secret_key: str | None = Field(None, description="Secret key for wallet")
    ca: str | None = Field(None, description="Contract address for wallet")


class CouncilUpdateRequest(BaseModel):
    """Request to update an existing council."""

    name: str | None = None
    description: str | None = None
    agents: dict | None = None
    connections: dict | None = None
    workflow_config: dict | None = None
    visual_layout: dict | None = None
    strategy: str | None = None
    tags: list[str] | None = None
    initial_capital: float | None = None
    risk_settings: dict | None = None
    is_public: bool | None = None
    is_template: bool | None = None
    status: str | None = None


class CouncilForkRequest(BaseModel):
    """Request to fork an existing council."""

    new_name: str | None = Field(None, description="Custom name for forked council")


class CouncilResponse(BaseModel):
    """Response with council details."""

    id: int
    user_id: int | None
    wallet_id: int | None
    is_system: bool
    is_public: bool
    is_template: bool
    name: str
    description: str | None
    strategy: str | None
    tags: list[str] | None
    agents: dict
    connections: dict
    workflow_config: dict | None
    visual_layout: dict | None
    initial_capital: Decimal
    risk_settings: dict | None
    current_capital: Decimal | None
    total_pnl: Decimal | None
    total_pnl_percentage: Decimal | None
    win_rate: Decimal | None
    total_trades: int | None
    status: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
    last_executed_at: datetime | None
    view_count: int
    fork_count: int
    forked_from_id: int | None
    meta_data: dict | None


class CouncilSummaryResponse(BaseModel):
    """Lightweight council summary (for lists)."""

    id: int
    user_id: int | None
    wallet_id: int | None
    is_system: bool
    is_public: bool
    is_template: bool
    name: str
    description: str | None
    strategy: str | None
    tags: list[str] | None
    initial_capital: Decimal
    total_pnl: Decimal | None
    total_pnl_percentage: Decimal | None
    win_rate: Decimal | None
    total_trades: int | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None
    view_count: int
    fork_count: int
    forked_from_id: int | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class CouncilRunCreateRequest(BaseModel):
    """Request to create a new council run."""

    council_id: int
    trading_mode: str = Field("backtest", description="backtest, paper, or live")
    symbols: list[str] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    schedule: str | None = None
    duration: str | None = None
    request_data: dict | None = None


class CouncilRunResponse(BaseModel):
    """Response with council run details."""

    id: int
    council_id: int
    user_id: int
    trading_mode: str
    symbols: list[str] | None
    start_date: datetime | None
    end_date: datetime | None
    schedule: str | None
    duration: str | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    request_data: dict | None
    initial_portfolio: dict | None
    final_portfolio: dict | None
    performance_metrics: dict | None
    results: dict | None
    error_message: str | None
    run_number: int
    created_at: datetime | None
    updated_at: datetime | None
