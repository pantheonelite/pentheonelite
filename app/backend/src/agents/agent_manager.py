"""Simple Agent Manager with class variables mapping to agent classes."""

from collections.abc import Callable
from typing import ClassVar

from app.backend.src.agents.analyst import (
    CryptoAnalystAgent,
    CryptoSentimentAgent,
    CryptoTechnicalAgent,
    CZBinanceAgent,
    DeFiAgent,
    ElonMuskAgent,
    MichaelSaylorAgent,
    SatoshiNakamotoAgent,
    VitalikButerinAgent,
)
from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState


class AgentManager:
    """Simple agent manager with class variables mapping to agent classes."""

    AGENTS: ClassVar[dict[str, type[BaseCryptoAgent]]] = {
        "satoshi_nakamoto": SatoshiNakamotoAgent,
        "vitalik_buterin": VitalikButerinAgent,
        "cz_binance": CZBinanceAgent,
        "michael_saylor": MichaelSaylorAgent,
        "elon_musk": ElonMuskAgent,
        "crypto_technical": CryptoTechnicalAgent,
        "crypto_sentiment": CryptoSentimentAgent,
        "crypto_analyst": CryptoAnalystAgent,
        "defi_agent": DeFiAgent,
    }

    @classmethod
    def get_agent_class(cls, key: str) -> type[BaseCryptoAgent] | None:
        """
        Get agent class by key.

        Parameters
        ----------
        key : str
            Agent key

        Returns
        -------
        type[BaseCryptoAgent] | None
            Agent class or None if not found
        """
        return cls.AGENTS.get(key)

    @classmethod
    def get_agent_function(cls, key: str) -> Callable | None:
        """
        Get LangGraph function for an agent.

        Parameters
        ----------
        key : str
            Agent key

        Returns
        -------
        Callable | None
            Agent function or None if not found
        """
        agent_class = cls.get_agent_class(key)
        if agent_class is None:
            return None
        agent_id = f"{key}_agent"

        # Return lambda that captures agent_class and agent_id
        return lambda state, progress_tracker=None: cls._execute_agent(agent_class, agent_id, state, progress_tracker)

    @staticmethod
    def _execute_agent(
        agent_class: type[BaseCryptoAgent],
        agent_id: str,
        state: CryptoAgentState,
        progress_tracker=None,
    ) -> CryptoAgentState:
        """Execute an agent with the given state."""
        agent_instance = agent_class()
        symbols = state.get("data", {}).get("symbols", [])

        analyses = {}
        for symbol in symbols:
            try:
                if progress_tracker:
                    progress_tracker.update_status(
                        agent_instance.agent_id, symbol, f"Analyzing {agent_instance.agent_name}"
                    )

                analysis = agent_instance.analyze_symbol(symbol, state)
                analyses[symbol] = analysis

                if progress_tracker:
                    progress_tracker.update_status(
                        agent_instance.agent_id, symbol, "Done", analysis=analysis.get("reasoning", "")
                    )
            except Exception as e:
                if progress_tracker:
                    progress_tracker.update_status(agent_instance.agent_id, symbol, "Error", analysis=str(e))
                analyses[symbol] = {
                    "agent_id": agent_instance.agent_id,
                    "signal": "hold",
                    "confidence": 0.0,
                    "reasoning": f"Error: {e!s}",
                }

        if "technical_signals" not in state:
            state["technical_signals"] = {}
        state["technical_signals"][agent_id] = analyses

        if progress_tracker:
            progress_tracker.update_status(agent_instance.agent_id, None, "Done")

        return state

    @classmethod
    def get_all_keys(cls) -> list[str]:
        """
        Get all agent keys.

        Returns
        -------
        list[str]
            List of agent keys
        """
        return list(cls.AGENTS.keys())

    @classmethod
    def get_agent_nodes(cls) -> dict[str, tuple[str, Callable]]:
        """
        Get agent nodes for LangGraph workflow.

        Returns
        -------
        dict[str, tuple[str, Callable]]
            Dictionary mapping agent keys to (node_name, function) tuples
        """
        nodes = {}
        for key in cls.AGENTS:
            func = cls.get_agent_function(key)
            if func:
                nodes[key] = (f"{key}_agent", func)
        return nodes

    @classmethod
    def get_agents_list(cls) -> list[dict[str, str]]:
        """
        Get list of agents for API responses.

        Returns
        -------
        list[dict[str, str]]
            List of agent dictionaries with just the key
        """
        return [{"key": key} for key in cls.AGENTS]
