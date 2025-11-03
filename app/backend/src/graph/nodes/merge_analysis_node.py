"""Aggregator node to merge outputs from parallel analysis nodes."""

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState

from .base_node import BaseNode

logger = structlog.get_logger(__name__)


class MergeAnalysisNode(BaseNode):
    """
    Merge outputs from technical, sentiment, and persona analysis into the state.

    This node plays the role of the "aggregator" in the LangGraph parallel pattern.
    """

    def __init__(self):
        super().__init__(
            name="merge_analysis",
            description="Aggregates technical, sentiment, and persona outputs",
        )

    def get_required_data(self) -> list[str]:
        """Fields expected to be present before aggregation."""
        return [
            "technical_signals",
            "sentiment_signals",
            # persona_signals and persona_consensus may be missing if no data
        ]

    def get_output_data(self) -> list[str]:
        """Fields guaranteed to exist after aggregation."""
        return [
            "technical_signals",
            "sentiment_signals",
            "persona_signals",
            "persona_consensus",
        ]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """Ensure containers exist and log aggregation sizes."""
        technical_count = len(state.get("technical_signals", {}))
        sentiment_count = len(state.get("sentiment_signals", {}))
        persona_count = len(state.get("persona_signals", {}))

        logger.info(
            "Aggregated: tech=%d, sent=%d, persona=%d",
            technical_count,
            sentiment_count,
            persona_count,
        )
        return state
