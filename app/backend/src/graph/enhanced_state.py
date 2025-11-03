"""Enhanced state management for LangGraph-based crypto trading workflow."""

import operator
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage


class SignalType(str, Enum):
    """Trading signal types."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """Risk level classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PriceData:
    """Price data structure with historical data support."""

    symbol: str
    price: float
    volume: float
    change_24h: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    # Historical data fields (optional)
    historical_klines: list[Any] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    timeframe: str | None = None


@dataclass
class TechnicalSignal:
    """Technical analysis signal."""

    signal: SignalType
    confidence: float
    indicators: dict[str, Any]
    reasoning: str
    timestamp: datetime


@dataclass
class SentimentSignal:
    """Sentiment analysis signal."""

    signal: SignalType
    confidence: float
    sentiment_score: float
    news_sentiment: float
    social_sentiment: float
    reasoning: str
    timestamp: datetime


@dataclass
class RiskAssessment:
    """Risk assessment data."""

    risk_level: RiskLevel
    portfolio_risk: float
    position_risk: float
    market_risk: float
    liquidity_risk: float
    max_position_size: float
    stop_loss: float
    reasoning: str
    timestamp: datetime


@dataclass
class TradingDecision:
    """Trading decision data."""

    symbol: str
    action: str  # "buy", "sell", "hold"
    quantity: float
    price: float
    confidence: float
    reasoning: str
    risk_level: RiskLevel
    timestamp: datetime


def merge_dicts_reducer(existing: dict | None, update: dict) -> dict:
    """
    Custom reducer to merge dictionaries from parallel nodes.

    Parameters
    ----------
    existing : dict | None
        Existing dictionary value (None if first update)
    update : dict
        New dictionary to merge

    Returns
    -------
    dict
        Merged dictionary
    """
    if existing is None:
        return update
    return {**existing, **update}


def merge_lists_reducer(existing: list | None, update: list) -> list:
    """
    Custom reducer to concatenate lists from parallel nodes.

    Parameters
    ----------
    existing : list | None
        Existing list value (None if first update)
    update : list
        New list to concatenate

    Returns
    -------
    list
        Concatenated list
    """
    if existing is None:
        return update
    return existing + update


class CryptoAgentState(TypedDict, total=False):
    """
    Enhanced state for crypto trading workflow with parallel execution support.

    State fields are optimized for LangGraph's parallel execution model:
    - Fields updated by parallel nodes use reducers (Annotated with reducer functions)
    - Single-writer fields don't need reducers (e.g., price_data from data_collection only)
    - operator.add is used for accumulating messages and lists
    - merge_dicts_reducer is used for merging dictionaries from parallel nodes
    """

    # LangGraph required fields
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Input configuration (single-writer: set once at initialization)
    symbols: list[str]
    timeframe: str
    start_date: datetime
    end_date: datetime
    model_name: str
    model_provider: str

    # Market data (single-writer: updated only by data_collection node)
    price_data: dict[str, Any]
    volume_data: dict[str, Any]
    news_data: dict[str, Any]
    social_data: dict[str, Any]

    # Analysis results (parallel writers: use reducers to avoid conflicts)
    # These fields are updated by parallel nodes (technical_analysis, sentiment_analysis, persona_execution)
    technical_signals: Annotated[dict[str, Any], merge_dicts_reducer]
    sentiment_signals: Annotated[dict[str, Any], merge_dicts_reducer]
    persona_signals: Annotated[dict[str, Any], merge_dicts_reducer]
    persona_consensus: dict[str, Any]  # Single-writer: updated only by merge_analysis
    risk_assessments: dict[str, Any]  # Single-writer: updated only by risk_assessment

    # Trading decisions (single-writer: updated only by portfolio_management)
    trading_decisions: dict[str, Any]
    portfolio_allocations: dict[str, float]

    # Workflow metadata
    execution_timestamp: datetime
    current_node: str
    progress_percentage: float
    error_messages: Annotated[list[str], merge_lists_reducer]  # Parallel nodes can add errors

    # Agent reasoning (parallel writers: use reducer)
    agent_reasoning: Annotated[dict[str, str], merge_dicts_reducer]
    confidence_scores: Annotated[dict[str, float], merge_dicts_reducer]

    # Portfolio state (single-writer: updated only by portfolio_management)
    portfolio: dict[str, float]
    total_value: float


def create_initial_state(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    model_name: str = "gpt-4o-mini",
    model_provider: str = "LiteLLM",
    timeframe: str = "1h",
    portfolio: dict[str, Any] | None = None,
) -> CryptoAgentState:
    """
    Create initial state for the crypto trading workflow.

    Parameters
    ----------
    symbols : List[str]
        List of crypto symbols to analyze
    start_date : datetime
        Start date for analysis
    end_date : datetime
        End date for analysis
    model_name : str
        LLM model name
    model_provider : str
        LLM provider
    timeframe : str
        Analysis timeframe

    Returns
    -------
    CryptoAgentState
        Initial state for the workflow
    """
    return CryptoAgentState(
        # LangGraph required field
        messages=[HumanMessage(content="Crypto trading workflow initialized")],
        # Input configuration
        symbols=symbols,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        model_name=model_name,
        model_provider=model_provider,
        # Market data (empty initially)
        price_data={},
        volume_data={},
        news_data={},
        social_data={},
        # Analysis results (empty initially)
        technical_signals={},
        sentiment_signals={},
        persona_signals={},
        persona_consensus={},
        risk_assessments={},
        # Trading decisions (empty initially)
        trading_decisions={},
        portfolio_allocations={},
        # Workflow metadata
        execution_timestamp=datetime.now(),
        current_node="start",
        progress_percentage=0.0,
        error_messages=[],
        # Agent reasoning (empty initially)
        agent_reasoning={},
        confidence_scores={},
        # Portfolio state (empty initially)
        portfolio=portfolio or {},
        total_value=10000.0,
    )


def update_state_progress(state: CryptoAgentState, node_name: str, progress: float) -> CryptoAgentState:
    """
    Update the progress of the workflow state.

    Parameters
    ----------
    state : CryptoAgentState
        Current state
    node_name : str
        Name of the current node
    progress : float
        Progress percentage (0.0 to 1.0)

    Returns
    -------
    CryptoAgentState
        Updated state
    """
    state["current_node"] = node_name
    state["progress_percentage"] = min(1.0, max(0.0, progress))
    return state


def add_error_message(state: CryptoAgentState, error: str) -> CryptoAgentState:
    """
    Add an error message to the state.

    Parameters
    ----------
    state : CryptoAgentState
        Current state
    error : str
        Error message to add

    Returns
    -------
    CryptoAgentState
        Updated state
    """
    state["error_messages"].append(f"{datetime.now().isoformat()}: {error}")
    return state


def get_state_summary(state: CryptoAgentState) -> dict[str, Any]:
    """
    Get a summary of the current state.

    Parameters
    ----------
    state : CryptoAgentState
        Current state

    Returns
    -------
    Dict[str, Any]
        State summary
    """
    return {
        "current_node": state["current_node"],
        "progress_percentage": state["progress_percentage"],
        "symbols_count": len(state["symbols"]),
        "price_data_count": len(state["price_data"]),
        "technical_signals_count": len(state["technical_signals"]),
        "sentiment_signals_count": len(state["sentiment_signals"]),
        "risk_assessments_count": len(state["risk_assessments"]),
        "trading_decisions_count": len(state["trading_decisions"]),
        "error_count": len(state["error_messages"]),
        "total_value": state["total_value"],
    }
