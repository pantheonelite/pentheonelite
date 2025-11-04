"""Analysis nodes for crypto trading workflow."""

import json

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState

from .base_node import BaseNode

logger = structlog.get_logger(__name__)


class TechnicalAnalysisNode(BaseNode):
    """Node for performing technical analysis using crypto technical agent."""

    def __init__(self):
        super().__init__(
            name="technical_analysis", description="Performs technical analysis using crypto technical agent"
        )

    def get_required_data(self) -> list[str]:
        """Get list of required data fields for technical analysis."""
        return ["symbols", "price_data"]

    def get_output_data(self) -> list[str]:
        """Get list of output data fields for technical analysis."""
        return ["technical_signals"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute technical analysis using the crypto technical agent.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state with technical signals from agent
        """
        try:
            # Enhanced state structure - data is directly in state
            symbols = state.get("symbols", [])
            logger.info("Running technical analysis agent on %s symbols", len(symbols))

            # Run the crypto technical analysis agent
            agent_result = self.execute_agent_safely("crypto_technical", state)

            # Log the technical agent result for debugging (only agent_signals to avoid HumanMessage)
            if "agent_signals" in agent_result:
                # Return only the fields we updated
                return {"technical_signals": agent_result["agent_signals"]}

            return {}

        except Exception as e:
            logger.exception("Error in technical analysis: %s", e)
            return state


class SentimentAnalysisNode(BaseNode):
    """Node for performing sentiment analysis using crypto sentiment agent."""

    def __init__(self):
        super().__init__(
            name="sentiment_analysis", description="Performs sentiment analysis using crypto sentiment agent"
        )

    def get_required_data(self) -> list[str]:
        return ["symbols", "news_data"]

    def get_output_data(self) -> list[str]:
        return ["sentiment_signals"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute sentiment analysis using the crypto sentiment agent.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state with sentiment signals from agent
        """
        try:
            # Enhanced state structure - data is directly in state
            symbols = state.get("symbols", [])
            logger.info("Running sentiment analysis agent on %s symbols", len(symbols))

            # Use existing news data from DataCollectionNode
            # Social data collection is disabled (temporarily)
            news_data = state.get("news_data", {})

            logger.info(
                "Using existing news data from DataCollectionNode (news_count=%d)",
                len(news_data),
            )

            # Add existing data to state for agent to use
            state["enhanced_sentiment_data"] = {
                symbol: {
                    "news": news_data.get(symbol, {}),
                }
                for symbol in symbols
            }

            # Run the crypto sentiment analysis agent
            agent_result = self.execute_agent_safely("crypto_sentiment", state)

            # Return only the fields we updated
            if "agent_signals" in agent_result:
                return {"sentiment_signals": agent_result["agent_signals"]}

            return {}

        except Exception as e:
            logger.exception("Error in sentiment analysis: %s", e)
            return state
