from collections.abc import Sequence
from typing import Any, cast

import pandas as pd
import structlog
from app.backend.client import AsterClient
from app.backend.src.graph.state import CryptoAgentState
from dateutil.relativedelta import relativedelta

from .benchmarks import BenchmarkCalculator
from .controller import AgentController
from .metrics import PerformanceMetricsCalculator
from .output import OutputBuilder
from .portfolio import Portfolio
from .trader import TradeExecutor
from .types import PerformanceMetrics, PortfolioValuePoint
from .valuation import calculate_portfolio_value, compute_exposures

logger = structlog.get_logger(__name__)


class BacktestEngine:
    """Coordinates the backtest loop using the new crypto agent components.

    This implementation orchestrates crypto agent decisions, trade execution,
    valuation, exposures and performance metrics for cryptocurrency backtesting.
    """

    def __init__(
        self,
        *,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        model_name: str,
        model_provider: str,
        selected_analysts: list[str] | None,
        initial_margin_requirement: float = 0.0,
    ) -> None:
        self._symbols = symbols
        self._start_date = start_date
        self._end_date = end_date
        self._initial_capital = float(initial_capital)
        self._model_name = model_name
        self._model_provider = model_provider
        self._selected_analysts = selected_analysts or ["crypto_analyst_agent"]

        # Initialize crypto portfolio
        self._portfolio = Portfolio(
            tickers=symbols,
            initial_cash=initial_capital,
            margin_requirement=initial_margin_requirement,
        )
        self._executor = TradeExecutor()
        self._agent_controller = AgentController()
        self._perf = PerformanceMetricsCalculator()
        self._results = OutputBuilder(initial_capital=self._initial_capital)

        # Benchmark calculator
        self._benchmark = BenchmarkCalculator()

        self._portfolio_values: list[PortfolioValuePoint] = []
        self._table_rows: list[list] = []
        self._performance_metrics: PerformanceMetrics = {
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "max_drawdown": None,
            "long_short_ratio": None,
            "gross_exposure": None,
            "net_exposure": None,
        }

    def _prefetch_data(self) -> None:
        """Pre-fetch data for all symbols to warm up the cache."""
        # Initialize Aster client
        self._aster_client = AsterClient()

        # Enter the context manager to initialize the client
        self._aster_client.__enter__()

        # For crypto, we don't need to prefetch as much data
        # The Aster client will handle caching internally
        # We could prefetch some basic price data if needed

    def run_backtest(self) -> PerformanceMetrics:
        """Run the crypto backtest using the new agent workflow."""
        self._prefetch_data()

        dates = pd.date_range(self._start_date, self._end_date, freq="B")
        if len(dates) > 0:
            self._portfolio_values = [{"Date": dates[0], "Portfolio Value": self._initial_capital}]
        else:
            self._portfolio_values = []

        for current_date in dates:
            lookback_start = (current_date - relativedelta(months=1)).strftime("%Y-%m-%d")
            current_date_str = current_date.strftime("%Y-%m-%d")
            if lookback_start == current_date_str:
                continue

            try:
                current_prices: dict[str, float] = {}
                missing_data = False
                for symbol in self._symbols:
                    try:
                        # Convert symbol to Aster format (remove /USDT if present, add USDT suffix)
                        aster_symbol = symbol.replace("/", "").replace("USDT", "") + "USDT"

                        # Get current price using Aster client
                        ticker_data = self._aster_client.get_ticker(aster_symbol)
                        price = float(ticker_data.price)

                        # Validate price is not zero
                        if price == 0.0:
                            logger.warning(
                                "Got zero price for %s (aster: %s) on %s. Skipping this date.",
                                symbol,
                                aster_symbol,
                                current_date_str,
                            )
                            missing_data = True
                            break

                        current_prices[symbol] = price
                        logger.debug(
                            "Price for %s: $%.2f on %s",
                            symbol,
                            price,
                            current_date_str,
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to get price for %s on %s: %s",
                            symbol,
                            current_date_str,
                            e,
                        )
                        missing_data = True
                        break
                if missing_data:
                    continue
            except Exception as e:
                logger.warning("Error processing date %s: %s", current_date_str, e)
                continue

            # Create crypto agent state
            try:
                state = self._create_crypto_agent_state(current_date_str, lookback_start, current_prices)
            except ValueError as e:
                logger.warning("Skipping date %s due to validation error: %s", current_date_str, e)
                continue

            # Run crypto agents workflow
            agent_output = self._run_crypto_agents(state)

            # Extract trading decisions from portfolio manager output
            decisions = self._extract_trading_decisions(agent_output)

            executed_trades: dict[str, int] = {}
            for symbol in self._symbols:
                d = decisions.get(symbol, {"action": "hold", "quantity": 0})
                action = d.get("action", "hold")
                qty = d.get("quantity", 0)
                executed_qty = self._executor.execute_trade(
                    symbol, action, qty, current_prices[symbol], self._portfolio
                )
                executed_trades[symbol] = executed_qty

            total_value = calculate_portfolio_value(self._portfolio, current_prices)
            exposures = compute_exposures(self._portfolio, current_prices)

            point: PortfolioValuePoint = {
                "Date": current_date,
                "Portfolio Value": total_value,
                "Long Exposure": exposures["Long Exposure"],
                "Short Exposure": exposures["Short Exposure"],
                "Gross Exposure": exposures["Gross Exposure"],
                "Net Exposure": exposures["Net Exposure"],
                "Long/Short Ratio": exposures["Long/Short Ratio"],
            }
            self._portfolio_values.append(point)

            # Build daily rows (stateless usage)
            rows = self._results.build_day_rows(
                date_str=current_date_str,
                tickers=self._symbols,
                agent_output=agent_output,
                executed_trades=executed_trades,
                current_prices=current_prices,
                portfolio=self._portfolio,
                performance_metrics=self._performance_metrics,
                total_value=total_value,
                benchmark_return_pct=self._benchmark.get_return_pct("BTC/USDT", self._start_date, current_date_str),
            )
            # Prepend today's rows to historical rows so latest day is on top
            self._table_rows = rows + self._table_rows
            # Print full history with latest day first (matches backtester.py behavior)
            self._results.print_rows(self._table_rows)

            # Update performance metrics after printing (match original timing)
            if len(self._portfolio_values) > 3:
                computed = self._perf.compute_metrics(self._portfolio_values)
                if computed:
                    self._performance_metrics.update(computed)

        return self._performance_metrics

    def get_portfolio_values(self) -> Sequence[PortfolioValuePoint]:
        """Get the portfolio values over time."""
        return list(self._portfolio_values)

    def _create_crypto_agent_state(
        self, current_date: str, lookback_start: str, current_prices: dict[str, float]
    ) -> CryptoAgentState:
        """Create crypto agent state for the current backtest iteration."""
        # Convert portfolio to crypto format
        portfolio_snapshot = self._portfolio.get_snapshot()

        # Validate current_prices has valid (non-zero) prices
        validated_prices = {symbol: price for symbol, price in current_prices.items() if price > 0}

        if not validated_prices:
            logger.warning(
                "No valid prices found in current_prices on %s. Available symbols: %s, Prices: %s",
                current_date,
                list(current_prices.keys()),
                current_prices,
            )
            # Return empty state to prevent further processing
            raise ValueError(f"No valid prices available on {current_date}")

        crypto_portfolio = {
            "cash": portfolio_snapshot["cash"],
            "positions": {
                symbol: {
                    "amount": pos["long"] - pos["short"],  # Net position
                    "cost_basis": pos["long_cost_basis"] if pos["long"] > 0 else pos["short_cost_basis"],
                    "current_price": validated_prices.get(symbol, 0.0),
                    "market_value": (pos["long"] - pos["short"]) * validated_prices.get(symbol, 0.0),
                    "unrealized_pnl": 0.0,  # Will be calculated
                }
                for symbol, pos in portfolio_snapshot["positions"].items()
            },
            "total_value": portfolio_snapshot["cash"]
            + sum(
                (pos["long"] - pos["short"]) * validated_prices.get(symbol, 0.0)
                for symbol, pos in portfolio_snapshot["positions"].items()
            ),
        }

        return {
            "messages": [],
            "data": {
                "symbols": self._symbols,
                "portfolio": crypto_portfolio,
                "current_prices": validated_prices,
                "start_date": lookback_start,
                "end_date": current_date,
                "analyst_signals": {},
                "risk_signals": {},
                "portfolio_signals": {},
            },
            "metadata": {
                "show_reasoning": False,
                "model_name": self._model_name,
                "model_provider": self._model_provider,
            },
        }

    def _run_crypto_agents(self, state: CryptoAgentState) -> dict[str, Any]:
        """Run the crypto agents workflow and return the final output."""
        try:
            # Use the agent controller to run the crypto agents
            result = self._agent_controller.run_crypto_agents(
                symbols=self._symbols,
                start_date=state["data"]["start_date"],
                end_date=state["data"]["end_date"],
                portfolio=self._portfolio,
                model_name=self._model_name,
                model_provider=self._model_provider,
                selected_analysts=self._selected_analysts,
            )
            # Cast AgentOutput (TypedDict) to dict[str, Any]
            return cast("dict[str, Any]", result)
        except Exception:
            # Return default decisions on error
            return {
                "decisions": {symbol: {"action": "hold", "quantity": 0} for symbol in self._symbols},
                "analyst_signals": {},
                "risk_signals": {},
                "portfolio_signals": {},
            }

    def _extract_trading_decisions(self, agent_output: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Extract trading decisions from the agent output."""
        decisions = agent_output.get("decisions", {})

        # Convert portfolio manager decisions to the format expected by trade executor
        trading_decisions = {}
        for symbol in self._symbols:
            if symbol in decisions:
                decision = decisions[symbol]
                trading_decisions[symbol] = {
                    "action": decision.get("action", "hold"),
                    "quantity": decision.get("quantity", 0.0),
                }
            else:
                trading_decisions[symbol] = {"action": "hold", "quantity": 0.0}

        return trading_decisions
