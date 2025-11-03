"""Complete persona execution and consensus node."""

import asyncio
from typing import Any

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.graph.nodes.base_node import BaseNode

logger = structlog.get_logger(__name__)


# Single source of truth for persona agents
PERSONA_AGENTS = [
    "cz_binance",
    "vitalik_buterin",
    "michael_saylor",
    "satoshi_nakamoto",
    "elon_musk",
]


class PersonaExecutionNode(BaseNode):
    """Complete persona execution and consensus node."""

    def __init__(self):
        super().__init__(
            name="persona_execution",
            description="Executes all persona agents in parallel and creates consensus",
        )

    @property
    def persona_agents(self) -> list[str]:
        """Return the list of persona agents."""
        return PERSONA_AGENTS

    def get_required_data(self) -> list[str]:
        """Return required input data fields."""
        return ["symbols", "price_data", "volume_data", "news_data"]

    def get_output_data(self) -> list[str]:
        """Return output data fields."""
        return ["persona_signals", "persona_consensus"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """Execute all persona agents in parallel and create consensus."""
        try:
            symbols = state.get("symbols", [])
            logger.info(
                "Running %d persona agents in parallel on %d symbols",
                len(self.persona_agents),
                len(symbols),
            )

            # Execute all personas in parallel
            persona_results = asyncio.run(self._run_personas_parallel(state))

            # Store individual persona signals in display-compatible format
            persona_signals = {}
            for persona_key, result in persona_results.items():
                agent_signals = result
                if not agent_signals:
                    logger.warning("No agent_signals found for %s", persona_key)
                    continue

                # Store in format expected by display manager
                persona_signals[persona_key] = agent_signals
                logger.info("Stored %s signals: %d symbols", persona_key, len(agent_signals))

            # Create consensus from all persona signals
            consensus = self._create_consensus(persona_signals, symbols)

            logger.info("Persona execution completed: %d agents, %d symbols", len(self.persona_agents), len(symbols))

            # Return only the fields we updated
            return {"persona_consensus": consensus, "persona_signals": persona_signals}

        except Exception:
            logger.exception("Error in persona execution")
            return state

    async def _run_persona_agent(self, persona_key: str, state: CryptoAgentState) -> tuple[str, dict[str, Any]]:
        """Run a single persona agent and return (key, result)."""
        try:
            logger.info("Starting persona agent: %s", persona_key)
            agent = self.tool_manager.get_agent(persona_key)
            agent_result = await agent.arun_agent(state, progress_tracker=None)

            if agent_result and "agent_signals" in agent_result:
                # Extract the signals for this specific persona agent
                # agent_result["agent_signals"] is {agent_id: {symbol: signal_data}}
                agent_signals_dict = agent_result["agent_signals"]

                # Get signals for this persona (agent_id matches persona_key)
                if persona_key in agent_signals_dict:
                    persona_signals = agent_signals_dict[persona_key]
                    logger.info("Persona %s result: %d symbols", persona_key, len(persona_signals))
                    return persona_key, persona_signals

                logger.warning(
                    "Persona %s: agent_id not found in agent_signals dict. Keys: %s",
                    persona_key,
                    list(agent_signals_dict.keys()),
                )
                return persona_key, {}

            logger.warning(
                "Persona %s returned no agent_signals in result. Keys: %s",
                persona_key,
                list(agent_result.keys()) if agent_result else "None",
            )
            return persona_key, {}
        except Exception:
            logger.exception("Persona %s failed", persona_key)
            return persona_key, {}

    async def _run_personas_parallel(self, state: CryptoAgentState) -> dict[str, dict[str, Any]]:
        """Run all persona agents in parallel using asyncio.gather."""
        results_list = await asyncio.gather(
            *[self._run_persona_agent(persona_key, state) for persona_key in self.persona_agents],
            return_exceptions=True,
        )

        results = {}
        for result in results_list:
            if isinstance(result, Exception):
                logger.error("Persona task failed: %s", result)
            else:
                key, value = result
                # value is the agent_signals dict for the persona
                results[key] = value

        return results

    def _create_consensus(
        self, persona_signals: dict[str, dict[str, Any]], symbols: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Create consensus from persona signals."""
        consensus = {}

        for symbol in symbols:
            signals = self._extract_signals_for_symbol(persona_signals, symbol)
            # Debug: signal aggregation per symbol
            logger.debug("Persona signals for %s: count=%d", symbol, len(signals))
            if not signals:
                consensus[symbol] = {"signal": "HOLD", "confidence": 0.0, "count": 0}
            else:
                # Simple weighted voting for FUTURES trading (LONG/SHORT/HOLD)
                weights = {"LONG": 0.0, "SHORT": 0.0, "HOLD": 0.0}
                for sig in signals:
                    signal = sig["signal"].upper()
                    # Map both old (BUY/SELL) and new (LONG/SHORT) signals
                    if signal in ["LONG", "BUY", "STRONG_BUY", "strong_buy"]:
                        weights["LONG"] += sig["confidence"] * (1.5 if "STRONG" in signal else 1.0)
                    elif signal in ["SHORT", "SELL", "STRONG_SELL", "strong_sell"]:
                        weights["SHORT"] += sig["confidence"] * (1.5 if "STRONG" in signal else 1.0)
                    else:
                        weights["HOLD"] += sig["confidence"]

                # Get consensus signal
                consensus_signal = max(weights, key=weights.get)
                consensus_confidence = weights[consensus_signal]

                consensus[symbol] = {
                    "signal": consensus_signal,
                    "confidence": consensus_confidence,
                    "count": len(signals),
                    "personas": signals,
                }

        return consensus

    def _extract_signals_for_symbol(
        self, persona_signals: dict[str, dict[str, Any]], symbol: str
    ) -> list[dict[str, Any]]:
        """Extract all persona signals for a given symbol."""
        signals = []
        for persona_key, agent_signals in persona_signals.items():
            if isinstance(agent_signals, dict) and symbol in agent_signals:
                signal_data = agent_signals[symbol]
                signals.append(
                    {
                        "persona": persona_key,
                        "signal": signal_data.get("signal", "HOLD"),
                        "confidence": signal_data.get("confidence", 0.5),
                    }
                )
        return signals


class GenericPersonaAgentNode(BaseNode):
    """
    Generic node for any persona agent execution.

    Replaces the 5 duplicate node classes with a single configurable one.
    """

    def __init__(self, persona_name: str):
        """
        Initialize persona agent node.

        Parameters
        ----------
        persona_name : str
            Name of the persona agent (e.g., "cz_binance", "vitalik_buterin")
        """
        super().__init__(
            name=f"{persona_name}_agent",
            description=f"{persona_name} persona analysis agent",
        )
        self.persona_name = persona_name

    def get_required_data(self) -> list[str]:
        """Return required input data fields."""
        return ["symbols", "price_data", "volume_data", "news_data"]

    def get_output_data(self) -> list[str]:
        """Return output data fields."""
        return [f"{self.persona_name}_signals"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute persona agent analysis.

        Parameters
        ----------
        state : CryptoAgentState
            Current agent state

        Returns
        -------
        CryptoAgentState
            Updated state with persona signals
        """
        try:
            symbols = state.get("symbols", [])
            logger.info("Running %s agent on %d symbols", self.persona_name, len(symbols))

            # Get the agent and run it
            agent = self.tool_manager.get_agent(self.persona_name)
            result = agent.run_agent(state, progress_tracker=None)

            # Store signals
            if result and "agent_signals" in result:
                signal_key = f"{self.persona_name}_signals"
                state.setdefault(signal_key, {})
                state[signal_key].update(result["agent_signals"])

            logger.info("%s agent completed", self.persona_name)
        except Exception:
            logger.exception("Error in %s agent", self.persona_name)

        return state
