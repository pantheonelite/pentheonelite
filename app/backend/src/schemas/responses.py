"""Response schemas for the trading system."""

from typing import Annotated, Any

from pydantic import BaseModel, Field


class TradingDecision(BaseModel):
    """Trading decision for a specific ticker."""

    ticker: Annotated[str, Field(description="Stock ticker symbol")]
    action: Annotated[str, Field(description="Trading action (buy/sell/hold/short/cover)")]
    quantity: Annotated[int, Field(description="Quantity to trade", default=0)]
    confidence: Annotated[float, Field(description="Confidence level (0-100)", ge=0, le=100)]
    reasoning: Annotated[str, Field(description="Reasoning for the decision")]

    # Price information
    current_price: Annotated[float | None, Field(description="Current market price", default=None)]
    target_price: Annotated[float | None, Field(description="Target price", default=None)]
    stop_loss: Annotated[float | None, Field(description="Stop loss price", default=None)]

    # Risk metrics
    risk_score: Annotated[float | None, Field(description="Risk score", default=None)]
    position_size: Annotated[float | None, Field(description="Recommended position size", default=None)]

    # Additional metadata
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class CryptoTradingDecision(BaseModel):
    """Trading decision for a specific crypto symbol."""

    symbol: Annotated[str, Field(description="Crypto symbol (e.g., BTC/USDT)")]
    action: Annotated[str, Field(description="Trading action (buy/sell/hold)")]
    quantity: Annotated[float, Field(description="Amount to trade", default=0.0)]
    confidence: Annotated[float, Field(description="Confidence level (0-100)", ge=0, le=100)]
    reasoning: Annotated[str, Field(description="Reasoning for the decision")]

    # Price information
    current_price: Annotated[float | None, Field(description="Current market price", default=None)]
    target_price: Annotated[float | None, Field(description="Target price", default=None)]
    stop_loss: Annotated[float | None, Field(description="Stop loss price", default=None)]

    # Risk metrics
    risk_score: Annotated[float | None, Field(description="Risk score", default=None)]
    position_size: Annotated[float | None, Field(description="Recommended position size", default=None)]

    # Additional metadata
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class PortfolioPosition(BaseModel):
    """Portfolio position representation."""

    ticker: Annotated[str, Field(description="Stock ticker symbol")]
    long_shares: Annotated[int, Field(description="Long position shares", default=0)]
    short_shares: Annotated[int, Field(description="Short position shares", default=0)]
    long_cost_basis: Annotated[float, Field(description="Long position cost basis", default=0.0)]
    short_cost_basis: Annotated[float, Field(description="Short position cost basis", default=0.0)]
    short_margin_used: Annotated[float, Field(description="Margin used for short position", default=0.0)]

    # Current values
    current_price: Annotated[float | None, Field(description="Current market price", default=None)]
    market_value: Annotated[float | None, Field(description="Current market value", default=None)]
    unrealized_pnl: Annotated[float | None, Field(description="Unrealized P&L", default=None)]

    @property
    def net_shares(self) -> int:
        """Net position (long - short)."""
        return self.long_shares - self.short_shares

    @property
    def total_cost_basis(self) -> float:
        """Total cost basis for both positions."""
        return self.long_cost_basis + self.short_cost_basis


class PerformanceMetrics(BaseModel):
    """Performance metrics for portfolio or strategy."""

    # Return metrics
    total_return: Annotated[float, Field(description="Total return percentage")]
    annualized_return: Annotated[float, Field(description="Annualized return percentage")]
    cumulative_return: Annotated[float, Field(description="Cumulative return percentage")]

    # Risk metrics
    volatility: Annotated[float, Field(description="Volatility (standard deviation)")]
    sharpe_ratio: Annotated[float | None, Field(description="Sharpe ratio", default=None)]
    sortino_ratio: Annotated[float | None, Field(description="Sortino ratio", default=None)]
    max_drawdown: Annotated[float, Field(description="Maximum drawdown percentage")]

    # Additional metrics
    win_rate: Annotated[float | None, Field(description="Win rate percentage", default=None)]
    profit_factor: Annotated[float | None, Field(description="Profit factor", default=None)]
    calmar_ratio: Annotated[float | None, Field(description="Calmar ratio", default=None)]

    # Benchmark comparison
    alpha: Annotated[float | None, Field(description="Alpha vs benchmark", default=None)]
    beta: Annotated[float | None, Field(description="Beta vs benchmark", default=None)]
    information_ratio: Annotated[float | None, Field(description="Information ratio", default=None)]

    # Exposure metrics
    gross_exposure: Annotated[float | None, Field(description="Gross exposure", default=None)]
    net_exposure: Annotated[float | None, Field(description="Net exposure", default=None)]
    long_short_ratio: Annotated[float | None, Field(description="Long/short ratio", default=None)]


class TradingResult(BaseModel):
    """Complete trading result for a session."""

    # Core results
    decisions: Annotated[dict[str, TradingDecision], Field(description="Trading decisions by ticker")]
    analyst_signals: Annotated[dict[str, dict[str, Any]], Field(description="Analyst signals")]

    # Portfolio information
    final_portfolio: Annotated[dict[str, Any], Field(description="Final portfolio state")]
    performance_metrics: Annotated[
        PerformanceMetrics | None,
        Field(description="Performance metrics", default=None),
    ]

    # Execution information
    execution_time: Annotated[float | None, Field(description="Total execution time in seconds", default=None)]
    total_trades: Annotated[int, Field(description="Total number of trades", default=0)]
    successful_trades: Annotated[int, Field(description="Number of successful trades", default=0)]

    # Metadata
    session_id: Annotated[str | None, Field(description="Session identifier", default=None)]
    timestamp: Annotated[str | None, Field(description="Result timestamp", default=None)]
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class BacktestResult(BaseModel):
    """Backtest result with detailed performance analysis."""

    # Time period
    start_date: Annotated[str, Field(description="Backtest start date")]
    end_date: Annotated[str, Field(description="Backtest end date")]
    total_days: Annotated[int, Field(description="Total trading days")]

    # Portfolio evolution
    daily_returns: Annotated[list[float], Field(description="Daily returns")]
    portfolio_values: Annotated[list[float], Field(description="Portfolio values over time")]
    cash_history: Annotated[list[float], Field(description="Cash balance over time")]

    # Performance metrics
    performance_metrics: Annotated[PerformanceMetrics, Field(description="Performance metrics")]

    # Trade history
    trade_history: Annotated[list[dict[str, Any]], Field(description="Detailed trade history")]

    # Risk analysis
    risk_metrics: Annotated[dict[str, Any], Field(description="Risk analysis metrics")]

    # Benchmark comparison
    benchmark_returns: Annotated[list[float] | None, Field(description="Benchmark returns", default=None)]
    benchmark_metrics: Annotated[
        PerformanceMetrics | None,
        Field(description="Benchmark performance", default=None),
    ]

    # Final state
    final_portfolio: Annotated[dict[str, Any], Field(description="Final portfolio state")]

    # Metadata
    backtest_id: Annotated[str | None, Field(description="Backtest identifier", default=None)]
    created_at: Annotated[str | None, Field(description="Creation timestamp", default=None)]
    metadata: Annotated[dict[str, Any], Field(description="Additional metadata", default_factory=dict)]


class CryptoTradingResult(BaseModel):
    """Crypto trading result containing decisions and analysis."""

    decisions: Annotated[
        dict[str, CryptoTradingDecision],
        Field(description="Trading decisions by symbol"),
    ]
    analyst_signals: Annotated[dict[str, Any], Field(description="Analyst signals and analysis")]
    final_portfolio: Annotated[dict[str, Any], Field(description="Final portfolio state")]
    execution_time: Annotated[float, Field(description="Execution time in seconds")]
    session_id: Annotated[str, Field(description="Session identifier")]
    timestamp: Annotated[str, Field(description="Result timestamp")]
    metadata: Annotated[dict[str, Any] | None, Field(description="Additional metadata", default=None)]
