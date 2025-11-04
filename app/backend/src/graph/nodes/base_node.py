"""Base node class for LangGraph-based crypto trading workflow."""

import asyncio
import inspect
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState

from .tool_manager import ToolManager

logger = structlog.get_logger(__name__)


class BaseNode(ABC):
    """
    Base class for all LangGraph nodes in the crypto trading workflow.

    This class provides common functionality for all nodes including:
    - Progress tracking
    - Error handling
    - State management
    - Logging
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base node.

        Parameters
        ----------
        name : str
            Name of the node
        description : str
            Description of what the node does
        """
        self.name = name
        self.description = description
        self.tool_manager = ToolManager()
        structlog.get_logger(f"node.{name}")

    @abstractmethod
    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute the node's main logic.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state after execution
        """

    @abstractmethod
    def get_required_data(self) -> list[str]:
        """
        Get list of required data fields for this node.

        Returns
        -------
        List[str]
            List of required data field names
        """

    @abstractmethod
    def get_output_data(self) -> list[str]:
        """
        Get list of output data fields produced by this node.

        Returns
        -------
        List[str]
            List of output data field names
        """

    def validate_input_data(self, state: CryptoAgentState) -> bool:
        """
        Validate that required input data is present.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        bool
            True if all required data is present
        """
        required_fields = self.get_required_data()
        missing_fields = [field for field in required_fields if field not in state or not state[field]]

        if missing_fields:
            logger.warning("Missing required fields: %s", missing_fields)
            return False

        return True

    def log_execution_start(self, state: CryptoAgentState) -> None:
        """Log the start of node execution."""
        logger.info("Starting execution of %s", self.name)
        logger.debug("State summary: %s", self._get_state_summary(state))

    def log_execution_end(self, *, success: bool = True) -> None:
        """Log the end of node execution."""
        if success:
            logger.info("Completed execution of %s", self.name)
        else:
            logger.error("Failed execution of %s", self.name)

    def _get_state_summary(self, state: CryptoAgentState) -> dict[str, Any]:
        """Get a summary of the current state for logging."""
        return {
            "current_node": state.get("current_node", "unknown"),
            "progress_percentage": state.get("progress_percentage", 0.0),
            "symbols_count": len(state.get("symbols", [])),
            "error_count": len(state.get("error_messages", [])),
        }

    def safe_execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Safely execute the node with error handling and progress tracking.

        Supports both sync and async execute methods.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state after execution
        """
        try:
            # Update current node and progress in state
            state["current_node"] = self.name

            # Log execution start
            self.log_execution_start(state)

            # Execute the node's main logic (handle both sync and async)
            if inspect.iscoroutinefunction(self.execute):
                # Async execution - run in a separate thread to avoid event loop conflicts
                def run_async():
                    return asyncio.run(self.execute(state))

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_async)
                    result_state = future.result()
            else:
                # Sync execution
                result_state = self.execute(state)

            # Ensure current_node is set in result
            result_state["current_node"] = self.name
            # Update progress percentage (6 nodes total, sequential execution)
            node_progress = {
                "data_collection": 0.167,  # 1/6
                "technical_analysis": 0.333,  # 2/6
                "sentiment_analysis": 0.500,  # 3/6
                "persona_analysis": 0.667,  # 4/6
                "risk_assessment": 0.833,  # 5/6
                "portfolio_management": 1.0,  # 6/6
            }
            result_state["progress_percentage"] = node_progress.get(self.name, 0.0) * 100.0

            # Log execution end with progress
            self.log_execution_end(success=True)
            logger.info("Progress: %.1f%% - Completed %s", result_state["progress_percentage"], self.name)

            return result_state

        except Exception as e:
            error_msg = f"Error in {self.name}: {e!s}"
            logger.exception(error_msg)
            self.log_execution_end(success=False)
            return state

    def parallel_safe_execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Safely execute the node for parallel execution without state conflicts.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state after execution
        """
        try:
            # Log execution start (without updating current_node to avoid conflicts)
            logger.info("Starting execution of %s", self.name)
            logger.debug("State summary: %s", self._get_state_summary(state))

            # Execute the node's main logic
            result_state = self.execute(state)

            # Log execution end
            logger.info("Completed execution of %s", self.name)

            return result_state

        except Exception as e:
            logger.exception("Error in node %s: %s", self.name, e)
            # Add error to state
            if "error_messages" not in state:
                state["error_messages"] = []
            state["error_messages"].append(f"Node {self.name}: {e!s}")
            logger.error("Failed execution of %s", self.name)
            return state

    def get_node_info(self) -> dict[str, Any]:
        """
        Get information about this node.

        Returns
        -------
        Dict[str, Any]
            Node information
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_data": self.get_required_data(),
            "output_data": self.get_output_data(),
        }

    def clean_symbol(self, symbol: str) -> str:
        """
        Clean and normalize a trading symbol.

        Parameters
        ----------
        symbol : str
            Raw trading symbol

        Returns
        -------
        str
            Cleaned symbol
        """
        return self.tool_manager.clean_symbol(symbol)

    def to_aster_symbol(self, symbol: str) -> str:
        """
        Convert symbol to Aster API format.

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        str
            Aster-formatted symbol
        """
        return self.tool_manager.to_aster_symbol(symbol)

    def execute_tool_safely(self, tool_name: str, input_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Execute a tool with error handling and result parsing.

        Parameters
        ----------
        tool_name : str
            Name of the tool to execute
        input_data : dict
            Input data for the tool

        Returns
        -------
        dict | None
            Parsed tool result or None if failed
        """
        return self.tool_manager.execute_tool_safely(tool_name, input_data)

    def execute_agent_safely(self, agent_name: str, state: dict[str, Any]) -> dict[str, Any] | None:
        """
        Execute an agent with error handling.

        Parameters
        ----------
        agent_name : str
            Name of the agent to execute
        state : dict
            State data for the agent

        Returns
        -------
        dict | None
            Agent result or None if failed
        """
        return self.tool_manager.execute_agent_safely(agent_name, state)
