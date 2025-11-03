"""Risk assessment node for crypto trading workflow."""

import structlog
from app.backend.src.agents.crypto_risk_manager import CryptoRiskManagerAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.graph.nodes.base_node import BaseNode

logger = structlog.get_logger(__name__)


class RiskAssessmentNode(BaseNode):
    """Risk assessment node using the simplified crypto risk manager."""

    def __init__(self):
        super().__init__(
            name="risk_assessment",
            description="Performs risk assessment using technical, sentiment, and persona signals",
        )
        self.risk_manager = CryptoRiskManagerAgent()

    def get_required_data(self) -> list[str]:
        """Return required input data fields."""
        return ["symbols", "technical_signals", "sentiment_signals", "persona_consensus"]

    def get_output_data(self) -> list[str]:
        """Return output data fields."""
        return ["risk_assessments"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """Execute risk assessment for all symbols."""
        try:
            symbols = state.get("symbols", [])
            logger.info("Running risk assessment for %d symbols", len(symbols))

            # Log signal availability for debugging
            # Count actual signals across all agents and symbols
            technical_signals = state.get("technical_signals", {})
            sentiment_signals = state.get("sentiment_signals", {})
            persona_consensus = state.get("persona_consensus", {})

            technical_count = sum(len(agent_signals) for agent_signals in technical_signals.values())
            sentiment_count = sum(len(agent_signals) for agent_signals in sentiment_signals.values())
            persona_count = len(persona_consensus)  # persona_consensus is symbol-level dict

            # Log agent-level breakdown for detailed debugging
            technical_agents = list(technical_signals.keys())
            sentiment_agents = list(sentiment_signals.keys())

            logger.info(
                "Risk assessment input signals - Technical: %d (from %d agents: %s), "
                "Sentiment: %d (from %d agents: %s), Persona: %d symbols",
                technical_count,
                len(technical_agents),
                technical_agents,
                sentiment_count,
                len(sentiment_agents),
                sentiment_agents,
                persona_count,
            )

            # Execute risk assessment for all symbols synchronously
            risk_assessments = {}
            for symbol in symbols:
                result = self._run_risk_assessment_single(symbol, state)
                if result:
                    risk_assessments[symbol] = result
                    logger.info("Risk assessment completed for %s", symbol)
                else:
                    logger.warning("No risk assessment result for %s", symbol)

            state["risk_assessments"] = risk_assessments
            logger.info("Risk assessment completed: %d symbols", len(risk_assessments))
            return state

        except Exception:
            logger.exception("Error in risk assessment")
            return state

    def _run_risk_assessment_single(self, symbol: str, state: CryptoAgentState) -> dict | None:
        """Run risk assessment for a single symbol."""
        try:
            return self.risk_manager.analyze_symbol(symbol, state)
        except Exception:
            logger.exception("Risk assessment failed for %s", symbol)
            return None
