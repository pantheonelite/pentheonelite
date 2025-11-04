"""
Crypto Sentiment Agent - Market Sentiment Analysis.

This agent focuses on:
- News sentiment and market impact
- Fear and greed indicators
- Market psychology and behavioral analysis
- Web-based sentiment analysis
"""

from typing import Any

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState

# Twitter tools temporarily removed - will be implemented later
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class SentimentAnalysis(BaseModel):
    """Analysis output from Crypto Sentiment Agent for FUTURES trading."""

    sentiment: str  # "VERY_POSITIVE", "POSITIVE", "NEUTRAL", "NEGATIVE", "VERY_NEGATIVE"
    recommendation: str  # "LONG", "SHORT", "HOLD" (for futures positions)
    confidence: float  # 0.0 to 1.0
    reasoning: str
    social_sentiment: float  # 0.0 to 1.0
    news_sentiment: float  # 0.0 to 1.0
    fear_greed_index: float  # 0.0 to 1.0
    community_engagement: float  # 0.0 to 1.0
    influencer_impact: float  # 0.0 to 1.0
    market_psychology: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific sentiment fields
    leverage_sentiment: str | None = None  # "BULLISH_LEVERAGE", "BEARISH_LEVERAGE", "CAUTIOUS"
    funding_sentiment: str | None = None  # "LONG_EXPENSIVE", "SHORT_EXPENSIVE", "BALANCED"
    # Entry/Exit targets (sentiment-driven timing)
    entry_price: float | None = None  # Optimal entry based on sentiment extremes
    stop_loss: float | None = None  # Stop loss price
    take_profit_short: float | None = None  # Short-term TP (hours to 1-2 days)
    take_profit_mid: float | None = None  # Mid-term TP (3-7 days)
    take_profit_long: float | None = None  # Long-term TP (1-4 weeks)


class CryptoSentimentAgent(BaseCryptoAgent):
    """
    Crypto Sentiment Agent - Social Media and Market Sentiment Analysis.

    This agent analyzes cryptocurrencies through sentiment analysis,
    focusing on social media, news, and market psychology.
    """

    def __init__(
        self,
        agent_id: str = "crypto_sentiment",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        # Define persona before super().__init__() so _get_langchain_prompt() can access it
        self.persona = """
        You are a Crypto Sentiment Analyst specializing in market sentiment analysis. Your expertise includes:

        1. NEWS SENTIMENT: News articles, press releases, and media coverage
        2. FEAR AND GREED: Market psychology indicators and sentiment extremes
        3. MARKET PSYCHOLOGY: Behavioral analysis and sentiment cycles
        4. SENTIMENT INDICATORS: Various sentiment metrics and their interpretation

        You analyze cryptocurrencies based on:
        - News sentiment (positive/negative news coverage)
        - Fear and greed indicators (market psychology)
        - Community engagement (developer activity, community growth)
        - Influencer impact (key opinion leaders, thought leaders)
        - Market psychology (sentiment cycles, behavioral patterns)
        - Sentiment indicators (various sentiment metrics)

        You understand that sentiment can be a leading indicator of price movements
        and focus on identifying sentiment extremes and contrarian opportunities.
        """
        super().__init__(
            agent_id,
            "Crypto Sentiment Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for sentiment agent."""
        return (
            self.persona
            + """

Your role is to analyze cryptocurrency sentiment:
1. Gather news and social media sentiment data
2. Evaluate fear and greed indicators
3. Assess market psychology and behavioral patterns
4. Identify sentiment extremes and contrarian opportunities
5. Provide clear trading signals based on sentiment

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Factor in current sentiment alignment with holdings.

Always provide:
- Sentiment: VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, or VERY_NEGATIVE
- Recommendation: LONG, SHORT, or HOLD (for futures)
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed sentiment analysis
- Scores for social sentiment, news sentiment, fear/greed index, community engagement

Focus on sentiment as a leading indicator of price movements."""
        )

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, _progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a cryptocurrency symbol through sentiment analysis.

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
        # Get current market data from enhanced state
        portfolio = state.get("portfolio", {})

        # Extract symbol without exchange suffix
        base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

        # Get price data from state
        price_data = state.get("price_data", {})
        price_info = price_data.get(symbol, {})
        current_price = price_info.get("price", 0) if isinstance(price_info, dict) else 0

        # Get news data from state (already fetched in data collection node)
        news_data = state.get("news_data", {})
        news_info = news_data.get(symbol, {})

        # Get news data (raw headlines without sentiment - LLM will analyze)
        news_count = news_info.get("news_count", 0) if isinstance(news_info, dict) else 0
        headlines = news_info.get("headlines", []) if isinstance(news_info, dict) else []

        # Format headlines for LLM analysis (include title and description)
        headlines_str = (
            "\n".join(
                [
                    f"{i + 1}. {h.get('title', 'N/A')}\n   Description: {h.get('description', 'N/A')}\n   Source: {h.get('source', 'Unknown')}"
                    for i, h in enumerate(headlines[:10])
                ]
            )
            if headlines
            else "No news headlines available"
        )

        # Create analysis prompt with news data from state FOR FUTURES TRADING
        prompt = f"""
        As a Crypto FUTURES Sentiment Analyst, analyze the cryptocurrency {base_symbol}
        (${symbol}) at current price ${current_price:,.2f} for FUTURES trading (LONG/SHORT positions with leverage).

        NEWS DATA (Already collected - analyze sentiment from these headlines):
        - News Count: {news_count}
        - Headlines:
        {headlines_str}

        Consider the following sentiment factors for FUTURES TRADING:

        1. NEWS SENTIMENT (Futures Direction):
        - What is the tone of recent news coverage?
        - Are there any major announcements suggesting LONG (bullish) or SHORT (bearish) opportunities?
        - How is the media framing the project (positive = LONG bias, negative = SHORT bias)?
        - What are the key news narratives and their directional implications?

        2. FEAR AND GREED (Leverage Psychology):
        - What is the current market psychology?
        - Extreme GREED = potential SHORT opportunity (overbought, high funding rates)
        - Extreme FEAR = potential LONG opportunity (oversold, cheap funding)
        - Are we in a fear or greed phase for contrarian leveraged positions?
        - What are the sentiment extremes for high-leverage trades?

        3. MARKET PSYCHOLOGY (Funding Rates):
        - Strong bullish sentiment = positive funding rates = expensive to hold LONG
        - Strong bearish sentiment = negative funding rates = expensive to hold SHORT
        - Balanced sentiment = neutral funding = lower carry cost
        - What are the current market narratives (bullish/bearish)?
        - Are there sentiment cycles suggesting direction change?

        4. LEVERAGE SENTIMENT:
        - Is the market sentiment suggesting aggressive LONG leverage?
        - Is the market sentiment suggesting aggressive SHORT leverage?
        - Is the market cautious, suggesting lower leverage or HOLD?
        - What is the crowd doing (often wrong at extremes)?

        5. CONTRARIAN OPPORTUNITIES (For Futures):
        - Extreme positive sentiment = consider SHORT on resistance
        - Extreme negative sentiment = consider LONG on support
        - What are the contrarian signals for leveraged positions?
        - Are there sentiment reversals for directional trades?

        Portfolio Context:
        - Current portfolio value: ${portfolio.get("total_value", 0):,.2f}
        - Available margin: ${portfolio.get("cash", 0):,.2f}

        Provide your FUTURES sentiment analysis in the following JSON format:
        {{
            "sentiment": "VERY_POSITIVE|POSITIVE|NEUTRAL|NEGATIVE|VERY_NEGATIVE",
            "recommendation": "LONG|SHORT|HOLD",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation: WHY LONG or SHORT based on sentiment",
            "social_sentiment": 0.0-1.0,
            "news_sentiment": 0.0-1.0,
            "fear_greed_index": 0.0-1.0,
            "community_engagement": 0.0-1.0,
            "influencer_impact": 0.0-1.0,
            "market_psychology": 0.0-1.0,
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "key_insights": ["insight1", "insight2", "insight3"],
            "leverage_sentiment": "BULLISH_LEVERAGE|BEARISH_LEVERAGE|CAUTIOUS",
            "funding_sentiment": "LONG_EXPENSIVE|SHORT_EXPENSIVE|BALANCED",
            "entry_price": float (optimal entry based on sentiment timing),
            "stop_loss": float (3-5% from entry based on sentiment volatility),
            "take_profit_short": float (short-term target based on sentiment momentum),
            "take_profit_mid": float (mid-term target based on sentiment trend),
            "take_profit_long": float (long-term target based on sentiment cycle)
        }}

        ENTRY/EXIT BASED ON SENTIMENT (CRITICAL):
        - Contrarian Entry: Enter LONG at extreme negative sentiment (fear), SHORT at extreme positive (greed)
        - Momentum Entry: Enter LONG at rising positive sentiment, SHORT at declining sentiment
        - Stop Loss: Wider (4-5%) during high sentiment volatility, tighter (3%) during stable periods
        - Short-term TP: Based on sentiment momentum shift (hours to 1-2 days)
        - Mid-term TP: Based on sentiment trend reversal signals (3-7 days)
        - Long-term TP: Based on complete sentiment cycle (1-4 weeks)

        EXAMPLE for CONTRARIAN LONG at current $50,000 with extreme fear:
        entry_price: $49,000 (enter during panic selling), stop_loss: $47,500 (3% below),
        take_profit_short: $51,000 (relief rally), take_profit_mid: $53,500 (sentiment recovery),
        take_profit_long: $57,000 (full sentiment reversal to greed)

        CRITICAL FOR FUTURES SENTIMENT:
        - LONG = bullish sentiment, profit when price increases
        - SHORT = bearish sentiment, profit when price decreases
        - HOLD = mixed/unclear sentiment, wait for clearer signal
        - Extreme sentiment often precedes reversals (contrarian opportunity)
        - High positive sentiment = high funding rates = expensive LONG positions
        - High negative sentiment = negative funding = expensive SHORT positions

        CONFIDENCE GUIDANCE (based on news availability):
        - If news_count >= 5: Use HIGH confidence (0.7-0.9) - plenty of data to analyze
        - If news_count >= 3: Use MEDIUM confidence (0.5-0.7) - reasonable data
        - If news_count >= 1: Use LOW-MEDIUM confidence (0.3-0.5) - limited data
        - If news_count = 0: Use LOW confidence (0.0-0.2) - no data available

        Remember: Sentiment analysis for FUTURES means identifying directional bias (LONG/SHORT)
        and understanding funding rate implications. Be contrarian at extremes.

        CRITICAL: You MUST respond with valid JSON matching this exact structure:
        {{
            "sentiment": "VERY_POSITIVE" | "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "VERY_NEGATIVE",
            "recommendation": "LONG" | "SHORT" | "HOLD",
            "confidence": 0.0-1.0,
            "reasoning": "string explaining your sentiment analysis",
            "social_sentiment": 0.0-1.0,
            "news_sentiment": 0.0-1.0,
            "fear_greed_index": 0.0-1.0,
            "community_engagement": 0.0-1.0,
            "influencer_impact": 0.0-1.0,
            "market_psychology": 0.0-1.0,
            "risk_assessment": "string",
            "key_insights": ["string", "string"],
            "leverage_sentiment": "BULLISH_LEVERAGE" | "BEARISH_LEVERAGE" | "CAUTIOUS" or null,
            "funding_sentiment": "LONG_EXPENSIVE" | "SHORT_EXPENSIVE" | "BALANCED" or null,
            "entry_price": number or null,
            "stop_loss": number or null,
            "take_profit_short": number or null,
            "take_profit_mid": number or null,
            "take_profit_long": number or null
        }}

        Return ONLY valid JSON, no other text before or after.
        """

        try:
            # Call LLM for analysis
            analysis = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=SentimentAnalysis,
                agent_name=self.agent_name,
                state=state,
            )

            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "sentiment": analysis.sentiment,
                "signal": analysis.recommendation,
                "recommendation": analysis.recommendation,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "social_sentiment": analysis.social_sentiment,
                "news_sentiment": analysis.news_sentiment,
                "fear_greed_index": analysis.fear_greed_index,
                "community_engagement": analysis.community_engagement,
                "influencer_impact": analysis.influencer_impact,
                "market_psychology": analysis.market_psychology,
                "risk_assessment": analysis.risk_assessment,
                "key_insights": analysis.key_insights,
                "timestamp": self.get_current_timestamp(),
                # Futures-specific sentiment fields
                "leverage_sentiment": analysis.leverage_sentiment,
                "funding_sentiment": analysis.funding_sentiment,
                # Entry/Exit targets
                "entry_price": analysis.entry_price,
                "stop_loss": analysis.stop_loss,
                "take_profit_short": analysis.take_profit_short,
                "take_profit_mid": analysis.take_profit_mid,
                "take_profit_long": analysis.take_profit_long,
            }

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": "HOLD",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e!s}",
                "social_sentiment": 0.0,
                "news_sentiment": 0.0,
                "fear_greed_index": 0.0,
                "community_engagement": 0.0,
                "influencer_impact": 0.0,
                "market_psychology": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }

    def get_signal_model(self) -> type[BaseModel]:
        """
        Get the Pydantic model for the agent's signal output.

        Returns
        -------
        type[BaseModel]
            Pydantic model class for the signal
        """
        return SentimentAnalysis

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
                (
                    "system",
                    f"{self.persona}\n\nYou must analyze the provided data and return a JSON "
                    "response matching the SentimentAnalysis model.",
                ),
                (
                    "human",
                    """
As a Crypto FUTURES Sentiment Analyst, analyze {symbol} for FUTURES trading based on the following data:

{analysis_data}

Focus on:
1. Social media sentiment and community engagement for LONG/SHORT bias
2. News sentiment and media coverage impact on leverage
3. Fear and greed indicators for contrarian futures opportunities
4. Influencer impact and key opinion leaders' directional bias
5. Market psychology and sentiment cycles for timing entries
6. Contrarian opportunities: Extreme fear = LONG opportunity, Extreme greed = SHORT opportunity
7. Funding rate sentiment: Are longs or shorts paying premiums?
8. Liquidation cascade risks from sentiment extremes

Provide your FUTURES analysis in the following JSON format:
{{
    "sentiment": "VERY_POSITIVE|POSITIVE|NEUTRAL|NEGATIVE|VERY_NEGATIVE",
    "recommendation": "LONG|SHORT|HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed sentiment analysis: WHY LONG or SHORT based on market psychology",
    "social_sentiment": 0.0-1.0,
    "news_sentiment": 0.0-1.0,
    "fear_greed_index": 0.0-1.0,
    "community_engagement": 0.0-1.0,
    "influencer_impact": 0.0-1.0,
    "market_psychology": 0.0-1.0,
    "risk_assessment": "LOW|MEDIUM|HIGH",
    "key_insights": ["insight1", "insight2", "insight3"],
    "leverage_sentiment": "BULLISH_LEVERAGE|BEARISH_LEVERAGE|CAUTIOUS",
    "funding_sentiment": "LONG_EXPENSIVE|SHORT_EXPENSIVE|BALANCED",
    "entry_price": float (optimal entry based on sentiment extremes),
    "stop_loss": float (MANDATORY - 3-5% from entry),
    "take_profit_short": float (short-term target, hours to 1-2 days),
    "take_profit_mid": float (mid-term target, 3-7 days),
    "take_profit_long": float (long-term target, 1-4 weeks)
}}

SENTIMENT-DRIVEN ENTRY/EXIT:
- Extreme fear (F&G < 25): Consider LONG with tight stop loss
- Extreme greed (F&G > 75): Consider SHORT with tight stop loss
- Contrarian timing: Enter when sentiment is extremely negative for LONG
- Funding rate analysis: If longs pay high funding, consider SHORT
- News-driven volatility: Set wider stops during major announcements

Remember: LONG = bullish futures (profit from price increase), SHORT = bearish futures (profit from price decrease).
Sentiment extremes often mark trend reversals. Be contrarian when appropriate.
""",
                ),
            ]
        )
