"""Crypto backtest service using the refactored backtesting system."""

import asyncio
from collections.abc import Callable
from typing import Any

import structlog
from app.backend.src.backtesting import BacktestEngine

logger = structlog.get_logger(__name__)


class CryptoBacktestService:
    """
    Crypto backtesting service that uses the refactored backtesting system.
    Integrates with the new crypto agent architecture.
    """

    def __init__(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        model_name: str = "gpt-4.1",
        model_provider: str = "OpenAI",
        selected_analysts: list[str] | None = None,
    ):
        """
        Initialize the crypto backtest service.

        :param symbols: List of crypto symbols to backtest.
        :param start_date: Start date string (YYYY-MM-DD).
        :param end_date: End date string (YYYY-MM-DD).
        :param initial_capital: Starting portfolio cash.
        :param model_name: Which LLM model name to use.
        :param model_provider: Which LLM provider.
        :param selected_analysts: List of analyst agents to use.
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.model_name = model_name
        self.model_provider = model_provider
        self.selected_analysts = selected_analysts or ["crypto_analyst_agent"]

        # Initialize the backtest engine
        self.engine = BacktestEngine(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            model_name=model_name,
            model_provider=model_provider,
            selected_analysts=selected_analysts,
        )

    async def arun_backtest(self, progress_callback: Callable | None = None) -> dict[str, Any]:
        """Run the crypto backtest asynchronously with optional progress callbacks."""
        try:
            # Run the backtest in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run_backtest_with_progress, progress_callback)
        except Exception:
            logger.exception("Error running crypto backtest")
            return {
                "results": [],
                "performance_metrics": {},
                "portfolio_values": [],
                "final_portfolio": {},
            }

    def _run_backtest_with_progress(self, progress_callback: Callable | None = None) -> dict[str, Any]:
        """Run the backtest with progress callbacks."""
        # Run the backtest
        performance_metrics = self.engine.run_backtest()
        portfolio_values = self.engine.get_portfolio_values()

        # Convert portfolio values to the expected format
        results = []
        for i, pv in enumerate(portfolio_values):
            # Send progress update if callback provided
            if progress_callback:
                progress_callback(
                    {
                        "type": "progress",
                        "current_date": pv["Date"].strftime("%Y-%m-%d"),
                        "progress": (i + 1) / len(portfolio_values),
                        "total_dates": len(portfolio_values),
                        "current_step": i + 1,
                    }
                )

            # Create a simplified result for this date
            date_result = {
                "date": pv["Date"].strftime("%Y-%m-%d"),
                "portfolio_value": pv["Portfolio Value"],
                "cash": pv.get("Cash", 0.0),
                "decisions": {},  # Will be populated by the engine
                "executed_trades": {},
                "analyst_signals": {},
                "current_prices": {},
                "long_exposure": pv.get("Long Exposure", 0.0),
                "short_exposure": pv.get("Short Exposure", 0.0),
                "gross_exposure": pv.get("Gross Exposure", 0.0),
                "net_exposure": pv.get("Net Exposure", 0.0),
                "long_short_ratio": pv.get("Long/Short Ratio"),
                "portfolio_return": ((pv["Portfolio Value"] / self.initial_capital) - 1) * 100,
                "performance_metrics": performance_metrics.copy(),
                "ticker_details": [],
            }

            # Add ticker details for each symbol
            for symbol in self.symbols:
                ticker_detail = {
                    "ticker": symbol,
                    "action": "hold",
                    "quantity": 0,
                    "price": 0.0,
                    "shares_owned": 0.0,
                    "long_shares": 0.0,
                    "short_shares": 0.0,
                    "position_value": 0.0,
                    "bullish_count": 0,
                    "bearish_count": 0,
                    "neutral_count": 0,
                }
                date_result["ticker_details"].append(ticker_detail)

            results.append(date_result)

            # Send intermediate result if callback provided
            if progress_callback:
                progress_callback(
                    {
                        "type": "backtest_result",
                        "data": date_result,
                    }
                )

        # Get final portfolio state
        final_portfolio = {
            "cash": portfolio_values[-1]["Portfolio Value"] if portfolio_values else self.initial_capital,
            "positions": {symbol: {"amount": 0.0, "cost_basis": 0.0} for symbol in self.symbols},
            "realized_gains": dict.fromkeys(self.symbols, 0.0),
        }

        return {
            "results": results,
            "performance_metrics": performance_metrics,
            "portfolio_values": portfolio_values,
            "final_portfolio": final_portfolio,
        }

    def run_backtest_sync(self) -> dict[str, Any]:
        """
        Run the backtest synchronously.
        This version can be used by the CLI.
        """
        # Use asyncio to run the async version
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.arun_backtest())
        finally:
            loop.close()
