from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DebateMessage(BaseModel):
    """Debate message model."""

    id: int
    agent_name: str
    message: str
    message_type: str
    sentiment: str | None
    market_symbol: str | None
    confidence: float | None
    debate_round: int | None
    created_at: datetime
    council_id: int | None = None
    council_name: str | None = None


class TradeRecord(BaseModel):
    """Trade record model."""

    id: int
    symbol: str
    order_type: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float | None
    pnl: float | None
    pnl_percentage: float | None
    status: str
    opened_at: datetime
    closed_at: datetime | None
    council_id: int | None = None
    council_name: str | None = None


class PerformanceDataPoint(BaseModel):
    """Performance chart data point."""

    timestamp: datetime
    total_value: float
    pnl: float
    pnl_percentage: float
    win_rate: float | None
    total_trades: int
    open_positions: int


class ConsensusDecisionResponse(BaseModel):
    """Consensus decision response model."""

    id: int
    council_id: int
    decision: str
    symbol: str
    confidence: float | None
    votes_buy: int
    votes_sell: int
    votes_hold: int
    total_votes: int
    agent_votes: dict | None
    reasoning: str | None
    market_price: float | None
    was_executed: bool
    market_order_id: int | None
    execution_reason: str | None
    created_at: datetime


class AgentInfo(BaseModel):
    """Agent information from council."""

    id: str
    name: str
    type: str
    role: str | None
    traits: list[str] | None
    specialty: str | None
    system_prompt: str | None
    position: dict[str, Any] | None


class PortfolioHoldingDetail(BaseModel):
    """Portfolio holding detail."""

    quantity: float
    avg_cost: float
    total_cost: float
    current_value: float | None = None
    unrealized_pnl: float | None = None


class CouncilOverviewResponse(BaseModel):
    """Comprehensive council overview response."""

    id: int
    name: str
    description: str | None
    strategy: str | None
    is_system: bool
    is_public: bool
    status: str
    is_paper_trading: bool
    initial_capital: float
    current_capital: float
    available_capital: float
    total_pnl: float
    total_pnl_percentage: float
    win_rate: float | None
    total_trades: int
    open_positions_count: int
    closed_positions_count: int
    created_at: datetime
    last_executed_at: datetime | None
    agents: list[AgentInfo] | None = None
    recent_debates: list[DebateMessage] | None = None
    recent_trades: list[TradeRecord] | None = None
    portfolio_holdings: dict[str, PortfolioHoldingDetail] | None = None


class GlobalActivityResponse(BaseModel):
    """Global activity across all system councils."""

    debates: list[DebateMessage]
    trades: list[TradeRecord]
    councils: dict[int, str]


class HoldTimes(BaseModel):
    """Hold times breakdown."""

    long: float
    short: float
    flat: float


class TradingMetricsResponse(BaseModel):
    """Comprehensive trading metrics for a council."""

    net_realized: float
    average_leverage: float
    average_confidence: float
    biggest_win: float
    biggest_loss: float
    hold_times: HoldTimes


class ActivePosition(BaseModel):
    """Active trading position."""

    id: int
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    leverage: float
    unrealized_pnl: float
    unrealized_pnl_percentage: float
    opened_at: datetime
    liquidation_price: float | None = None


class ActivePositionsResponse(BaseModel):
    """List of active positions."""

    positions: list[ActivePosition]
    total_unrealized_pnl: float
