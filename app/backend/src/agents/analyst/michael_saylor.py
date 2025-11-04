"""
Michael Saylor Agent - Bitcoin Maximalist and MicroStrategy CEO.

This agent embodies the philosophy of the Bitcoin maximalist, focusing on:
- Bitcoin as the only true digital asset
- Corporate treasury adoption
- Long-term value preservation
- Inflation hedge and store of value
- Network effects and adoption
- Regulatory clarity and institutional acceptance
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class SaylorAnalysis(BaseModel):
    """Analysis output from Michael Saylor Agent for FUTURES trading."""

    recommendation: str  # "LONG", "SHORT", "HOLD" (for futures positions - LONG bias for BTC)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    bitcoin_maximalism: float  # 0.0 to 1.0
    corporate_adoption: float  # 0.0 to 1.0
    store_of_value: float  # 0.0 to 1.0
    inflation_hedge: float  # 0.0 to 1.0
    network_effects: float  # 0.0 to 1.0
    regulatory_clarity: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific fields
    leverage_conviction: float | None = None  # 5-10x for BTC (high conviction), 1-2x for altcoins (skeptical)
    macro_timing: str | None = None  # "ACCUMULATE", "HOLD", "REDUCE" based on macro conditions


class MichaelSaylorAgent(BaseCryptoAgent):
    """
    Michael Saylor Agent - Bitcoin Maximalist and MicroStrategy CEO.

    This agent analyzes cryptocurrencies through the lens of a Bitcoin maximalist,
    focusing on Bitcoin's unique properties and corporate adoption potential.
    """

    def __init__(
        self,
        agent_id: str = "michael_saylor",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        self.persona = """
        You are Michael Saylor, CEO of MicroStrategy and Bitcoin maximalist. Your philosophy centers on:

        1. BITCOIN SUPREMACY: Bitcoin is the only true digital asset worth holding
        2. STORE OF VALUE: Digital property that preserves purchasing power over time
        3. CORPORATE ADOPTION: Encourage companies to hold Bitcoin as a treasury reserve asset
        4. HARD MONEY: Bitcoin as a solution to monetary inflation and currency debasement
        5. LONG-TERM HOLDING: Time in the market beats timing the market
        6. NETWORK EFFECTS: Bitcoin's network effects make it the clear winner

        You analyze cryptocurrencies based on:
        - Bitcoin only - you are extremely skeptical of altcoins
        - Institutional adoption and corporate treasury strategy
        - Macro-economic factors (inflation, monetary policy, fiat devaluation)
        - Network security and hash rate
        - Regulatory clarity and acceptance
        - Long-term price appreciation potential

        You are vocal, passionate, and unwavering in your Bitcoin conviction.
        You see Bitcoin as the apex property of the human race and the solution
        to monetary inflation.
        """
        super().__init__(
            agent_id,
            "Michael Saylor Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for Michael Saylor agent."""
        return (
            self.persona
            + """

Your role is to analyze cryptocurrencies from a Bitcoin maximalist perspective:
1. Gather current price and adoption data
2. Evaluate store of value properties
3. Assess corporate adoption potential
4. Check network effects and institutional acceptance
5. Provide clear trading signals (heavily favor Bitcoin)

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Factor in current holdings and PnL when making decisions.

Always provide:
- Recommendation: BUY (for Bitcoin), HOLD, or SELL
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed maximalist analysis
- Scores for Bitcoin maximalism, corporate adoption, store of value, and network effects

Be extremely bullish on Bitcoin and skeptical of all other cryptocurrencies."""
        )

    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        return SaylorAnalysis

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """
        Get the LLM prompt template for generating analysis.

        Returns
        -------
        ChatPromptTemplate
            LangChain prompt template
        """
        return ChatPromptTemplate.from_messages(
            [
                ("system", self.persona),
                ("user", "{analysis_data}"),
            ]
        )

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, _progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a cryptocurrency symbol through Saylor's lens.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state with market data

        Returns
        -------
        dict[str, Any]
            Analysis results including recommendation and reasoning
        """
        try:
            # Extract symbol without exchange suffix
            base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

            # Get data from the state (collected by data_collection node)
            price_data = state.get("price_data", {}).get(symbol, {})
            volume_data = state.get("volume_data", {}).get(symbol, {})
            news_data = state.get("news_data", {}).get(symbol, {})

            # Get portfolio data
            portfolio = state.get("data", {}).get("portfolio", {})
            total_value = portfolio.get("total_value", 0)
            cash = portfolio.get("cash", 0)

            # Extract key metrics from collected data
            if hasattr(price_data, "price"):
                # PriceData object - access attributes directly
                current_price = price_data.price
                volume_24h = price_data.volume
                change_percent_24h = price_data.change_percent_24h
                high_24h = price_data.high_24h
                low_24h = price_data.low_24h
            else:
                # Dictionary - use get method
                current_price = price_data.get("price", 0)
                volume_24h = price_data.get("volume", 0)
                change_percent_24h = price_data.get("change_percent_24h", 0)
                high_24h = price_data.get("high_24h", 0)
                low_24h = price_data.get("low_24h", 0)

            # Get volume metrics from volume_data
            current_volume = volume_data.get("current_volume", 0)
            avg_volume = volume_data.get("avg_volume", 0)
            volume_trend = volume_data.get("volume_trend", "unknown")

            # Get news sentiment from news_data
            news_count = news_data.get("news_count", 0)
            headlines = news_data.get("headlines", [])

            # Build analysis context using collected data
            analysis_context = f"""
            Market Data for {symbol}:

            PRICE METRICS:
            - Current Price: ${current_price:,.2f}
            - 24h Change: {change_percent_24h:,.2f}%
            - 24h High: ${high_24h:,.2f}
            - 24h Low: ${low_24h:,.2f}

            VOLUME METRICS:
            - Current Volume: ${current_volume:,.2f}
            - Average Volume: ${avg_volume:,.2f}
            - Volume Trend: {volume_trend}

            NEWS METRICS:
            - News Count: {news_count}
            - Recent Headlines: {headlines[:3] if headlines else "None"}

            MARKET SENTIMENT:
            - Price Trend: {"uptrend" if change_percent_24h > 0 else "downtrend" if change_percent_24h < 0 else "sideways"}
            - Volume Activity: {"high" if current_volume > avg_volume * 1.2 else "low" if current_volume < avg_volume * 0.8 else "normal"}
            - Market Interest: {"high" if news_count > 5 else "low" if news_count < 2 else "moderate"}
            """

            # Create analysis prompt
            prompt = f"""
            As Michael Saylor, Bitcoin maximalist and CEO of MicroStrategy, analyze the cryptocurrency {base_symbol} (${symbol}) at current price ${current_price:,.2f}.

            {analysis_context}

            Consider the following factors:

            1. BITCOIN MAXIMALISM:
            - Is this Bitcoin or an inferior alternative?
            - How does it compare to Bitcoin's properties?
            - What makes it different from Bitcoin?

            2. CORPORATE ADOPTION:
            - Would corporations add this to their treasury?
            - What are the accounting and regulatory implications?
            - How does it compare to Bitcoin for corporate use?

            3. STORE OF VALUE:
            - What is the monetary policy and supply cap?
            - How scarce and durable is this asset?
            - Can it serve as digital gold?

            4. INFLATION HEDGE:
            - How does it protect against monetary debasement?
            - What is the inflation rate and issuance schedule?
            - Is it a better hedge than Bitcoin?

            5. NETWORK EFFECTS:
            - How strong are the network effects?
            - What is the adoption rate and security model?
            - Can it compete with Bitcoin's network effects?

            6. REGULATORY CLARITY:
            - What is the legal status and regulatory framework?
            - How does it compare to Bitcoin's regulatory position?
            - What are the compliance requirements?

            7. INSTITUTIONAL ACCEPTANCE:
            - Are there custody solutions and insurance?
            - How do institutions view this asset?
            - What is the institutional adoption rate?

            8. LONG-TERM VIABILITY:
            - What are the fundamentals and technology?
            - How does the team and execution compare?
            - What is the long-term roadmap?

            Portfolio Context:
            - Current portfolio value: ${total_value:,.2f}
            - Available cash: ${cash:,.2f}

            Provide your FUTURES analysis in the following JSON format:
            {{
                "recommendation": "LONG|SHORT|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "Detailed explanation: WHY LONG or SHORT based on Bitcoin maximalist perspective",
                "bitcoin_maximalism": 0.0-1.0,
                "corporate_adoption": 0.0-1.0,
                "store_of_value": 0.0-1.0,
                "inflation_hedge": 0.0-1.0,
                "network_effects": 0.0-1.0,
                "regulatory_clarity": 0.0-1.0,
                "risk_assessment": "LOW|MEDIUM|HIGH",
                "key_insights": ["insight1", "insight2", "insight3"],
                "leverage_conviction": 5.0-10.0 (high for BTC, 1-2x for altcoins),
                "macro_timing": "ACCUMULATE|HOLD|REDUCE"
            }}

            FUTURES STRATEGY (Saylor's Bitcoin Maximalist Approach):
            - BTC: ALWAYS LONG bias (5-10x leverage on conviction) - never SHORT Bitcoin
            - Altcoins: Skeptical SHORT bias (1-2x leverage, if trading at all)
            - Macro: HIGH inflation = STRONG LONG BTC, falling inflation = HOLD/reduce leverage
            - Corporate adoption news = LONG signal (MicroStrategy-style accumulation)
            - Network security at ATH = LONG signal (hash rate, nodes)
            - Regulatory clarity improving = LONG signal (institutional acceptance)

            Remember: You are a Bitcoin maximalist. You believe Bitcoin is the ONLY
            true digital asset worth holding. For FUTURES: Be AGGRESSIVELY LONG on Bitcoin
            (especially on dips), use 5-10x leverage with confidence. For altcoins, either
            HOLD (ignore) or SHORT (if forced to trade). Never recommend LONG on anything but Bitcoin.
            Focus on macro conditions (inflation, monetary policy) for leverage timing.
            """

            # Call LLM for analysis
            analysis = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=SaylorAnalysis,
                agent_name=self.agent_name,
                state=state,
            )

            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": analysis.recommendation.lower(),  # Convert to lowercase: buy/sell/hold
                "recommendation": analysis.recommendation,
                "confidence": analysis.confidence * 100,  # Convert to percentage (0-100)
                "reasoning": analysis.reasoning,
                "bitcoin_maximalism": analysis.bitcoin_maximalism,
                "corporate_adoption": analysis.corporate_adoption,
                "store_of_value": analysis.store_of_value,
                "inflation_hedge": analysis.inflation_hedge,
                "network_effects": analysis.network_effects,
                "regulatory_clarity": analysis.regulatory_clarity,
                "risk_assessment": analysis.risk_assessment,
                "key_insights": analysis.key_insights,
                "timestamp": self.get_current_timestamp(),
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": "hold",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e!s}",
                "bitcoin_maximalism": 0.0,
                "corporate_adoption": 0.0,
                "store_of_value": 0.0,
                "inflation_hedge": 0.0,
                "network_effects": 0.0,
                "regulatory_clarity": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }
