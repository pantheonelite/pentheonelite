"""Main crypto trading agent orchestrator."""

from datetime import datetime, timedelta
from typing import Any

import structlog
from app.backend.src.graph.workflow_orchestrator import CryptoWorkflowOrchestrator

logger = structlog.get_logger(__name__)


class CryptoAgent:
    """
    Main crypto trading agent orchestrator.

    This class wraps the LangGraph workflow and provides a clean interface
    for executing trading decisions based on the pattern from:
    https://github.com/51bitquant/ai-hedge-fund-crypto
    """

    def __init__(
        self, model_name: str = "gpt-4o-mini", model_provider: str = "OpenRouter", *, show_agent_graph: bool = False
    ):
        """
        Initialize the crypto trading agent.

        Parameters
        ----------
        model_name : str
            LLM model name to use
        model_provider : str
            LLM provider to use
        show_agent_graph : bool
            Whether to save the workflow graph as an image
        """
        self.model_name = model_name
        self.model_provider = model_provider
        self.show_agent_graph = show_agent_graph

        # Create workflow orchestrator
        self.orchestrator = CryptoWorkflowOrchestrator()

        logger.info("Crypto agent initialized", model_name=model_name, model_provider=model_provider)

    def run(
        self,
        tickers: list[str],
        end_date: datetime,
        portfolio: dict[str, Any],
        *,
        start_date: datetime | None = None,
        _show_reasoning: bool = False,
    ) -> dict[str, Any]:
        """
        Execute the crypto trading workflow.

        Parameters
        ----------
        tickers : List[str]
            List of crypto symbols to trade
        end_date : datetime
            End date for analysis
        portfolio : Dict[str, Any]
            Initial portfolio state
        start_date : datetime, optional
            Start date for historical data (defaults to 30 days before end_date)
        show_reasoning : bool
            Whether to show agent reasoning

        Returns
        -------
        Dict[str, Any]
            Trading decisions and analysis results
        """
        # Set default start_date if not provided
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        logger.info("Starting crypto trading agent", tickers=tickers, start_date=start_date, end_date=end_date)

        # Run the workflow using the orchestrator
        results = self.orchestrator.run_workflow(
            symbols=tickers,
            start_date=start_date,
            end_date=end_date,
            model_name=self.model_name,
            model_provider=self.model_provider,
            portfolio=portfolio,
            timeframe="1h",
        )

        # Parse decisions from results
        decisions = {}
        for symbol, decision in results.get("trading_decisions", {}).items():
            if isinstance(decision, dict):
                decisions[symbol] = decision
            else:
                decisions[symbol] = {
                    "action": getattr(decision, "action", "hold"),
                    "quantity": getattr(decision, "quantity", 0.0),
                    "price": getattr(decision, "price", 0.0),
                    "confidence": getattr(decision, "confidence", 0.0),
                    "reasoning": getattr(decision, "reasoning", ""),
                }

        logger.info("Crypto trading agent completed", decisions_count=len(decisions))

        return {
            "decisions": decisions,
            "analyst_signals": results.get("technical_signals", {}),
            "sentiment_signals": results.get("sentiment_signals", {}),
            "persona_signals": results.get("persona_signals", {}),
            "risk_signals": results.get("risk_assessments", {}),
            "portfolio_allocations": results.get("portfolio_allocations", {}),
            "price_data": results.get("price_data", {}),
            "execution_timestamp": results.get("execution_timestamp"),
            "progress_percentage": results.get("progress_percentage", 100.0),
            "error_messages": results.get("error_messages", []),
        }
