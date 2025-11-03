"""Request schemas for the trading system."""

from typing import Annotated, Any

from pydantic import BaseModel, Field

from .agent_context import CryptoPosition


class GraphNode(BaseModel):
    """Graph node representation."""

    id: Annotated[str, Field(description="Node identifier")]
    type: Annotated[str | None, Field(description="Node type", default=None)]
    data: Annotated[dict[str, Any] | None, Field(description="Node data", default=None)]
    position: Annotated[dict[str, float] | None, Field(description="Node position", default=None)]


class GraphEdge(BaseModel):
    """Graph edge representation."""

    id: Annotated[str, Field(description="Edge identifier")]
    source: Annotated[str, Field(description="Source node ID")]
    target: Annotated[str, Field(description="Target node ID")]
    type: Annotated[str | None, Field(description="Edge type", default=None)]
    data: Annotated[dict[str, Any] | None, Field(description="Edge data", default=None)]


class AgentModelConfig(BaseModel):
    """Agent model configuration."""

    agent_id: Annotated[str, Field(description="Agent identifier")]
    model_name: Annotated[str | None, Field(description="Model name", default=None)]
    model_provider: Annotated[str | None, Field(description="Model provider", default=None)]
    temperature: Annotated[float | None, Field(description="Model temperature", default=None)]
    max_tokens: Annotated[int | None, Field(description="Maximum tokens", default=None)]


class BaseHedgeFundRequest(BaseModel):
    """Base request for hedge fund operations."""

    # Core trading parameters
    tickers: Annotated[list[str], Field(description="List of tickers to analyze")]
    graph_nodes: Annotated[list[GraphNode], Field(description="Workflow graph nodes")]
    graph_edges: Annotated[list[GraphEdge], Field(description="Workflow graph edges")]

    # Model configuration
    agent_models: Annotated[
        list[AgentModelConfig] | None,
        Field(description="Agent model configurations", default=None),
    ]
    model_name: Annotated[str | None, Field(description="Default model name", default="gpt-4")]
    model_provider: Annotated[str | None, Field(description="Default model provider", default="OpenAI")]

    # Portfolio configuration
    margin_requirement: Annotated[float | None, Field(description="Margin requirement", default=0.5)]
    portfolio_positions: Annotated[
        list[CryptoPosition] | None,
        Field(description="Initial portfolio positions", default=None),
    ]

    # Feature flags
    show_reasoning: Annotated[bool, Field(description="Show agent reasoning", default=False)]
    enable_streaming: Annotated[bool, Field(description="Enable streaming", default=False)]

    # Metadata
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class HedgeFundRequest(BaseHedgeFundRequest):
    """Request for live hedge fund operations."""

    # Time parameters
    start_date: Annotated[str | None, Field(description="Analysis start date", default=None)]
    end_date: Annotated[str | None, Field(description="Analysis end date", default=None)]

    # Portfolio parameters
    initial_cash: Annotated[float | None, Field(description="Initial cash amount", default=100000.0)]

    # Risk parameters
    risk_tolerance: Annotated[str | None, Field(description="Risk tolerance level", default="moderate")]
    max_position_size: Annotated[float | None, Field(description="Maximum position size", default=0.1)]

    # Execution parameters
    execution_delay: Annotated[float | None, Field(description="Execution delay in seconds", default=0.0)]
    dry_run: Annotated[bool, Field(description="Dry run mode", default=False)]


class BacktestRequest(BaseHedgeFundRequest):
    """Request for backtesting operations."""

    # Required time parameters for backtesting
    start_date: Annotated[str, Field(description="Backtest start date")]
    end_date: Annotated[str, Field(description="Backtest end date")]

    # Portfolio parameters
    initial_capital: Annotated[float | None, Field(description="Initial capital", default=100000.0)]

    # Backtest-specific parameters
    rebalance_frequency: Annotated[str | None, Field(description="Rebalance frequency", default="daily")]
    transaction_costs: Annotated[float | None, Field(description="Transaction costs", default=0.001)]
    slippage: Annotated[float | None, Field(description="Slippage factor", default=0.0)]

    # Performance tracking
    benchmark_ticker: Annotated[str | None, Field(description="Benchmark ticker", default="SPY")]
    risk_free_rate: Annotated[float | None, Field(description="Risk-free rate", default=0.02)]

    # Output configuration
    save_results: Annotated[bool, Field(description="Save backtest results", default=True)]
    output_format: Annotated[str | None, Field(description="Output format", default="json")]
    include_plots: Annotated[bool, Field(description="Include performance plots", default=False)]


class BaseCryptoHedgeFundRequest(BaseModel):
    """Base request for crypto hedge fund operations."""

    # Core trading parameters
    symbols: Annotated[list[str], Field(description="List of crypto symbols to trade")]
    start_date: Annotated[str | None, Field(description="Start date for analysis", default=None)]
    end_date: Annotated[str | None, Field(description="End date for analysis", default=None)]

    # Portfolio configuration
    initial_cash: Annotated[float, Field(description="Initial cash amount", default=100000.0)]
    portfolio_positions: Annotated[
        list[CryptoPosition] | None,
        Field(description="Initial portfolio positions", default=None),
    ]

    # Graph configuration
    graph_nodes: Annotated[list[GraphNode], Field(description="Graph nodes")]
    graph_edges: Annotated[list[GraphEdge], Field(description="Graph edges")]

    # Model configuration
    model_name: Annotated[str | None, Field(description="LLM model name", default=None)]
    model_provider: Annotated[str | None, Field(description="LLM model provider", default=None)]
    agent_model_configs: Annotated[
        list[AgentModelConfig] | None,
        Field(description="Per-agent model configurations", default=None),
    ]

    # Execution configuration
    show_reasoning: Annotated[bool, Field(description="Show agent reasoning", default=True)]
    enable_streaming: Annotated[bool, Field(description="Enable streaming responses", default=False)]

    # Metadata
    metadata: Annotated[dict[str, Any] | None, Field(description="Additional metadata", default=None)]
