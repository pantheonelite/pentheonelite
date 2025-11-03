"""Schemas for the trading system."""

from .agent_context import AgentContext, BaseAgentContext, TradingContext
from .agent_signals import CryptoAgentSignal, CryptoSignalType
from .requests import BacktestRequest, BaseHedgeFundRequest, HedgeFundRequest
from .responses import PerformanceMetrics, PortfolioPosition, TradingDecision

__all__ = [
    "AgentContext",
    "BacktestRequest",
    "BaseAgentContext",
    "BaseHedgeFundRequest",
    "CryptoAgentSignal",
    "CryptoSignalType",
    "HedgeFundRequest",
    "PerformanceMetrics",
    "PortfolioPosition",
    "TradingContext",
    "TradingDecision",
]
