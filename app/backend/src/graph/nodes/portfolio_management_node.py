"""Portfolio management node for crypto trading workflow."""

import asyncio

import structlog
from app.backend.src.agents.portfolio_manager import CryptoPortfolioManagerAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState

from .base_node import BaseNode

logger = structlog.get_logger(__name__)


class PortfolioManagementNode(BaseNode):
    """Node for portfolio management using crypto portfolio manager agent."""

    def __init__(self):
        super().__init__(
            name="portfolio_management",
            description="Manages portfolio using crypto portfolio manager agent",
        )

    def get_required_data(self) -> list[str]:
        return ["symbols", "technical_signals", "sentiment_signals", "persona_signals", "risk_assessments"]

    def get_output_data(self) -> list[str]:
        return ["trading_decisions", "portfolio_allocations"]

    async def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute portfolio management using LLM-based per-symbol decisions.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state with trading decisions from LLM agent
        """
        try:
            symbols = state.get("symbols", [])
            logger.info("Running portfolio management with LLM decisions for %d symbols", len(symbols))

            # Get the portfolio manager agent
            portfolio_manager = CryptoPortfolioManagerAgent()

            # Execute LLM-based decisions for each symbol in parallel
            tasks = []
            for symbol in symbols:
                task = portfolio_manager.analyze_symbol(symbol, state)
                tasks.append(task)

            decisions_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results into trading decisions
            trading_decisions = {}
            for result in decisions_results:
                if isinstance(result, dict) and "symbol" in result:
                    symbol = result["symbol"]
                    trading_decisions[symbol] = result
                    logger.info(
                        "Portfolio decision for %s: %s (confidence: %.1f%%)",
                        symbol,
                        result.get("action", "unknown"),
                        result.get("confidence", 0.0),
                    )
                elif isinstance(result, Exception):
                    logger.error("Error in portfolio decision: %s", result)

            # Update state with decisions
            state["trading_decisions"].update(trading_decisions)
            logger.info("Portfolio management completed: %d decisions", len(trading_decisions))

            return state

        except Exception:
            logger.exception("Error in portfolio management")
            return state
