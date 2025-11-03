"""Refactored cryptocurrency analyst agent using OOP design patterns."""

import json
from typing import Any, Literal

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.tools.crypto import (
    aster_get_history,
    aster_get_price,
    crypto_sentiment_analysis,
    price_trend_analysis,
    technical_indicators_analysis,
    trading_strategy_analysis,
    volume_analysis,
)
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class CryptoAnalystSignal(BaseModel):
    """Signal output from crypto analyst agent."""

    signal: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    confidence: float  # 0-100
    reasoning: str
    technical_score: float | None = None
    technical_reasoning: str | None = None
    fundamental_score: float | None = None
    fundamental_reasoning: str | None = None
    sentiment_score: float | None = None
    sentiment_reasoning: str | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    risk_level: str | None = None


class CryptoAnalystAgent(BaseCryptoAgent):
    """Cryptocurrency analyst agent for technical and fundamental analysis."""

    def __init__(self, use_langchain: bool = False):
        super().__init__(agent_id="crypto_analyst_agent", agent_name="Crypto Analyst", use_langchain=use_langchain)
        # Note: Tools are now @tool decorator functions, not class instances

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for crypto analyst agent."""
        return """You are a professional cryptocurrency analyst.

Your expertise includes:
- Technical analysis (indicators, patterns, trends)
- Fundamental analysis (on-chain metrics, network health)
- Sentiment analysis (market mood, news impact)
- Risk assessment and portfolio strategy

Your role is to provide comprehensive crypto analysis by:
1. Gathering current price and historical data
2. Analyzing technical indicators (RSI, MACD, volume, etc.)
3. Checking market sentiment and news
4. Evaluating trading strategies
5. Providing clear actionable signals

📊 PORTFOLIO AWARENESS:
Check for EXISTING position before recommending. Factor in current holdings and unrealized PnL.

Always provide:
- Signal: strong_buy, buy, hold, sell, or strong_sell
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed explanation of your analysis
- Technical, fundamental, and sentiment scores if available

Be thorough but concise. Focus on actionable insights."""

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a single crypto symbol using technical, fundamental, and sentiment analysis.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        Dict[str, Any]
            Analysis results for the symbol
        """
        try:
            # Fetch market data
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Fetching price data...")
            price_data = await self._fetch_price_data(symbol)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Fetching historical data...")
            historical_data = await self._fetch_historical_data(symbol, state)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Analyzing price trends...")
            trend_analysis = await self._analyze_price_trend(symbol, state)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Analyzing volume...")
            volume_analysis = await self._analyze_volume(symbol)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Analyzing sentiment...")
            sentiment_analysis = await self._analyze_sentiment(symbol)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Fetching news data...")
            news_data = await self._fetch_news_data(symbol)

            # Advanced technical analysis
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Calculating technical indicators...")
            technical_indicators = await self._fetch_technical_indicators(symbol, state)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Analyzing trading strategy...")
            strategy_analysis = await self._analyze_trading_strategy(symbol, state)

            # Perform analysis
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Performing technical analysis...")
            technical_analysis = self._analyze_technical_indicators(
                trend_analysis, volume_analysis, historical_data, technical_indicators
            )

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Performing fundamental analysis...")
            fundamental_analysis = self._analyze_fundamentals(price_data, historical_data)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Performing sentiment analysis...")
            sentiment_analysis_result = self._analyze_sentiment_components(sentiment_analysis, news_data)

            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Assessing risk...")
            risk_assessment = self._assess_risk(price_data, historical_data, sentiment_analysis)

            # Compile analysis data
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Compiling analysis data...")
            analysis_data = {
                # "signal": "hold",  # Default
                # "composite_score": 50.0,  # Default
                "technical_analysis": technical_analysis,
                "fundamental_analysis": fundamental_analysis,
                "sentiment_analysis": sentiment_analysis_result,
                "risk_assessment": risk_assessment,
                "price_data": price_data,
                "trend_analysis": trend_analysis,
                "volume_analysis": volume_analysis,
                "advanced_technical_indicators": technical_indicators,
                "strategy_analysis": strategy_analysis,
            }

            # Generate comprehensive analysis using LLM
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, symbol, "Generating LLM analysis...")
            crypto_output = self.generate_llm_analysis(symbol, analysis_data, state)
            return crypto_output.model_dump()

        except Exception as e:
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e!s}",
                "error": str(e),
            }

    def get_signal_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the agent's signal output."""
        return CryptoAnalystSignal

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """Get the LLM prompt template for generating analysis."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AGGRESSIVE quantitative cryptocurrency analyst with deep expertise in:
                - Technical analysis (RSI, MACD, Bollinger Bands, Stochastic, Williams %R, ATR, Moving Averages)
                - Price trend analysis (support/resistance levels, trend identification)
                - Volume analysis (volume patterns, liquidity assessment)
                - Fundamental analysis (market cap, adoption metrics, historical performance)
                - Sentiment analysis (news, market sentiment, social indicators)
                - Risk assessment (volatility, liquidity risk, position sizing)

                Your role is to conduct deep quantitative research and provide ACTIONABLE trading recommendations.

                ⚡ CRITICAL MINDSET: BE DECISIVE & ACTION-ORIENTED ⚡
                - You are a PROFESSIONAL TRADER looking for opportunities, not a passive observer
                - Markets reward action with proper risk management, not hesitation
                - Even moderate signals warrant strong_buy/buy or sell/strong_sell decisions
                - "hold" should be RARE - only when truly conflicted signals exist

                **YOUR ANALYSIS MUST INCLUDE:**

                1. **Executive Summary**: Brief overview of current market condition and key findings

                2. **Current Price Analysis**:
                   - Current price and 24h change percentage with context
                   - Compare to recent high/low and historical averages
                   - Volume analysis (current vs average)

                3. **Technical Indicators Deep Dive**:
                   - RSI: Current value, interpretation (oversold/overbought/neutral), historical context
                   - MACD: Signal strength, histogram trends, divergence analysis
                   - Bollinger Bands: Current position relative to bands, squeeze/expansion patterns
                   - Stochastic: %K and %D values, momentum interpretation
                   - Williams %R: Overbought/oversold levels
                   - ATR: Volatility assessment and risk implications
                   - Moving Averages: SMA/EMA alignment, trend confirmation
                   - Volume Indicators: OBV trends, volume-price divergence

                4. **Price Action Analysis**:
                   - Support levels (major and minor) with confidence levels
                   - Resistance levels (major and minor) with confidence levels
                   - Current price position relative to key levels
                   - Fibonacci retracement levels if available
                   - Recent price patterns (breakouts, reversals, consolidations)

                5. **Trend Analysis**:
                   - Short-term trend (1-7 days): Direction, strength, target range
                   - Mid-term trend (1-4 weeks): Direction, strength, target range
                   - Long-term trend (1-6 months): Direction, strength, target range
                   - Trend confirmation signals from multiple indicators

                6. **Fundamental Factors**:
                   - Market cap classification and implications
                   - Liquidity assessment (24h volume, order book depth)
                   - Historical performance analysis
                   - Volatility characteristics

                7. **Sentiment Analysis**:
                   - News sentiment summary
                   - Market sentiment from technical indicators
                   - Social/crowd sentiment indicators (if available)

                8. **Risk Assessment**:
                   - Volatility risk: Specific percentages and historical context
                   - Liquidity risk: Volume thresholds and execution concerns
                   - Market cap risk: Size and stability assessment
                   - Overall risk level with quantitative justification

                9. **Trading Recommendation** (BE AGGRESSIVE):
                   - Signal: strong_buy | buy | hold | sell | strong_sell
                   - PREFER: strong_buy/strong_sell when 60%+ conviction
                   - USE: buy/sell when 40-59% conviction
                   - AVOID "hold" unless genuinely conflicted (< 40% either direction)
                   - Confidence: 0-100 based on convergence of signals (be generous with 60-80 range)
                   - Target price: Specific price target with time horizon
                   - Stop loss: Risk management price level
                   - Position sizing recommendation (if applicable)

                10. **Detailed Reasoning**:
                    Provide comprehensive explanation connecting:
                    - All technical indicators and their convergence/divergence
                    - Price action and support/resistance dynamics
                    - Volume patterns confirming or contradicting trend
                    - Fundamental factors supporting the thesis
                    - Risk factors and mitigations
                    - Historical context and precedent cases
                    - Specific numbers and percentages throughout

                🎯 DECISION GUIDELINES:
                - strong_buy: RSI < 45, bullish MACD, price near support, 2+ bullish indicators
                - buy: RSI < 55, any bullish momentum, reasonable upside potential
                - hold: ONLY if RSI 48-52, flat MACD, no clear direction (RARE!)
                - sell: RSI > 45, any bearish momentum, reasonable downside risk
                - strong_sell: RSI > 55, bearish MACD, price near resistance, 2+ bearish indicators

                ALWAYS use specific numbers, percentages, price levels, and quantitative metrics.
                Reference the provided data directly in your analysis.
                Consider 24/7 trading, high volatility, regulatory environment, and adoption cycles.
                YOUR JOB IS TO FIND OPPORTUNITIES, NOT TO SIT ON THE SIDELINES!

                Return ONLY the JSON specified below.""",
                ),
                (
                    "human",
                    """Cryptocurrency: {symbol}

                Market Data Available:
                {analysis_data}

                Conduct your comprehensive quantitative analysis and respond EXACTLY in this JSON schema:
                {{
                  "signal": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
                  "confidence": float (0-100),
                  "reasoning": "Comprehensive analysis including executive summary, current price analysis, "
                              "deep dive into all technical indicators with values and interpretation, "
                              "support/resistance levels with prices, short-term (1-7 days), mid-term (1-4 weeks), "
                              "and long-term (1-6 months) trend predictions with specific price ranges, "
                              "fundamental factors, sentiment analysis, risk assessment with percentages, "
                              "and detailed reasoning connecting all factors. Include actual numbers from data.",
                  "technical_score": float | null,
                  "technical_reasoning": "Specific explanation of technical_score (0-100). "
                                        "Include how RSI, MACD, Bollinger Bands, Moving Averages, and other "
                                        "indicators contributed to this score. Cite specific indicator values.",
                  "fundamental_score": float | null,
                  "fundamental_reasoning": "Specific explanation of fundamental_score (0-100). "
                                          "Include market cap analysis, volume assessment, historical performance, "
                                          "and adoption metrics. Cite specific numbers.",
                  "sentiment_score": float | null,
                  "sentiment_reasoning": "Specific explanation of sentiment_score (0-100). "
                                        "Include news sentiment summary, technical sentiment signals, "
                                        "and market sentiment indicators. Cite specific sources.",
                  "target_price": float | null,
                  "stop_loss": float | null,
                  "risk_level": "low" | "medium" | "high" | null
                }}""",
                ),
            ]
        )

    async def _fetch_price_data(self, symbol: str) -> dict[str, Any]:
        """Fetch real-time price data for a symbol."""
        try:
            result = aster_get_price.invoke({"symbol": symbol, "exchange": "aster"})
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_historical_data(self, symbol: str, _state: CryptoAgentState | None = None) -> dict[str, Any]:
        """Fetch historical data for a symbol."""
        try:
            result = aster_get_history.invoke({"symbol": symbol, "timeframe": "1h", "limit": 168, "exchange": "aster"})
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_price_trend(self, symbol: str, _state: CryptoAgentState | None = None) -> dict[str, Any]:
        """Analyze price trends for a symbol."""
        try:
            result = price_trend_analysis.invoke(
                {"symbol": symbol, "timeframe": "1h", "period": 24, "exchange": "aster"}
            )
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_volume(self, symbol: str) -> dict[str, Any]:
        """Analyze volume patterns for a symbol."""
        try:
            result = volume_analysis.invoke({"symbol": symbol, "timeframe": "1h", "period": 24, "exchange": "aster"})
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_sentiment(self, symbol: str) -> dict[str, Any]:
        """Analyze market sentiment for a symbol."""
        try:
            result = crypto_sentiment_analysis.invoke(
                {"symbol": symbol, "timeframe": "1h", "period": 24, "exchange": "aster"}
            )
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_news_data(self, _symbol: str) -> dict[str, Any]:
        """Fetch news data for a symbol."""
        try:
            # TODO: Implement news crawling with @tool decorator pattern
            return {"articles": []}
        except Exception as e:
            return {"error": str(e)}

    def _extract_indicators(self, indicators_data: dict[str, Any]) -> dict[str, Any]:
        """Extract technical indicators for LLM analysis."""
        summary = {}
        extractors = {
            "rsi": lambda d: {"value": d.get("rsi"), "signal": d.get("signal")},
            "macd": lambda d: {"macd": d.get("macd"), "signal": d.get("signal"), "histogram": d.get("histogram")},
            "bollinger_bands": lambda d: {
                "upper": d.get("upper"),
                "middle": d.get("middle"),
                "lower": d.get("lower"),
                "signal": d.get("signal"),
            },
            "stochastic": lambda d: {"k": d.get("k"), "d": d.get("d"), "signal": d.get("signal")},
            "williams_r": lambda d: {"value": d.get("williams_r"), "signal": d.get("signal")},
            "atr": lambda d: {"value": d.get("atr"), "signal": d.get("signal")},
            "moving_averages": lambda d: {
                "sma_20": d.get("sma_20"),
                "sma_50": d.get("sma_50"),
                "ema_12": d.get("ema_12"),
                "ema_26": d.get("ema_26"),
                "trend": d.get("trend"),
            },
            "volume_indicators": lambda d: {"obv": d.get("obv"), "signal": d.get("signal")},
            "fibonacci_levels": lambda d: {"levels": d.get("levels", {})},
        }

        for key, extractor in extractors.items():
            if key in indicators_data:
                summary[key] = extractor(indicators_data[key])

        return summary

    def _analyze_technical_indicators(
        self,
        trend_analysis: dict[str, Any],
        volume_analysis: dict[str, Any],
        historical_data: dict[str, Any],
        technical_indicators: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preprocess technical data for LLM analysis."""
        # Extract key data for LLM analysis
        trend = trend_analysis.get("trend", "neutral")
        volume_trend = volume_analysis.get("volume_trend", "neutral")
        support_levels = trend_analysis.get("support_levels", [])
        resistance_levels = trend_analysis.get("resistance_levels", [])

        # Get current price for context
        current_price = None
        if historical_data.get("prices"):
            current_price = historical_data["prices"][-1].get("close", 0) if historical_data["prices"] else None

        # Extract advanced technical indicators if available
        indicators_summary = {}
        if technical_indicators and isinstance(technical_indicators, dict):
            indicators_data = technical_indicators.get("indicators", {})
            indicators_summary = self._extract_indicators(indicators_data)

        return {
            "trend": trend,
            "volume_trend": volume_trend,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "current_price": current_price,
            "technical_indicators": indicators_summary,
            "raw_trend_data": trend_analysis,
            "raw_volume_data": volume_analysis,
            "raw_historical_data": historical_data,
            "raw_technical_indicators": technical_indicators,
        }

    def _analyze_fundamentals(self, price_data: dict[str, Any], historical_data: dict[str, Any]) -> dict[str, Any]:
        """Preprocess fundamental data for LLM analysis."""
        # Extract key metrics for LLM to analyze
        market_cap = price_data.get("market_cap")
        price_change_24h = price_data.get("change_percent_24h", 0)
        volume_24h = price_data.get("volume", 0)
        data_points = historical_data.get("count", 0) if historical_data else 0

        # Return preprocessed data for LLM to analyze
        return {
            "market_cap": market_cap,
            "price_change_24h": price_change_24h,
            "volume_24h": volume_24h,
            "data_points": data_points,
            "raw_price_data": price_data,
            "raw_historical_data": historical_data,
        }

    def _analyze_sentiment_components(
        self, sentiment_analysis: dict[str, Any], news_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Preprocess sentiment data for LLM analysis."""
        # Extract key sentiment data for LLM to analyze
        sentiment_label = sentiment_analysis.get("sentiment_label", "neutral")
        sentiment_score = sentiment_analysis.get("sentiment_score", 0)
        articles = news_data.get("articles", [])

        # Return preprocessed data for LLM to analyze
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "news_count": len(articles),
            "articles": articles,
            "raw_sentiment_data": sentiment_analysis,
            "raw_news_data": news_data,
        }

    def _assess_risk(
        self,
        price_data: dict[str, Any],
        historical_data: dict[str, Any],
        _sentiment_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Preprocess risk data for LLM analysis."""
        # Calculate volatility for context
        avg_volatility = None
        prices = historical_data.get("prices", [])
        if len(prices) > 1:
            price_changes = []
            for i in range(1, len(prices)):
                prev_price = prices[i - 1].get("close", 0)
                curr_price = prices[i].get("close", 0)
                if prev_price > 0:
                    change = abs(curr_price - prev_price) / prev_price
                    price_changes.append(change)

            if price_changes:
                avg_volatility = sum(price_changes) / len(price_changes)

        volume_24h = price_data.get("volume", 0)
        market_cap = price_data.get("market_cap")

        # Return preprocessed data for LLM to analyze
        return {
            "avg_volatility": avg_volatility,
            "volume_24h": volume_24h,
            "market_cap": market_cap,
            "raw_price_data": price_data,
            "raw_historical_data": historical_data,
        }

    async def _fetch_technical_indicators(self, symbol: str, _state: CryptoAgentState | None = None) -> dict[str, Any]:
        """Fetch advanced technical indicators."""
        try:
            result = technical_indicators_analysis.invoke(
                {"symbol": symbol, "timeframe": "1h", "period": 100, "exchange": "aster"}
            )
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_trading_strategy(self, symbol: str, _state: CryptoAgentState | None = None) -> dict[str, Any]:
        """Analyze trading strategies."""
        try:
            result = trading_strategy_analysis.invoke(
                {
                    "symbol": symbol,
                    "timeframe": "1h",
                    "period": 100,
                    "exchange": "aster",
                    "analysis_type": "comprehensive",
                }
            )
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}
