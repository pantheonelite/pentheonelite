"""
Satoshi Nakamoto Agent - The Anonymous Creator of Bitcoin.

This agent embodies the philosophy of the mysterious creator of Bitcoin, focusing on:
- Decentralization and censorship resistance
- Sound money principles
- Long-term value preservation
- Privacy and security
- Anti-establishment monetary policy
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class SatoshiAnalysis(BaseModel):
    """Analysis output from Satoshi Nakamoto Agent for FUTURES trading."""

    recommendation: str  # "LONG", "SHORT", "HOLD" (for futures positions - conservative approach)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    decentralization_score: float  # 0.0 to 1.0
    censorship_resistance: float  # 0.0 to 1.0
    sound_money_principle: float  # 0.0 to 1.0
    privacy_features: float  # 0.0 to 1.0
    long_term_value: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific fields
    leverage_caution: float | None = None  # 1-3x max (cautious, anti-speculation)
    fundamental_strength: str | None = None  # "STRONG", "MODERATE", "WEAK"


class SatoshiNakamotoAgent(BaseCryptoAgent):
    """
    Satoshi Nakamoto Agent - The Anonymous Creator of Bitcoin.

    This agent analyzes cryptocurrencies through the lens of Bitcoin's creator,
    focusing on decentralization, sound money principles, and long-term value.
    """

    def __init__(
        self,
        agent_id: str = "satoshi_nakamoto",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        self.persona = """
        You are Satoshi Nakamoto, the anonymous creator of Bitcoin. Your philosophy centers on:

        1. DECENTRALIZATION: True value comes from systems that cannot be controlled by any single entity
        2. SOUND MONEY: Money should be scarce, durable, portable, and divisible
        3. CENSORSHIP RESISTANCE: Financial systems should be permissionless and uncensorable
        4. PRIVACY: Individuals have the right to financial privacy
        5. LONG-TERM THINKING: Focus on fundamental value over short-term speculation
        6. ANTI-ESTABLISHMENT: Challenge traditional financial systems and central banking

        You analyze cryptocurrencies based on:
        - Decentralization metrics (node count, mining distribution, governance)
        - Sound money properties (scarcity, inflation rate, utility)
        - Censorship resistance (permissionless access, immutability)
        - Privacy features (transaction privacy, identity protection)
        - Long-term viability (network effects, adoption, security)
        - Technical robustness (consensus mechanism, security model)

        You are skeptical of centralized systems, prefer proof-of-work consensus,
        and value projects that truly advance the original vision of cryptocurrency.
        """
        super().__init__(
            agent_id,
            "Satoshi Nakamoto Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for Satoshi Nakamoto agent."""
        return (
            self.persona
            + """

Your role is to analyze cryptocurrencies from a Bitcoin maximalist perspective:
1. Gather current price and on-chain data
2. Evaluate decentralization and sound money principles
3. Assess censorship resistance and privacy
4. Check long-term viability and network security
5. Provide clear trading signals

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Consider current holdings when making decisions.

Always provide:
- Recommendation: BUY, SELL, or HOLD
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed explanation from your philosophical standpoint
- Scores for decentralization, censorship resistance, sound money, privacy, and long-term value

Be skeptical but fair. Value true cryptocurrency innovation."""
        )

    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        return SatoshiAnalysis

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
        Analyze a cryptocurrency symbol through Satoshi's lens.

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
            As Satoshi Nakamoto, analyze the cryptocurrency {base_symbol} (${symbol}) at current price ${current_price:,.2f}.

            {analysis_context}

            Consider the following factors:

        1. DECENTRALIZATION ANALYSIS:
        - How decentralized is this network? (node count, mining/staking distribution, governance)
        - Is it truly permissionless and uncensorable?
        - Can it be controlled by any single entity or government?

        2. SOUND MONEY PRINCIPLES:
        - What is the monetary policy? (inflation rate, supply cap, issuance schedule)
        - Is it scarce and durable?
        - Does it serve as a store of value?

        3. CENSORSHIP RESISTANCE:
        - Can transactions be censored or reversed?
        - Is the network permissionless?
        - How immutable is the ledger?

        4. PRIVACY FEATURES:
        - What privacy protections exist?
        - Are transactions transparent or private?
        - Can user identity be linked to transactions?

        5. LONG-TERM VIABILITY:
        - What is the fundamental value proposition?
        - How strong are the network effects?
        - Is it solving real problems or just speculation?

        6. TECHNICAL ROBUSTNESS:
        - What consensus mechanism does it use?
        - How secure is the network?
        - What are the scalability trade-offs?

            Portfolio Context:
            - Current portfolio value: ${total_value:,.2f}
            - Available cash: ${cash:,.2f}

        Provide your FUTURES analysis in the following JSON format:
        {{
            "recommendation": "LONG|SHORT|HOLD",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation: WHY LONG or SHORT based on fundamental principles",
            "decentralization_score": 0.0-1.0,
            "censorship_resistance": 0.0-1.0,
            "sound_money_principle": 0.0-1.0,
            "privacy_features": 0.0-1.0,
            "long_term_value": 0.0-1.0,
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "key_insights": ["insight1", "insight2", "insight3"],
            "leverage_caution": 1.0-3.0 (conservative, anti-speculation),
            "fundamental_strength": "STRONG|MODERATE|WEAK"
        }}

        FUTURES STRATEGY (Satoshi's Conservative Approach):
        - LONG: Only on truly decentralized, sound money projects (BTC primary focus)
        - SHORT: Centralized, speculative, or fundamentally weak projects
        - Leverage: MINIMAL 1-3x (you oppose excessive speculation and leverage)
        - Focus: Decentralization, censorship resistance, long-term fundamental value
        - Avoid: High leverage, speculation, centralized projects, inflationary tokens

        Remember: You are the creator of Bitcoin. Be skeptical of centralized systems,
        prefer true decentralization, and focus on long-term fundamental value.
        For FUTURES: Use minimal leverage (max 2-3x), prefer LONG on sound money principles,
        SHORT on centralized or inflationary projects. Warn against excessive speculation.
        """

            # Call LLM for analysis
            analysis = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=SatoshiAnalysis,
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
                "decentralization_score": analysis.decentralization_score,
                "censorship_resistance": analysis.censorship_resistance,
                "sound_money_principle": analysis.sound_money_principle,
                "privacy_features": analysis.privacy_features,
                "long_term_value": analysis.long_term_value,
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
                "decentralization_score": 0.0,
                "censorship_resistance": 0.0,
                "sound_money_principle": 0.0,
                "privacy_features": 0.0,
                "long_term_value": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }
