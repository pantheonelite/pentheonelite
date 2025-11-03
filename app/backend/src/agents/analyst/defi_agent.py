"""DeFi Specialist Agent.

Provides DeFi-focused analysis considering TVL, yields, protocol risks,
and on-chain activity to issue a buy/sell/hold style recommendation.
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class DeFiSignal(BaseModel):
    """Signal output from DeFi specialist agent."""

    recommendation: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 - 1.0
    reasoning: str
    tvl_trend: float | None = None
    yield_opportunity: float | None = None
    protocol_risk: str | None = None  # low/medium/high
    onchain_activity: float | None = None


class DeFiAgent(BaseCryptoAgent):
    """DeFi specialist agent using an LLM for reasoning and output shaping."""

    def __init__(self, use_langchain: bool = False):
        super().__init__(agent_id="defi_agent", agent_name="DeFi Specialist", use_langchain=use_langchain)

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for DeFi agent."""
        return """You are a DeFi specialist analyzing cryptocurrencies from a decentralized finance perspective.

Your expertise includes:
- Total Value Locked (TVL) analysis
- Yield farming and staking opportunities
- Protocol risks (smart contract, liquidity, oracle risks)
- On-chain activity metrics
- DeFi protocol security and audits
- Liquidity pool dynamics

Your role is to analyze cryptocurrencies for DeFi opportunities:
1. Gather current price and TVL data
2. Evaluate yield opportunities and farming potential
3. Assess protocol risks and security
4. Check on-chain activity and usage
5. Provide clear trading signals

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Factor in current DeFi holdings.

Always provide:
- Recommendation: BUY, SELL, or HOLD
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed DeFi analysis
- TVL trend, yield opportunity, protocol risk, and on-chain activity scores

Focus on DeFi fundamentals and protocol health."""

    def _analyze_symbol_manual(self, symbol: str, state: CryptoAgentState) -> dict[str, Any]:
        """Generate DeFi analysis via LLM using a structured prompt and schema."""
        try:
            analysis_data: dict[str, Any] = {
                "symbol": symbol,
                "timeframe": state.get("timeframe", "1h"),
                "start_date": str(state.get("start_date")),
                "end_date": str(state.get("end_date")),
                # Optional scaffolding the LLM may use
                "onchain_metrics": {
                    "tvl_usd": None,
                    "tvl_trend": None,
                    "active_addresses": None,
                    "tx_volume": None,
                },
                "yield_data": {
                    "base_yield": None,
                    "boosted_yield": None,
                },
                "risk_indicators": {
                    "smart_contract_risk": None,
                    "liquidity_risk": None,
                    "oracle_risk": None,
                },
            }

            result = self.generate_llm_analysis(symbol, analysis_data, state)
            return result.model_dump()
        except Exception as e:
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": f"Error in DeFi analysis: {e!s}",
                "error": str(e),
            }

    def get_signal_model(self) -> type[BaseModel]:
        return DeFiSignal

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are a DeFi specialist. Analyze a crypto symbol from a DeFi perspective and "
                        "produce an actionable signal. Your output MUST exactly match the schema fields.\n\n"
                        "FIELDS:\n"
                        "- recommendation: one of BUY, SELL, HOLD\n"
                        "- confidence: float 0.0..1.0\n"
                        "- reasoning: concise DeFi rationale\n"
                        "- tvl_trend: float -1.0..+1.0 or null\n"
                        "- yield_opportunity: float 0.0..1.0 or null\n"
                        "- protocol_risk: one of low, medium, high\n"
                        "- onchain_activity: float 0.0..1.0 or null\n\n"
                        "Consider TVL, liquidity, smart contract/oracle risks, yields/emissions, governance, "
                        "composability, and on-chain activity. If data is insufficient, return HOLD with moderate confidence."
                    ),
                ),
                (
                    "human",
                    (
                        "Symbol: {symbol}\n"
                        "Context JSON (optional scaffolding):\n{analysis_data}\n\n"
                        "Return ONLY the schema fields."
                    ),
                ),
            ]
        )
