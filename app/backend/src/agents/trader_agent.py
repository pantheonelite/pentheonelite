"""Refactored cryptocurrency trader agent using OOP design patterns."""

import json
from typing import Any, Literal

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.tools.crypto import AsterPriceTool, VolumeAnalysisTool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class CryptoTraderSignal(BaseModel):
    """Signal output from crypto trader agent."""

    signal: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    confidence: float  # 0-100
    reasoning: str
    investment_plan: str | None = None
    position_size: float | None = None
    entry_price: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    time_horizon: str | None = None
    risk_reward_ratio: float | None = None
    key_factors: list[str] = []
    warnings: list[str] = []
    past_lessons: list[str] = []


class CryptoTraderAgent(BaseCryptoAgent):
    """Cryptocurrency trader agent for making trading decisions."""

    def __init__(self):
        super().__init__(agent_id="crypto_trader_agent", agent_name="Crypto Trader")

        # Initialize tools
        self.price_tool = AsterPriceTool()
        self.volume_tool = VolumeAnalysisTool()

    def analyze_symbol(self, symbol: str, state: CryptoAgentState) -> dict[str, Any]:
        """
        Analyze trading opportunity for a single crypto symbol.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        dict[str, Any]
            Trading decision and analysis results for the symbol
        """
        try:
            data = state["data"]
            portfolio = data.get("portfolio", {})

            # Gather analysis reports from state
            analysis_reports = self._gather_analysis_reports(state)

            # Get current market data
            market_data = self._get_current_market_data(symbol)

            # Retrieve past trading memories for learning
            past_memories = self._get_past_memories(symbol, analysis_reports, state)

            # Compile trading data
            trading_data = {
                "symbol": symbol,
                "market_data": market_data,
                "analysis_reports": analysis_reports,
                "past_memories": past_memories,
                "portfolio": portfolio,
            }

            # Generate comprehensive trading decision using LLM
            trader_output = self.generate_llm_analysis(symbol, trading_data, state)

            return trader_output.model_dump()

        except Exception as e:
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": f"Error in trading analysis: {e!s}",
                "warnings": [f"Trading analysis failed: {e!s}"],
                "error": str(e),
            }

    def get_signal_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the agent's signal output."""
        return CryptoTraderSignal

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """Get the LLM prompt template for generating trading decision."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a professional cryptocurrency trader with expertise in:
                - Technical and fundamental analysis
                - Market sentiment interpretation
                - Risk-adjusted position sizing
                - Entry and exit strategy development
                - Portfolio management and diversification

                Your role is to synthesize insights from multiple analysts and make concrete trading decisions.

                Consider these key factors:
                - Market trends and momentum
                - Support and resistance levels
                - Volume and liquidity patterns
                - Sentiment indicators
                - Fundamental catalysts
                - Risk management parameters
                - Portfolio exposure and diversification

                Learn from past trading decisions to avoid repeating mistakes and capitalize on successful strategies.

                Always provide:
                - Clear BUY/HOLD/SELL signal with confidence level
                - Specific entry price, target price, and stop loss
                - Position sizing recommendation
                - Risk-reward ratio assessment
                - Time horizon for the trade
                - Key factors supporting the decision
                - Relevant warnings or concerns

                Return ONLY the JSON specified below.""",
                ),
                (
                    "human",
                    """Cryptocurrency: {symbol}

                Trading Analysis Data:
                {analysis_data}

                Respond EXACTLY in this JSON schema:
                {{
                  "signal": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
                  "confidence": float (0-100),
                  "reasoning": "string",
                  "investment_plan": "string" | null,
                  "position_size": float | null,
                  "entry_price": float | null,
                  "target_price": float | null,
                  "stop_loss": float | null,
                  "time_horizon": "string" | null,
                  "risk_reward_ratio": float | null,
                  "key_factors": ["string"],
                  "warnings": ["string"],
                  "past_lessons": ["string"]
                }}""",
                ),
            ]
        )

    def _gather_analysis_reports(self, state: CryptoAgentState) -> dict[str, Any]:
        """Gather analysis reports from various agents in state."""
        data = state.get("data", {})
        messages = state.get("messages", [])

        reports = {
            "investment_plan": data.get("investment_plan", ""),
            "market_report": data.get("market_report", ""),
            "sentiment_report": data.get("sentiment_report", ""),
            "news_report": data.get("news_report", ""),
            "fundamentals_report": data.get("fundamentals_report", ""),
            "risk_assessment": data.get("risk_assessment", ""),
        }

        # Extract analyst messages if available
        analyst_messages = []
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                analyst_messages.append(msg.content)

        reports["analyst_insights"] = "\n\n".join(analyst_messages) if analyst_messages else ""

        return reports

    def _get_current_market_data(self, symbol: str) -> dict[str, Any]:
        """Get current market data for the symbol."""
        try:
            price_data = json.loads(self.price_tool._run(symbol, "aster"))
            
            return {
                "current_price": price_data.get("price", 0),
                "change_24h": price_data.get("change_percent_24h", 0),
                "high_24h": price_data.get("high_24h", 0),
                "low_24h": price_data.get("low_24h", 0),
                "volume_24h": price_data.get("volume", 0),
                "market_cap": price_data.get("market_cap"),
            }
        except Exception as e:
            return {
                "current_price": 0,
                "error": f"Failed to fetch market data: {e!s}",
            }

    def _get_past_memories(
        self, symbol: str, analysis_reports: dict[str, Any], state: CryptoAgentState
    ) -> list[dict[str, Any]]:
        """Retrieve past trading memories for learning from history."""
        try:
            # Get memory system from state if available
            memory = state.get("memory")
            if not memory:
                return []

            # Create context from current situation
            curr_situation = "\n\n".join(
                [
                    str(report)
                    for report in analysis_reports.values()
                    if report and isinstance(report, str)
                ]
            )

            # Retrieve similar past trading situations
            past_memories = memory.get_memories(curr_situation, n_matches=3)

            memories = []
            if past_memories:
                for i, rec in enumerate(past_memories, 1):
                    memories.append(
                        {
                            "decision": rec.get("decision", "N/A"),
                            "outcome": rec.get("outcome", "N/A"),
                            "lesson": rec.get("lesson", "N/A"),
                            "recommendation": rec.get("recommendation", "N/A"),
                        }
                    )

            return memories

        except Exception as e:
            return [{"error": f"Failed to retrieve memories: {e!s}"}]

    def _calculate_position_metrics(
        self, current_price: float, target_price: float, stop_loss: float
    ) -> dict[str, float]:
        """Calculate position metrics like risk-reward ratio."""
        if not all([current_price, target_price, stop_loss]):
            return {}

        potential_gain = target_price - current_price
        potential_loss = current_price - stop_loss

        risk_reward_ratio = (
            abs(potential_gain / potential_loss) if potential_loss != 0 else 0
        )

        return {
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "potential_gain_percent": round((potential_gain / current_price) * 100, 2),
            "potential_loss_percent": round((potential_loss / current_price) * 100, 2),
        }


# Create a global instance for backward compatibility
crypto_trader_agent_instance = CryptoTraderAgent()


def crypto_trader_agent(state: CryptoAgentState, agent_id: str = "crypto_trader_agent"):
    """
    Legacy function wrapper for backward compatibility.

    Parameters
    ----------
    state : CryptoAgentState
        The current agent state
    agent_id : str
        Agent identifier

    Returns
    -------
    dict[str, Any]
        Updated state with agent results
    """
    return crypto_trader_agent_instance.run_agent(state)
