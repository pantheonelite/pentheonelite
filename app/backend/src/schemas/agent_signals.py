"""Agent signal schemas for cryptocurrency trading decisions."""

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class CryptoSignalType(StrEnum):
    """Cryptocurrency trading signal types."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class ConfidenceLevel(StrEnum):
    """Confidence level categories."""

    VERY_LOW = "very_low"  # 0-20%
    LOW = "low"  # 21-40%
    MEDIUM = "medium"  # 41-60%
    HIGH = "high"  # 61-80%
    VERY_HIGH = "very_high"  # 81-100%


class CryptoAgentSignal(BaseModel):
    """Base cryptocurrency agent signal structure."""

    signal: Annotated[CryptoSignalType, Field(description="Cryptocurrency trading signal")]
    confidence: Annotated[int, Field(description="Confidence level (0-100)", ge=0, le=100)]
    reasoning: Annotated[str, Field(description="Reasoning for the signal")]

    # Optional metadata
    symbol: Annotated[str | None, Field(description="Specific crypto symbol if applicable", default=None)]
    exchange: Annotated[str | None, Field(description="Exchange name", default=None)]
    agent_id: Annotated[str | None, Field(description="Agent identifier", default=None)]
    timestamp: Annotated[str | None, Field(description="Signal timestamp", default=None)]

    # Additional analysis data
    analysis_data: Annotated[
        dict[str, Any],
        Field(description="Additional analysis data", default_factory=dict),
    ]

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level category."""
        if self.confidence <= 20:
            return ConfidenceLevel.VERY_LOW
        if self.confidence <= 40:
            return ConfidenceLevel.LOW
        if self.confidence <= 60:
            return ConfidenceLevel.MEDIUM
        if self.confidence <= 80:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.VERY_HIGH

    @property
    def is_bullish(self) -> bool:
        """Check if signal is bullish."""
        return self.signal in [CryptoSignalType.BUY, CryptoSignalType.STRONG_BUY]

    @property
    def is_bearish(self) -> bool:
        """Check if signal is bearish."""
        return self.signal in [CryptoSignalType.SELL, CryptoSignalType.STRONG_SELL]

    @property
    def is_neutral(self) -> bool:
        """Check if signal is neutral."""
        return self.signal == CryptoSignalType.HOLD


class CryptoAnalystSignal(CryptoAgentSignal):
    """Cryptocurrency analyst-specific signal with additional fields."""

    # Technical analysis metrics
    technical_score: Annotated[float | None, Field(description="Technical analysis score", default=None)]
    trend_direction: Annotated[str | None, Field(description="Trend direction (up/down/sideways)", default=None)]
    support_level: Annotated[float | None, Field(description="Support level price", default=None)]
    resistance_level: Annotated[float | None, Field(description="Resistance level price", default=None)]
    rsi: Annotated[float | None, Field(description="RSI indicator value", default=None)]
    macd_signal: Annotated[str | None, Field(description="MACD signal (bullish/bearish)", default=None)]

    # Fundamental analysis metrics
    fundamental_score: Annotated[float | None, Field(description="Fundamental analysis score", default=None)]
    market_cap_rank: Annotated[int | None, Field(description="Market cap ranking", default=None)]
    volume_trend: Annotated[str | None, Field(description="Volume trend (increasing/decreasing)", default=None)]
    adoption_metrics: Annotated[dict[str, Any] | None, Field(description="Adoption and usage metrics", default=None)]

    # Sentiment analysis metrics
    sentiment_score: Annotated[float | None, Field(description="Sentiment analysis score", default=None)]
    social_sentiment: Annotated[str | None, Field(description="Social media sentiment", default=None)]
    news_sentiment: Annotated[str | None, Field(description="News sentiment", default=None)]
    fear_greed_index: Annotated[float | None, Field(description="Fear & Greed Index value", default=None)]

    # Risk assessment
    risk_level: Annotated[str | None, Field(description="Risk level assessment (low/medium/high)", default=None)]
    volatility_estimate: Annotated[float | None, Field(description="Estimated volatility", default=None)]
    correlation_risk: Annotated[float | None, Field(description="Correlation with major cryptos", default=None)]

    # Price targets
    target_price: Annotated[float | None, Field(description="Target price", default=None)]
    stop_loss: Annotated[float | None, Field(description="Stop loss price", default=None)]
    take_profit: Annotated[float | None, Field(description="Take profit price", default=None)]


class CryptoRiskSignal(CryptoAgentSignal):
    """Cryptocurrency risk management signal with risk-specific fields."""

    # Risk metrics
    portfolio_risk: Annotated[float | None, Field(description="Portfolio risk level", default=None)]
    position_risk: Annotated[float | None, Field(description="Position-specific risk", default=None)]
    market_risk: Annotated[float | None, Field(description="Market risk exposure", default=None)]
    liquidity_risk: Annotated[float | None, Field(description="Liquidity risk assessment", default=None)]

    # Risk recommendations
    position_size: Annotated[float | None, Field(description="Recommended position size", default=None)]
    max_position_size: Annotated[float | None, Field(description="Maximum recommended position size", default=None)]
    diversification_ratio: Annotated[
        float | None, Field(description="Recommended diversification ratio", default=None)
    ]

    # Risk warnings
    warnings: Annotated[list[str], Field(description="Risk warnings", default_factory=list)]
    alerts: Annotated[list[str], Field(description="Risk alerts", default_factory=list)]


class CryptoPortfolioSignal(CryptoAgentSignal):
    """Cryptocurrency portfolio management signal with portfolio-specific fields."""

    # Portfolio metrics
    target_allocation: Annotated[float | None, Field(description="Target allocation percentage", default=None)]
    current_allocation: Annotated[float | None, Field(description="Current allocation percentage", default=None)]
    rebalance_needed: Annotated[bool, Field(description="Whether rebalancing is needed", default=False)]

    # Trading recommendations
    action: Annotated[
        str | None,
        Field(description="Recommended action (buy/sell/hold)", default=None),
    ]
    amount: Annotated[float | None, Field(description="Recommended amount to trade", default=None)]
    price_target: Annotated[float | None, Field(description="Price target", default=None)]

    # Portfolio optimization
    optimization_score: Annotated[float | None, Field(description="Portfolio optimization score", default=None)]
    diversification_benefit: Annotated[float | None, Field(description="Diversification benefit", default=None)]
    correlation_impact: Annotated[float | None, Field(description="Impact on portfolio correlation", default=None)]


class CryptoTradingSignal(CryptoAgentSignal):
    """Cryptocurrency trading execution signal."""

    # Trading parameters
    order_type: Annotated[str | None, Field(description="Order type (market/limit/stop)", default=None)]
    amount: Annotated[float | None, Field(description="Amount to trade", default=None)]
    price: Annotated[float | None, Field(description="Order price", default=None)]
    stop_price: Annotated[float | None, Field(description="Stop price for stop orders", default=None)]

    # Execution parameters
    exchange: Annotated[str | None, Field(description="Recommended exchange", default=None)]
    slippage_tolerance: Annotated[float | None, Field(description="Maximum acceptable slippage", default=None)]
    time_in_force: Annotated[str | None, Field(description="Time in force (GTC/IOC/FOK)", default=None)]

    # Risk management
    max_loss: Annotated[float | None, Field(description="Maximum acceptable loss", default=None)]
    risk_reward_ratio: Annotated[float | None, Field(description="Risk to reward ratio", default=None)]
