"""Workflow orchestrator for LangGraph-based crypto trading."""

from datetime import datetime
from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from .enhanced_state import CryptoAgentState, create_initial_state
from .nodes import (
    DataCollectionNode,
    MergeAnalysisNode,
    PortfolioManagementNode,
    RiskAssessmentNode,
    SentimentAnalysisNode,
    TechnicalAnalysisNode,
)
from .nodes.parallel_persona_execution_node import PersonaExecutionNode

logger = structlog.get_logger(__name__)


class CryptoWorkflowOrchestrator:
    """
    Orchestrates the crypto trading workflow using LangGraph.

    This class creates and manages the workflow graph with proper node connections
    and state management.
    """

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.nodes = {
            "data_collection": DataCollectionNode(),
            "technical_analysis": TechnicalAnalysisNode(),
            "sentiment_analysis": SentimentAnalysisNode(),
            "persona_execution": PersonaExecutionNode(),
            "merge_analysis": MergeAnalysisNode(),
            "risk_assessment": RiskAssessmentNode(),
            "portfolio_management": PortfolioManagementNode(),
        }

    def create_workflow(self) -> StateGraph:
        """
        Create the LangGraph workflow with parallel persona execution.

        Returns
        -------
        StateGraph
            Configured workflow graph with parallel persona agents
        """
        # Create the workflow graph
        workflow = StateGraph(CryptoAgentState)

        # Add main workflow nodes
        for node_name, node_instance in self.nodes.items():
            # Use parallel-safe execution for parallel nodes to avoid state conflicts
            if node_name in ["technical_analysis", "sentiment_analysis", "persona_execution"]:
                workflow.add_node(node_name, node_instance.parallel_safe_execute)
            else:
                workflow.add_node(node_name, node_instance.safe_execute)

        # Define the workflow edges (parallel fan-out + aggregator)
        workflow.add_edge("data_collection", "technical_analysis")
        workflow.add_edge("data_collection", "sentiment_analysis")
        workflow.add_edge("data_collection", "persona_execution")

        workflow.add_edge("technical_analysis", "merge_analysis")
        workflow.add_edge("sentiment_analysis", "merge_analysis")
        workflow.add_edge("persona_execution", "merge_analysis")

        workflow.add_edge("merge_analysis", "risk_assessment")
        workflow.add_edge("risk_assessment", "portfolio_management")
        workflow.add_edge("portfolio_management", END)

        # Set entry point
        workflow.set_entry_point("data_collection")

        return workflow

    def run_workflow(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        model_name: str = "gpt-4o-mini",
        model_provider: str = "LiteLLM",
        timeframe: str = "1h",
        portfolio: dict[str, Any] | None = None,
        max_concurrency: int = 10,
    ) -> dict[str, Any]:
        """
        Run the complete crypto trading workflow with parallel execution optimization.

        Parameters
        ----------
        symbols : list[str]
            List of crypto symbols to analyze
        start_date : datetime
            Start date for analysis
        end_date : datetime
            End date for analysis
        model_name : str, optional
            LLM model name (default: "gpt-4o-mini")
        model_provider : str, optional
            LLM provider (default: "LiteLLM")
        timeframe : str, optional
            Analysis timeframe (default: "1h")
        portfolio : dict[str, Any] | None, optional
            Initial portfolio state (default: None)
        max_concurrency : int, optional
            Maximum number of concurrent nodes in parallel execution (default: 10)
            - For I/O-bound tasks (LLM API calls): Use 10-20
            - For CPU-bound tasks: Use os.cpu_count()
            - Higher values allow more parallel API calls but may hit rate limits

        Returns
        -------
        dict[str, Any]
            Final workflow results with trading decisions, signals, and risk assessments

        Notes
        -----
        This method uses LangGraph's superstep execution model for optimal parallelism:
        - Parallel nodes (technical_analysis, sentiment_analysis, persona_execution) execute
          concurrently in the same superstep after data_collection
        - State reducers prevent INVALID_CONCURRENT_GRAPH_UPDATE errors
        - max_concurrency controls the level of parallelism for performance tuning
        """
        # Create initial state using the enhanced state structure
        initial_state = create_initial_state(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            model_name=model_name,
            model_provider=model_provider,
            timeframe=timeframe,
            portfolio=portfolio or {},
        )

        # Create and compile workflow
        workflow = self.create_workflow()
        compiled_workflow = workflow.compile()

        # Execute workflow with max_concurrency configuration for parallel execution
        logger.info(
            "Executing workflow with parallel optimization",
            symbols=symbols,
            max_concurrency=max_concurrency,
            nodes=["technical_analysis", "sentiment_analysis", "persona_execution"],
        )

        final_state = compiled_workflow.invoke(
            initial_state, config={"configurable": {"max_concurrency": max_concurrency}}
        )

        # Extract results from enhanced state
        return {
            "symbols": symbols,
            "trading_decisions": final_state.get("trading_decisions", {}),
            "portfolio_allocations": final_state.get("portfolio_allocations", {}),
            "technical_signals": final_state.get("technical_signals", {}),
            "sentiment_signals": final_state.get("sentiment_signals", {}),
            "persona_signals": final_state.get("persona_signals", {}),
            "persona_consensus": final_state.get("persona_consensus", {}),
            "risk_assessments": final_state.get("risk_assessments", {}),
            "price_data": final_state.get("price_data", {}),
            "execution_timestamp": final_state.get("execution_timestamp", datetime.now()).isoformat(),
            "progress_percentage": final_state.get("progress_percentage", 100.0),
            "error_messages": final_state.get("error_messages", []),
        }

    def get_workflow_info(self) -> dict[str, Any]:
        """
        Get information about the workflow structure.

        Returns
        -------
        Dict[str, Any]
            Workflow information
        """
        return {
            "nodes": {name: node.get_node_info() for name, node in self.nodes.items()},
            "workflow_structure": {
                "entry_point": "data_collection",
                "parallel_nodes": ["technical_analysis", "sentiment_analysis", "persona_execution"],
                "aggregator": "merge_analysis",
                "final_nodes": ["risk_assessment", "portfolio_management"],
                "end_point": "portfolio_management",
            },
        }
