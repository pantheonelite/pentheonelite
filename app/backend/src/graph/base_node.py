"""Base node class for LangGraph-based crypto trading workflow."""

from abc import ABC, abstractmethod
from typing import Any, cast

import structlog

from .enhanced_state import CryptoAgentState, add_error_message, update_state_progress

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
        # Cast to regular dict for dynamic key access
        state_dict = cast("dict[str, Any]", state)
        missing_fields = [field for field in required_fields if field not in state_dict or not state_dict[field]]

        if missing_fields:
            logger.warning("Missing required fields: %s", missing_fields)
            return False

        return True

    def log_execution_start(self, state: CryptoAgentState) -> None:
        """Log the start of node execution."""
        logger.info("Starting execution of %s", self.name)
        logger.debug("State summary: %s", self._get_state_summary(state))

    def log_execution_end(self, state: CryptoAgentState, *, success: bool = True) -> None:
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

    def safe_execute(self, state: CryptoAgentState, progress_update: float = 0.0) -> CryptoAgentState:
        """
        Safely execute the node with error handling and progress tracking.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state
        progress_update : float
            Progress percentage to update

        Returns
        -------
        CryptoAgentState
            Updated state after execution
        """
        try:
            # Log execution start
            self.log_execution_start(state)

            # Update progress
            state = update_state_progress(state, self.name, progress_update)

            # Validate input data
            if not self.validate_input_data(state):
                error_msg = f"Missing required input data for {self.name}"
                state = add_error_message(state, error_msg)
                self.log_execution_end(state, success=False)
                return state

            # Execute the node's main logic
            result_state = self.execute(state)

            # Log execution end
            self.log_execution_end(result_state, success=True)

            return result_state

        except Exception as e:
            error_msg = f"Error in {self.name}: {e!s}"
            logger.exception(error_msg)
            state = add_error_message(state, error_msg)
            self.log_execution_end(state, success=False)
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
