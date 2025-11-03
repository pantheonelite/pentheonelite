from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

import pandas as pd


class Action(str, Enum):
    """Trading actions enumeration."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    # Note: Removed SHORT and COVER for crypto as they're not commonly used
    # in crypto spot trading. These can be added back if needed for margin trading.


# Backward-compatible alias
ActionLiteral = Literal["buy", "sell", "hold"]


class PositionState(TypedDict):
    """Represents per-ticker position state in the portfolio."""

    long: int
    short: int
    long_cost_basis: float
    short_cost_basis: float
    short_margin_used: float


class TickerRealizedGains(TypedDict):
    """Realized PnL per side for a single ticker."""

    long: float
    short: float


class PortfolioSnapshot(TypedDict):
    """Snapshot of portfolio state.

    The structure mirrors the existing dict used by the current Backtester
    to ensure drop-in compatibility during incremental refactors.
    """

    cash: float
    margin_used: float
    margin_requirement: float
    positions: dict[str, PositionState]
    realized_gains: dict[str, TickerRealizedGains]


# DataFrame alias for clarity in interfaces
PriceDataFrame = pd.DataFrame


class AgentDecision(TypedDict):
    """Agent trading decision structure."""

    action: ActionLiteral
    quantity: float


AgentDecisions = dict[str, AgentDecision]


# Analyst signal payloads can vary by agent; keep as loose dicts
AnalystSignal = dict[str, Any]
AgentSignals = dict[str, dict[str, AnalystSignal]]


class AgentOutput(TypedDict):
    """Agent output structure containing decisions and signals."""

    decisions: AgentDecisions
    analyst_signals: AgentSignals


# Use functional style to allow keys with spaces to mirror current code
PortfolioValuePoint = TypedDict(
    "PortfolioValuePoint",
    {
        "Date": datetime,
        "Portfolio Value": float,
        "Long Exposure": float,
        "Short Exposure": float,
        "Gross Exposure": float,
        "Net Exposure": float,
        "Long/Short Ratio": float,
    },
    total=False,
)


class PerformanceMetrics(TypedDict, total=False):
    """Performance metrics computed over the equity curve.

    Keys are aligned with the current implementation in src/backtester.py.
    Values are optional to support progressive calculation over time.
    """

    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float | None
    max_drawdown_date: str | None
    long_short_ratio: float | None
    gross_exposure: float | None
    net_exposure: float | None
