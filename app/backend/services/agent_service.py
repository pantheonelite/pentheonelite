"""Agent service for creating and managing agent functions."""

from collections.abc import Callable
from functools import partial

from app.backend.src.graph.state import CryptoAgentState as AgentState


class AgentService:
    """Service for creating and managing agent functions."""

    def __init__(self):
        """Initialize the agent service."""
        self._agent_functions = {}

    def create_agent_function(self, agent_function: Callable, agent_id: str) -> Callable[[AgentState], dict]:
        """
        Creates a new function from an agent function that accepts an agent_id.

        Parameters
        ----------
        agent_function : Callable
            The agent function to wrap.
        agent_id : str
            The ID to be passed to the agent.

        Returns
        -------
        Callable[[AgentState], dict]
            A new function that can be called by LangGraph.
        """
        return partial(agent_function, agent_id=agent_id)

    def register_agent_function(self, agent_id: str, agent_function: Callable) -> None:
        """
        Register an agent function for later use.

        Parameters
        ----------
        agent_id : str
            The ID for the agent.
        agent_function : Callable
            The agent function to register.
        """
        self._agent_functions[agent_id] = agent_function

    def get_agent_function(self, agent_id: str) -> Callable | None:
        """
        Get a registered agent function by ID.

        Parameters
        ----------
        agent_id : str
            The ID of the agent.

        Returns
        -------
        Callable | None
            The agent function if found, None otherwise.
        """
        return self._agent_functions.get(agent_id)

    def list_agent_functions(self) -> list[str]:
        """
        List all registered agent function IDs.

        Returns
        -------
        list[str]
            List of agent function IDs.
        """
        return list(self._agent_functions.keys())

    def remove_agent_function(self, agent_id: str) -> bool:
        """
        Remove an agent function by ID.

        Parameters
        ----------
        agent_id : str
            The ID of the agent to remove.

        Returns
        -------
        bool
            True if the agent was removed, False if not found.
        """
        if agent_id in self._agent_functions:
            del self._agent_functions[agent_id]
            return True
        return False
