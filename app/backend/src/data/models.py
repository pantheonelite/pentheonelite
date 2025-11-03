"""Data models for cryptocurrency trading and analysis."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CryptoPrice(BaseModel):
    """Cryptocurrency price data."""

    open: float
    close: float
    high: float
    low: float
    volume: float
    timestamp: datetime
    symbol: str
    exchange: str


class CryptoPriceResponse(BaseModel):
    """Response containing cryptocurrency price data."""

    symbol: str
    prices: list[CryptoPrice]
    exchange: str


class CryptoMetrics(BaseModel):
    """Cryptocurrency market metrics."""

    symbol: str
    exchange: str
    timestamp: datetime
    market_cap: float | None = None
    volume_24h: float | None = None
    price_change_24h: float | None = None
    price_change_percent_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    dominance: float | None = None  # Market dominance percentage


class CryptoMetricsResponse(BaseModel):
    """Response containing cryptocurrency metrics."""

    metrics: list[CryptoMetrics]


class CryptoNews(BaseModel):
    """Cryptocurrency news article."""

    symbol: str | None = None
    title: str
    author: str | None = None
    source: str
    published_date: datetime
    url: str
    content: str | None = None
    sentiment: str | None = None
    sentiment_score: float | None = None


class CryptoNewsResponse(BaseModel):
    """Response containing cryptocurrency news."""

    news: list[CryptoNews]


class CryptoInfo(BaseModel):
    """Cryptocurrency information."""

    symbol: str
    name: str
    description: str | None = None
    website: str | None = None
    whitepaper: str | None = None
    github: str | None = None
    twitter: str | None = None
    telegram: str | None = None
    discord: str | None = None
    reddit: str | None = None
    blockchain: str | None = None
    consensus_mechanism: str | None = None
    max_supply: float | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    launch_date: datetime | None = None
    category: str | None = None  # e.g., "DeFi", "Layer 1", "NFT", etc.


class CryptoInfoResponse(BaseModel):
    """Response containing cryptocurrency information."""

    info: CryptoInfo


class CryptoPosition(BaseModel):
    """Cryptocurrency position in portfolio."""

    symbol: str
    amount: float = 0.0  # Amount of crypto held
    cost_basis: float = 0.0  # Average cost per unit
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    exchange: str | None = None


class CryptoPortfolio(BaseModel):
    """Cryptocurrency portfolio."""

    positions: dict[str, CryptoPosition] = Field(default_factory=dict)
    total_cash: float = 0.0
    total_value: float = 0.0
    total_pnl: float = 0.0
    base_currency: str = "USDT"  # Base currency for valuation


class CryptoSignal(BaseModel):
    """Cryptocurrency trading signal."""

    signal: str | None = None  # "buy", "sell", "hold", "strong_buy", "strong_sell"
    confidence: float | None = None  # 0-100
    reasoning: dict | str | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size: float | None = None  # Recommended position size
    risk_level: str | None = None  # "low", "medium", "high"


class CryptoSymbolAnalysis(BaseModel):
    """Analysis for a specific cryptocurrency symbol."""

    symbol: str
    exchange: str
    analyst_signals: dict[str, CryptoSignal] = Field(default_factory=dict)
    technical_analysis: dict[str, Any] = Field(default_factory=dict)
    fundamental_analysis: dict[str, Any] = Field(default_factory=dict)
    sentiment_analysis: dict[str, Any] = Field(default_factory=dict)
    risk_assessment: dict[str, Any] = Field(default_factory=dict)


class CryptoAgentStateData(BaseModel):
    """State data for crypto trading agents."""

    symbols: list[str]  # List of crypto symbols to analyze
    exchanges: list[str] = Field(default_factory=lambda: ["binance", "coinbase", "kraken"])
    portfolio: CryptoPortfolio
    start_date: str
    end_date: str
    symbol_analyses: dict[str, CryptoSymbolAnalysis] = Field(default_factory=dict)
    market_data: dict[str, Any] = Field(default_factory=dict)
    news_data: dict[str, Any] = Field(default_factory=dict)


class CryptoAgentStateMetadata(BaseModel):
    """Metadata for crypto trading agent state."""

    show_reasoning: bool = False
    analysis_type: str = "comprehensive"  # "price_only", "technical", "fundamental", "sentiment", "comprehensive"
    risk_tolerance: str = "medium"  # "low", "medium", "high"
    trading_strategy: str = "swing"  # "scalping", "day", "swing", "position"
    model_config = {"extra": "allow"}


class CryptoOrderBook(BaseModel):
    """Cryptocurrency order book data."""

    symbol: str
    exchange: str
    timestamp: datetime
    bids: list[list[float]] = Field(description="List of [price, quantity] for bids")
    asks: list[list[float]] = Field(description="List of [price, quantity] for asks")
    spread: float | None = None
    spread_percent: float | None = None


class CryptoTrade(BaseModel):
    """Cryptocurrency trade execution."""

    symbol: str
    exchange: str
    side: str  # "buy" or "sell"
    amount: float
    price: float
    timestamp: datetime
    order_id: str | None = None
    fee: float | None = None
    fee_currency: str | None = None


class CryptoOrder(BaseModel):
    """Cryptocurrency order."""

    symbol: str
    exchange: str
    side: str  # "buy" or "sell"
    type: str  # "market", "limit", "stop", "stop_limit"
    amount: float
    price: float | None = None
    stop_price: float | None = None
    status: str = "pending"  # "pending", "filled", "cancelled", "rejected"
    order_id: str | None = None
    timestamp: datetime
    filled_amount: float = 0.0
    remaining_amount: float = 0.0
    average_price: float | None = None
    fee: float | None = None
    fee_currency: str | None = None


class CryptoPerformanceMetrics(BaseModel):
    """Cryptocurrency trading performance metrics."""

    total_return: float
    annualized_return: float
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    volatility: float
    beta: float | None = None  # Beta vs crypto market index
    alpha: float | None = None  # Alpha vs crypto market index


class CryptoBacktestResult(BaseModel):
    """Cryptocurrency backtest result."""

    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    performance_metrics: CryptoPerformanceMetrics
    trades: list[CryptoTrade]
    portfolio_history: list[dict[str, Any]]
    benchmark_return: float | None = None
    benchmark_symbol: str | None = None
