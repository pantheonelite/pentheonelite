"""Workflow result handler for crypto trading workflow."""

import json
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class WorkflowResult:
    """
    Represents the result of a crypto trading workflow execution.

    This class provides structured access to all workflow outputs including
    technical signals, risk assessments, sentiment analysis, and trading decisions.
    """

    def __init__(self, raw_result: dict[str, Any]):
        """
        Initialize a WorkflowResult from raw workflow output.

        Parameters
        ----------
        raw_result : dict[str, Any]
            Raw result dictionary from workflow execution
        """
        self.raw_result = raw_result

        # Extract different types of signals
        self.technical_signals = raw_result.get("technical_signals", {})
        self.risk_assessments = raw_result.get("risk_assessments", {})
        self.sentiment_signals = raw_result.get("sentiment_signals", {})
        self.trading_decisions = raw_result.get("trading_decisions", {})
        self.portfolio_signals = raw_result.get("portfolio_signals", {})
        self.price_data = raw_result.get("price_data", {})

        # Extract metadata
        self.execution_timestamp = raw_result.get("execution_timestamp", "")
        self.progress_percentage = raw_result.get("progress_percentage", 0.0)
        self.error_messages = raw_result.get("error_messages", [])
        self.portfolio_allocations = raw_result.get("portfolio_allocations", {})

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to dictionary format.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the workflow result
        """
        return {
            "technical_signals": self.technical_signals,
            "risk_assessments": self.risk_assessments,
            "sentiment_signals": self.sentiment_signals,
            "trading_decisions": self.trading_decisions,
            "portfolio_signals": self.portfolio_signals,
            "price_data": self.price_data,
            "portfolio_allocations": self.portfolio_allocations,
            "metadata": {
                "execution_timestamp": self.execution_timestamp,
                "progress_percentage": self.progress_percentage,
                "error_messages": self.error_messages,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert result to JSON string.

        Parameters
        ----------
        indent : int
            JSON indentation level

        Returns
        -------
        str
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def get_all_signals_for_symbol(self, symbol: str) -> dict[str, Any]:
        """
        Get all signals for a specific symbol.

        Parameters
        ----------
        symbol : str
            Crypto symbol to get signals for

        Returns
        -------
        dict[str, Any]
            Dictionary containing all signals for the symbol
        """
        return {
            "technical": self._extract_symbol_signals(self.technical_signals, symbol),
            "risk": self._extract_symbol_signals(self.risk_assessments, symbol),
            "sentiment": self._extract_symbol_signals(self.sentiment_signals, symbol),
            "trading": self._extract_symbol_signals(self.trading_decisions, symbol),
        }

    def _extract_symbol_signals(self, signals: dict[str, Any], symbol: str) -> dict[str, Any]:
        """Extract signals for a specific symbol from agent signals."""
        symbol_signals = {}
        for agent, data in signals.items():
            if isinstance(data, dict) and symbol in data:
                symbol_signals[agent] = data[symbol]
        return symbol_signals

    def print_summary(self):
        """Print a formatted summary of the workflow results."""
        # Technical Signals
        if self.technical_signals:
            self._print_signals(self.technical_signals, "Technical")

        # Risk Assessments
        if self.risk_assessments:
            self._print_signals(self.risk_assessments, "Risk")

        # Sentiment Signals
        if self.sentiment_signals:
            self._print_signals(self.sentiment_signals, "Sentiment")

        # Trading Decisions
        if self.trading_decisions:
            self._print_signals(self.trading_decisions, "Trading")

    def _print_signals(self, signals: dict[str, Any], signal_type: str):  # noqa: ARG002
        """Print formatted signals for all agents."""
        for data in signals.values():
            if isinstance(data, dict):
                for signal in data.values():
                    if isinstance(signal, dict):
                        signal.get("action", signal.get("signal", "N/A"))
                        signal.get("confidence", 0)
                        signal.get("reasoning", "")[:80]
                    else:
                        pass

    def get_portfolio_allocation_table(self) -> list[list[str]]:
        """
        Get portfolio allocation data formatted for table display.

        Returns
        -------
        list[list[str]]
            Table data for portfolio allocations
        """
        table_data = []
        for agent, allocations in self.portfolio_allocations.items():
            if isinstance(allocations, dict):
                for symbol, allocation in allocations.items():
                    table_data.append(
                        [
                            agent,
                            symbol,
                            allocation.get("amount", 0),
                            allocation.get("percentage", 0),
                        ]
                    )
        return table_data

    def has_errors(self) -> bool:
        """
        Check if workflow execution had errors.

        Returns
        -------
        bool
            True if there are error messages, False otherwise
        """
        return len(self.error_messages) > 0

    def get_summary_statistics(self) -> dict[str, Any]:
        """
        Get summary statistics about the workflow execution.

        Returns
        -------
        dict[str, Any]
            Dictionary containing summary statistics
        """
        # Count signals by type
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for signals in [
            self.technical_signals,
            self.risk_assessments,
            self.sentiment_signals,
        ]:
            for agent_data in signals.values():
                if isinstance(agent_data, dict):
                    for signal in agent_data.values():
                        if isinstance(signal, dict):
                            action = signal.get("action", signal.get("signal", "")).upper()
                            if action in ["BUY", "STRONG_BUY"]:
                                buy_count += 1
                            elif action in ["SELL", "STRONG_SELL"]:
                                sell_count += 1
                            elif action == "HOLD":
                                hold_count += 1

        return {
            "total_signals": buy_count + sell_count + hold_count,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "hold_signals": hold_count,
            "has_errors": self.has_errors(),
            "error_count": len(self.error_messages),
            "progress": self.progress_percentage,
        }
