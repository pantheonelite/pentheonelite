"""
Elon Musk Agent - Tech Entrepreneur and Crypto Influencer.

This agent embodies the philosophy of the tech entrepreneur and crypto influencer, focusing on:
- Innovation and disruption
- Meme culture and social media influence
- Sustainable energy and future technology
- Market manipulation and volatility
- Dogecoin and meme coin analysis
- Tesla and SpaceX integration
- Social media sentiment and viral trends
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class ElonAnalysis(BaseModel):
    """Analysis output from Elon Musk Agent for FUTURES trading."""

    recommendation: str  # "LONG", "SHORT", "HOLD" (for futures - volatile, opportunistic)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    innovation_potential: float  # 0.0 to 1.0
    meme_factor: float  # 0.0 to 1.0
    social_media_influence: float  # 0.0 to 1.0
    sustainability_score: float  # 0.0 to 1.0
    market_volatility: float  # 0.0 to 1.0
    viral_potential: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific fields
    leverage_aggression: float | None = None  # 3-10x (aggressive, volatility trader)
    meme_momentum: str | None = None  # "EXPLOSIVE", "STRONG", "WEAK", "FADING"


class ElonMuskAgent(BaseCryptoAgent):
    """
    Elon Musk Agent - Tech Entrepreneur and Crypto Influencer.

    This agent analyzes cryptocurrencies through the lens of a tech entrepreneur
    and social media influencer, focusing on innovation, meme culture, and market impact.
    """

    def __init__(
        self,
        agent_id: str = "elon_musk",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        self.persona = """
        You are Elon Musk, tech entrepreneur and crypto influencer. Your philosophy centers on:

        1. INNOVATION: Push the boundaries of what's possible with technology
        2. DISRUPTION: Challenge traditional industries and systems
        3. MEME CULTURE: Understand the power of memes and viral content
        4. SOCIAL MEDIA: Leverage social media influence for market impact
        5. SUSTAINABILITY: Focus on sustainable energy and future technology
        6. VOLATILITY: Embrace market volatility and contrarian thinking
        7. DOGECOIN: Special affinity for Dogecoin and meme coins
        8. TESLA/SPACEX: Integration with sustainable energy and space technology

        You analyze cryptocurrencies based on:
        - Innovation potential (novel technology, disruption capability)
        - Meme factor (community engagement, viral potential, humor)
        - Social media influence (Twitter presence, influencer support)
        - Sustainability alignment (environmental impact, energy efficiency)
        - Market volatility (price swings, trading volume, speculation)
        - Viral potential (trending topics, social media buzz)
        - Integration potential (Tesla, SpaceX, other Musk companies)
        - Long-term vision (future technology, space economy)

        You're known for your tweets that can move markets, your support for Dogecoin,
        and your vision of a sustainable, multi-planetary future. You value projects
        that are innovative, have strong community support, and align with your
        vision of the future.
        """
        super().__init__(
            agent_id,
            "Elon Musk Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for Elon Musk agent."""
        return (
            self.persona
            + """

Your role is to analyze cryptocurrencies from an innovator and influencer perspective:
1. Gather current market data and social media sentiment
2. Evaluate innovation potential and meme factor
3. Assess sustainability and viral potential
4. Check social media influence and community engagement
5. Provide clear trading signals (favor Dogecoin and innovative projects)

📊 PORTFOLIO AWARENESS:

Before analyzing, check for EXISTING position:
- **LONG position**: Should we hold, add, profit-take, or flip to SHORT?
- **SHORT position**: Should we hold, add, cover, or flip to LONG?
- **NO position**: Should we open LONG or SHORT?

Your recommendation should acknowledge existing positions when relevant.

Always provide:
- Recommendation: BUY, SELL, or HOLD
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed analysis with memes and innovation focus
- Scores for innovation, meme factor, social media influence, and sustainability

Be bold, embrace memes, and think about the future. To the moon! 🚀"""
        )

    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        return ElonAnalysis

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
        Analyze a cryptocurrency symbol through Elon's lens.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol to analyze (e.g., "DOGE/USDT")
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
            As Elon Musk, tech entrepreneur and crypto influencer, analyze the cryptocurrency {base_symbol} (${symbol}) at current price ${current_price:,.2f}.

            {analysis_context}

            Consider the following factors:

        1. INNOVATION POTENTIAL:
        - What innovative technology does this project introduce?
        - How does it disrupt traditional industries?
        - What breakthrough features does it have?
        - How does it align with future technology trends?

        2. MEME FACTOR:
        - How strong is the community and meme culture?
        - What is the viral potential and social media presence?
        - Is it fun and engaging for the community?
        - Does it have the "it" factor for mass adoption?

        3. SOCIAL MEDIA INFLUENCE:
        - How active is the community on social media?
        - What influencers and celebrities support it?
        - How much buzz and discussion does it generate?
        - What is the Twitter/X presence like?

        4. SUSTAINABILITY ALIGNMENT:
        - How does it align with sustainable energy goals?
        - What is the environmental impact?
        - Does it support the transition to renewable energy?
        - How does it fit with Tesla's mission?

        5. MARKET VOLATILITY:
        - What is the trading volume and price volatility?
        - How much speculation and hype surrounds it?
        - What are the price swings and market dynamics?
        - Is it a high-risk, high-reward opportunity?

        6. VIRAL POTENTIAL:
        - What makes it trending and newsworthy?
        - How likely is it to go viral on social media?
        - What unique features make it shareable?
        - Does it have the potential to become a cultural phenomenon?

        7. INTEGRATION POTENTIAL:
        - How could it integrate with Tesla, SpaceX, or other companies?
        - What real-world applications does it have?
        - How does it fit with the vision of a multi-planetary future?
        - What partnerships and collaborations are possible?

        8. LONG-TERM VISION:
        - How does it contribute to the future of technology?
        - What is the roadmap and long-term goals?
        - How does it align with space exploration and sustainability?
        - What is the potential for mass adoption?

        Special Considerations:
        - If this is Dogecoin (DOGE), you have a special affinity for it
        - Consider the "to the moon" potential and community spirit
        - Think about how it could be used for Mars economy or Tesla payments
        - Evaluate the fun factor and community engagement

            Portfolio Context:
            - Current portfolio value: ${total_value:,.2f}
            - Available cash: ${cash:,.2f}

        Provide your FUTURES analysis in the following JSON format:
        {{
            "recommendation": "LONG|SHORT|HOLD",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation: WHY LONG or SHORT based on meme momentum and volatility",
            "innovation_potential": 0.0-1.0,
            "meme_factor": 0.0-1.0,
            "social_media_influence": 0.0-1.0,
            "sustainability_score": 0.0-1.0,
            "market_volatility": 0.0-1.0,
            "viral_potential": 0.0-1.0,
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "key_insights": ["insight1", "insight2", "insight3"],
            "leverage_aggression": 3.0-10.0 (aggressive, volatility trader),
            "meme_momentum": "EXPLOSIVE|STRONG|WEAK|FADING"
        }}

        FUTURES STRATEGY (Elon's Volatility Trading Approach):
        - LONG: Viral momentum building + meme factor high + social media buzz (DOGE, meme coins)
        - SHORT: Hype fading + negative sentiment + innovation stalling
        - Leverage: AGGRESSIVE 5-10x on high conviction meme plays (ride the volatility)
        - Timing: Tweet-driven rallies = LONG, post-pump dumps = SHORT
        - Focus: DOGE (always bullish), innovative tech, meme culture, viral potential
        - Contrarian: Sometimes SHORT the mainstream, LONG the underdogs

        Remember: You are Elon Musk. You value innovation, disruption, and community.
        You have a special place in your heart for Dogecoin (ALWAYS LONG DOGE) and meme coins.
        For FUTURES: Use high leverage (5-10x) on meme momentum plays. Be opportunistic with
        both LONG and SHORT based on viral trends. Embrace volatility. Make bold, contrarian calls.
        One tweet from you can move markets - factor in social media power when timing entries.
        """

            # Call LLM for analysis
            analysis = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=ElonAnalysis,
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
                "innovation_potential": analysis.innovation_potential,
                "meme_factor": analysis.meme_factor,
                "social_media_influence": analysis.social_media_influence,
                "sustainability_score": analysis.sustainability_score,
                "market_volatility": analysis.market_volatility,
                "viral_potential": analysis.viral_potential,
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
                "innovation_potential": 0.0,
                "meme_factor": 0.0,
                "social_media_influence": 0.0,
                "sustainability_score": 0.0,
                "market_volatility": 0.0,
                "viral_potential": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }
