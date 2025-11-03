"""Agent context schemas for the trading system."""

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class TradingMode(StrEnum):
    """Trading mode enumeration."""

    LIVE = "live"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


class RiskTolerance(StrEnum):
    """Risk tolerance levels."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class BaseAgentContext(BaseModel):
    """Base context for all trading agents."""

    # Core identifiers
    session_id: Annotated[str, Field(description="Unique session identifier")]
    trace_id: Annotated[str | None, Field(description="Trace ID for observability", default=None)]

    # Trading context
    symbols: Annotated[list[str], Field(description="List of crypto symbols to analyze")]
    exchanges: Annotated[
        list[str],
        Field(description="List of exchanges to use", default_factory=lambda: ["binance", "coinbase", "kraken"]),
    ]
    trading_mode: Annotated[TradingMode, Field(description="Current trading mode")]
    risk_tolerance: Annotated[
        RiskTolerance,
        Field(description="Risk tolerance level", default=RiskTolerance.MODERATE),
    ]

    # Time context
    start_date: Annotated[str, Field(description="Analysis start date")]
    end_date: Annotated[str, Field(description="Analysis end date")]
    current_date: Annotated[str, Field(description="Current analysis date")]

    # Model configuration
    model_name: Annotated[str, Field(description="LLM model name", default="gpt-4")]
    model_provider: Annotated[str, Field(description="Model provider", default="OpenAI")]

    # Feature flags
    show_reasoning: Annotated[bool, Field(description="Show agent reasoning", default=False)]
    enable_streaming: Annotated[bool, Field(description="Enable streaming responses", default=False)]

    # Metadata
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class TradingContext(BaseAgentContext):
    """Extended context for trading operations."""

    # Portfolio information
    initial_cash: Annotated[float, Field(description="Initial cash amount", default=100000.0)]
    margin_requirement: Annotated[float, Field(description="Margin requirement", default=0.5)]
    margin_used: Annotated[float, Field(description="Current margin used", default=0.0)]

    # Portfolio positions
    positions: Annotated[
        dict[str, "CryptoPosition"],
        Field(description="Current crypto positions", default_factory=dict),
    ]

    # Performance tracking
    realized_gains: Annotated[
        dict[str, dict[str, float]],
        Field(description="Realized gains by ticker", default_factory=dict),
    ]

    # Analysis results
    analyst_signals: Annotated[
        dict[str, dict[str, Any]],
        Field(description="Analyst signals", default_factory=dict),
    ]

    # API configuration
    api_keys: Annotated[
        dict[str, str],
        Field(description="API keys for external services", default_factory=dict),
    ]


class AgentContext(BaseAgentContext):
    """Context for individual agent execution."""

    # Agent identification
    agent_id: Annotated[str, Field(description="Unique agent identifier")]
    agent_name: Annotated[str, Field(description="Human-readable agent name")]
    agent_type: Annotated[str, Field(description="Type of agent (analyst, risk_manager, etc.)")]

    # Execution context
    execution_order: Annotated[int, Field(description="Execution order in workflow", default=0)]
    dependencies: Annotated[list[str], Field(description="Agent dependencies", default_factory=list)]

    # Data context
    input_data: Annotated[dict[str, Any], Field(description="Input data for agent", default_factory=dict)]
    output_data: Annotated[
        dict[str, Any],
        Field(description="Output data from agent", default_factory=dict),
    ]

    # Status tracking
    status: Annotated[str, Field(description="Current agent status", default="pending")]
    error_message: Annotated[str | None, Field(description="Error message if failed", default=None)]

    # Performance metrics
    execution_time: Annotated[float | None, Field(description="Execution time in seconds", default=None)]
    memory_usage: Annotated[float | None, Field(description="Memory usage in MB", default=None)]


class CryptoPosition(BaseModel):
    """Cryptocurrency position representation."""

    symbol: Annotated[str, Field(description="Cryptocurrency symbol")]
    amount: Annotated[float, Field(description="Amount of crypto held", default=0.0)]
    cost_basis: Annotated[float, Field(description="Average cost per unit", default=0.0)]
    current_price: Annotated[float, Field(description="Current market price", default=0.0)]
    market_value: Annotated[float, Field(description="Current market value", default=0.0)]
    unrealized_pnl: Annotated[float, Field(description="Unrealized P&L", default=0.0)]
    exchange: Annotated[str | None, Field(description="Exchange where position is held", default=None)]

    @property
    def total_cost_basis(self) -> float:
        """Total cost basis for the position."""
        return self.cost_basis * self.amount
