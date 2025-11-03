"""Crypto trading workflow service for backend integration."""

from datetime import datetime
from typing import Any

import structlog
from app.backend.src.agent.agent import CryptoAgent
from app.backend.src.utils.workflow_result import WorkflowResult

logger = structlog.get_logger(__name__)


class CryptoWorkflowService:
    """
    Service class for crypto trading workflow execution.

    This service provides a clean interface for backend integration,
    handling workflow execution and result formatting.
    """

    def __init__(self, model_name: str = "gpt-4o-mini", model_provider: str = "LiteLLM"):
        """
        Initialize the crypto workflow service.

        Parameters
        ----------
        model_name : str
            LLM model name to use
        model_provider : str
            LLM provider name
        """
        self.model_name = model_name
        self.model_provider = model_provider
        self.agent = CryptoAgent(model_name=model_name, model_provider=model_provider)
        logger.info("Crypto workflow service initialized", model_name=model_name, model_provider=model_provider)

    def execute_workflow(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        portfolio: dict[str, Any] | None = None,
        *,
        show_reasoning: bool = False,
    ) -> WorkflowResult:
        """
        Execute the crypto trading workflow.

        Parameters
        ----------
        symbols : list[str]
            List of crypto symbols to analyze
        start_date : str
            Start date for analysis (YYYY-MM-DD)
        end_date : str
            End date for analysis (YYYY-MM-DD)
        portfolio : dict[str, Any] | None
            Initial portfolio state
        show_reasoning : bool
            Whether to include agent reasoning in output

        Returns
        -------
        WorkflowResult
            Structured workflow result
        """
        logger.info("Executing crypto workflow", symbols=symbols, start_date=start_date, end_date=end_date)

        # Default portfolio if not provided
        if portfolio is None:
            portfolio = {
                "cash": 100000.0,
                "positions": {symbol: {"amount": 0.0, "cost_basis": 0.0} for symbol in symbols},
                "realized_gains": dict.fromkeys(symbols, 0.0),
            }

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=None)  # noqa: DTZ007

        # Execute workflow
        result = self.agent.run(
            tickers=symbols,
            start_date=start_dt,
            end_date=end_dt,
            portfolio=portfolio,
            show_reasoning=show_reasoning,
        )

        # Convert to WorkflowResult
        workflow_result = WorkflowResult(result)

        logger.info(
            "Workflow execution completed",
            symbols=symbols,
            has_errors=workflow_result.has_errors(),
            progress=workflow_result.progress_percentage,
        )

        return workflow_result

    def get_symbol_analysis(self, workflow_result: WorkflowResult, symbol: str) -> dict[str, Any]:
        """
        Get comprehensive analysis for a specific symbol.

        Parameters
        ----------
        workflow_result : WorkflowResult
            Workflow execution result
        symbol : str
            Symbol to analyze

        Returns
        -------
        dict[str, Any]
            Comprehensive analysis for the symbol
        """
        return workflow_result.get_all_signals_for_symbol(symbol)

    def get_portfolio_summary(self, workflow_result: WorkflowResult) -> dict[str, Any]:
        """
        Get portfolio summary from workflow result.

        Parameters
        ----------
        workflow_result : WorkflowResult
            Workflow execution result

        Returns
        -------
        dict[str, Any]
            Portfolio summary
        """
        return {
            "allocations": workflow_result.portfolio_allocations,
            "statistics": workflow_result.get_summary_statistics(),
            "execution_info": {
                "timestamp": workflow_result.execution_timestamp,
                "progress": workflow_result.progress_percentage,
                "has_errors": workflow_result.has_errors(),
                "error_count": len(workflow_result.error_messages),
            },
        }

    def to_api_response(self, workflow_result: WorkflowResult) -> dict[str, Any]:
        """
        Convert workflow result to API response format.

        Parameters
        ----------
        workflow_result : WorkflowResult
            Workflow execution result

        Returns
        -------
        dict[str, Any]
            API response format
        """
        return {
            "success": not workflow_result.has_errors(),
            "data": workflow_result.to_dict(),
            "metadata": {
                "execution_timestamp": workflow_result.execution_timestamp,
                "progress_percentage": workflow_result.progress_percentage,
                "error_count": len(workflow_result.error_messages),
            },
        }
