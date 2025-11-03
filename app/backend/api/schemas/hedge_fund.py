from datetime import datetime, timedelta
from typing import Any

from app.backend.services.graph import GraphService
from app.backend.src.llm.base_client import ModelProvider
from pydantic import BaseModel, Field, field_validator

from .graph import GraphEdge, GraphNode


class AgentModelConfig(BaseModel):
    """Configuration for agent model settings."""

    agent_id: str
    model_name: str | None = None
    model_provider: ModelProvider | None = None


class PortfolioPosition(BaseModel):
    """Represents a position in the portfolio."""

    ticker: str
    quantity: float
    trade_price: float

    @field_validator("trade_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Trade price must be positive!")
        return v


class HedgeFundResponse(BaseModel):
    """Response from hedge fund simulation."""

    decisions: dict
    analyst_signals: dict


class BaseHedgeFundRequest(BaseModel):
    tickers: list[str]
    graph_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]
    agent_models: list[AgentModelConfig] | None = None
    model_name: str | None = "gpt-4.1"
    model_provider: ModelProvider | None = ModelProvider.OPENAI
    margin_requirement: float = 0.0
    portfolio_positions: list[PortfolioPosition] | None = None
    api_keys: dict[str, str] | None = None

    def get_agent_ids(self) -> list[str]:
        """Extract agent IDs from graph structure."""
        return [node.id for node in self.graph_nodes]

    def get_agent_model_config(self, agent_id: str) -> tuple[str, ModelProvider]:
        """Get model configuration for a specific agent."""
        if self.agent_models:
            graph_service = GraphService()
            base_agent_key = graph_service.extract_base_agent_key(agent_id)

            for config in self.agent_models:
                config_base_key = graph_service.extract_base_agent_key(config.agent_id)
                if config.agent_id == agent_id or config_base_key == base_agent_key:
                    model_name = config.model_name or self.model_name
                    model_provider = config.model_provider or self.model_provider
                    if model_name and model_provider:
                        return (model_name, model_provider)
        if self.model_name and self.model_provider:
            return (self.model_name, self.model_provider)
        raise ValueError("No valid model configuration found")


class BacktestRequest(BaseHedgeFundRequest):
    start_date: str
    end_date: str
    initial_capital: float = 100000.0


class BacktestDayResult(BaseModel):
    date: str
    portfolio_value: float
    cash: float
    decisions: dict[str, Any]
    executed_trades: dict[str, int]
    analyst_signals: dict[str, Any]
    current_prices: dict[str, float]
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    long_short_ratio: float | None = None


class BacktestPerformanceMetrics(BaseModel):
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float | None = None
    max_drawdown_date: str | None = None
    long_short_ratio: float | None = None
    gross_exposure: float | None = None
    net_exposure: float | None = None


class BacktestResponse(BaseModel):
    results: list[BacktestDayResult]
    performance_metrics: BacktestPerformanceMetrics
    final_portfolio: dict[str, Any]


class HedgeFundRequest(BaseHedgeFundRequest):
    end_date: str | None = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    start_date: str | None = None
    initial_cash: float = 100000.0

    def get_start_date(self) -> str:
        """Calculate start date if not provided."""
        if self.start_date:
            return self.start_date
        return (datetime.strptime(self.end_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
