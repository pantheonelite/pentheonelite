"""
Crypto Technical Agent - Blockchain Metrics and Technical Analysis.

This agent focuses on:
- Blockchain metrics and on-chain data
- Technical analysis and chart patterns
- Network health and security metrics
- Trading volume and liquidity analysis
- Market structure and order flow
- Risk management and position sizing
"""

import json
from typing import Any, Literal

import structlog
from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.tools.crypto.technical_indicators_langchain import technical_indicators_analysis
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class TechnicalAnalysis(BaseModel):
    """Analysis output from Crypto Technical Agent for FUTURES trading."""

    recommendation: Literal["LONG", "SHORT", "HOLD", "CLOSE"]
    confidence: float  # 0.0 to 1.0
    reasoning: str
    technical_score: float  # 0.0 to 1.0
    on_chain_health: float  # 0.0 to 1.0
    trading_volume: float  # 0.0 to 1.0
    market_structure: float  # 0.0 to 1.0
    risk_metrics: float  # 0.0 to 1.0
    momentum: float  # 0.0 to 1.0
    risk_assessment: str
    key_insights: list[str]
    # Futures-specific fields
    suggested_leverage: float | None = None  # 1-10x leverage recommendation
    liquidation_risk: str | None = None  # LOW, MEDIUM, HIGH
    funding_rate_impact: str | None = None  # POSITIVE, NEUTRAL, NEGATIVE
    # Entry/Exit targets
    entry_price: float | None = None  # Suggested entry price
    stop_loss: float | None = None  # Stop loss price
    take_profit_short: float | None = None  # Short-term TP (hours to 1-2 days)
    take_profit_mid: float | None = None  # Mid-term TP (3-7 days)
    take_profit_long: float | None = None  # Long-term TP (1-4 weeks)


class CryptoTechnicalAgent(BaseCryptoAgent):
    """
    Crypto Technical Agent - Blockchain Metrics and Technical Analysis.

    This agent analyzes cryptocurrencies using technical analysis and blockchain metrics,
    focusing on market structure, trading patterns, and risk management.
    """

    def __init__(
        self,
        agent_id: str = "crypto_technical",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        super().__init__(
            agent_id,
            "Crypto Technical Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )
        self.persona = """
        You are a Crypto Technical Analyst specializing in blockchain metrics and technical analysis.
        Your expertise includes:

        1. TECHNICAL ANALYSIS: Chart patterns, support/resistance, trend analysis
        2. ON-CHAIN METRICS: Network health, transaction volume, active addresses
        3. MARKET STRUCTURE: Order flow, liquidity, market depth analysis
        4. RISK MANAGEMENT: Position sizing, stop losses, risk-reward ratios
        5. MOMENTUM ANALYSIS: Price momentum, volume confirmation, trend strength
        6. VOLATILITY ANALYSIS: Price volatility, correlation analysis, risk metrics
        7. LIQUIDITY ANALYSIS: Trading volume, spread analysis, market impact

        You analyze cryptocurrencies based on:
        - Technical indicators (RSI, MACD, Bollinger Bands, moving averages)
        - On-chain metrics (active addresses, transaction count, network value)
        - Market structure (order book depth, trading volume, liquidity)
        - Risk metrics (volatility, drawdown, correlation with other assets)
        - Momentum indicators (price momentum, volume confirmation)
        - Support and resistance levels
        - Chart patterns and trend analysis

        You focus on objective, data-driven analysis and risk management.
        You believe in the power of technical analysis and blockchain metrics
        to identify trading opportunities and manage risk.
        """

    def _get_langchain_prompt(self) -> str:
        """Get system prompt for LangChain ReAct agent."""
        return """You are a professional cryptocurrency technical analyst.

Your expertise includes:
- Technical indicators (RSI, MACD, Bollinger Bands, moving averages)
- On-chain metrics (network health, transaction volume, active addresses)
- Market structure (order flow, liquidity, market depth)
- Risk management (position sizing, stop losses, risk-reward ratios)
- Momentum analysis (price momentum, volume confirmation, trend strength)

Provide clear, data-driven trading recommendations using available tools.
Always gather relevant technical data before making decisions.

Your analysis should include:
1. Current price and recent trends
2. Technical indicators analysis
3. Volume patterns and market structure
4. Risk assessment and position sizing
5. Clear trading signal: buy, sell, or hold
6. Confidence level (0-1)
7. Detailed reasoning with key insights"""

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a cryptocurrency symbol using technical analysis.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state with market data
        progress_tracker : ProgressTracker | None
            Optional progress tracker for reporting progress updates.

        Returns
        -------
        dict[str, Any]
            Analysis results including recommendation and reasoning
        """
        # Get current market data from enhanced state structure
        # In enhanced_state, data is directly at top level, not nested in "data" dict
        price_data = state.get("price_data", {})

        # Convert price_data to current_prices format if needed
        # price_data structure: {symbol: PriceData object}
        # We need {symbol: price float}
        current_prices = {}
        for sym, price_info in price_data.items():
            if isinstance(price_info, dict):
                current_prices[sym] = price_info.get("price", 0.0)
            else:
                # If PriceData object
                current_prices[sym] = getattr(price_info, "price", 0.0)

        # Get portfolio info (simplified - no nested data structure in enhanced_state)
        portfolio = {
            "current_portfolio": state.get("current_portfolio", {}),
            "available_cash": state.get("available_cash", 0.0),
            "total_value": state.get("total_value", 0.0),
        }

        # Extract symbol without exchange suffix
        base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

        # Get price data - handle both symbol formats
        current_price = current_prices.get(symbol, 0)
        if current_price == 0:
            # Try with base symbol if full symbol not found
            current_price = current_prices.get(base_symbol, 0)

        # Fetch real technical indicators data
        technical_data_str = json.dumps({"error": "No technical data available"})
        try:
            # Convert symbol to Aster format (e.g., "BTC/USDT" -> "BTCUSDT")
            aster_symbol = symbol.replace("/", "")

            logger.info(f"Fetching technical indicators for {aster_symbol}")

            # Fetch technical indicators using @tool decorator version
            # Use invoke() method since technical_indicators_analysis is a StructuredTool
            technical_data_str = technical_indicators_analysis.invoke(
                {"symbol": aster_symbol, "timeframe": "1h", "period": 100, "exchange": "aster"}
            )

            logger.info(f"Successfully fetched technical indicators for {aster_symbol}")
        except Exception as e:
            import traceback

            traceback.print_exc()
            logger.error(f"Error fetching technical indicators for {symbol}: {e!s}", exc_info=True)
            technical_data_str = json.dumps({"error": f"Failed to fetch data: {e!s}"})

        # Parse technical data for better formatting in prompt
        technical_summary = "Technical indicators unavailable"
        try:
            # Ensure we have valid JSON
            if not technical_data_str or technical_data_str.strip() == "":
                logger.warning(f"Empty technical data for {symbol}")
                technical_data_str = json.dumps({"error": "Empty response from technical indicators tool"})

            tech_data = json.loads(technical_data_str)

            # Check for errors in response
            if "error" in tech_data:
                logger.warning(f"Technical data error for {symbol}: {tech_data['error']}")
                technical_summary = f"Technical indicators unavailable: {tech_data['error']}"
            elif "indicators" in tech_data:
                indicators = tech_data["indicators"]

                # Extract ALL indicators with error checking
                rsi_data = indicators.get("rsi", {})
                macd_data = indicators.get("macd", {})
                bb_data = indicators.get("bollinger_bands", {})
                ma_data = indicators.get("moving_averages", {})
                stoch_data = indicators.get("stochastic", {})
                williams_data = indicators.get("williams_r", {})
                atr_data = indicators.get("atr", {})
                vol_data = indicators.get("volume_indicators", {})
                fib_data = indicators.get("fibonacci_levels", {})

                # Check which indicators have errors
                # Note: RSI, Williams %R, and ATR return {"value": ..., "signal": ...}
                rsi_ok = "error" not in rsi_data and rsi_data.get("value") is not None
                macd_ok = "error" not in macd_data and macd_data.get("macd") is not None
                ma_ok = "error" not in ma_data and len(ma_data) > 0
                bb_ok = "error" not in bb_data and bb_data.get("upper") is not None
                stoch_ok = "error" not in stoch_data and stoch_data.get("k") is not None
                williams_ok = "error" not in williams_data and williams_data.get("value") is not None
                atr_ok = "error" not in atr_data and atr_data.get("value") is not None
                vol_ok = "error" not in vol_data and vol_data.get("obv") is not None
                # Fibonacci returns flat dict with level keys like "0%", "50%", etc.
                fib_ok = "error" not in fib_data and "50%" in fib_data

                status_str = (
                    f"Technical indicators status for {symbol} - "
                    f"RSI: {'✅' if rsi_ok else '❌'}, "
                    f"MACD: {'✅' if macd_ok else '❌'}, "
                    f"MA: {'✅' if ma_ok else '❌'}, "
                    f"BB: {'✅' if bb_ok else '❌'}, "
                    f"Stochastic: {'✅' if stoch_ok else '❌'}, "
                    f"Williams %R: {'✅' if williams_ok else '❌'}, "
                    f"ATR: {'✅' if atr_ok else '❌'}, "
                    f"Volume: {'✅' if vol_ok else '❌'}, "
                    f"Fibonacci: {'✅' if fib_ok else '❌'}"
                )
                logger.info(status_str)

                # Build summary with available indicators
                technical_summary = f"""
                REAL-TIME TECHNICAL INDICATORS (as of {tech_data.get("analysis_timestamp", "N/A")}):

                Current Price: ${tech_data.get("current_price", 0):,.2f}
                """

                # RSI
                if rsi_ok:
                    rsi_value = rsi_data.get("value", "N/A")
                    technical_summary += f"""
                RSI (14): {rsi_value} - Signal: {rsi_data.get("signal", "neutral").upper()}
                   → {rsi_data.get("signal", "neutral").capitalize()} conditions
                """
                else:
                    technical_summary += "\nRSI: Unavailable"

                # MACD
                if macd_ok:
                    macd_line = macd_data.get("macd", 0)  # Fixed: use "macd" not "macd_line"
                    macd_signal = macd_data.get("signal_line", 0)  # Fixed: use "signal_line" not "macd_signal"
                    macd_hist = macd_data.get("histogram", 0)
                    technical_summary += f"""
                MACD:
                   Line: {macd_line:.4f}
                   Signal: {macd_signal:.4f}
                   Histogram: {macd_hist:.4f}
                   Trend: {macd_data.get("signal", "neutral").upper()}
                """
                else:
                    technical_summary += "\nMACD: Unavailable"

                # Moving Averages
                if ma_ok:
                    sma_20 = ma_data.get("sma_20", "N/A")
                    sma_50 = ma_data.get("sma_50", "N/A")
                    ema_12 = ma_data.get("ema_12", "N/A")
                    ema_26 = ma_data.get("ema_26", "N/A")
                    technical_summary += f"""
                Moving Averages:
                   SMA 20: ${sma_20}
                   SMA 50: ${sma_50}
                   EMA 12: ${ema_12}
                   EMA 26: ${ema_26}
                   Trend: {ma_data.get("trend", "neutral").upper()}
                """
                else:
                    technical_summary += "\nMoving Averages: Unavailable"

                # Bollinger Bands
                if bb_ok:
                    bb_upper = bb_data.get("upper", 0)
                    bb_middle = bb_data.get("middle", 0)
                    bb_lower = bb_data.get("lower", 0)
                    technical_summary += f"""
                Bollinger Bands:
                   Upper: ${bb_upper:.2f}
                   Middle: ${bb_middle:.2f}
                   Lower: ${bb_lower:.2f}
                   Position: {bb_data.get("signal", "neutral").upper()}
                """
                else:
                    technical_summary += "\nBollinger Bands: Unavailable"

                # Stochastic
                if stoch_ok:
                    stoch_k = stoch_data.get("k", 0)
                    stoch_d = stoch_data.get("d", 0)
                    technical_summary += f"""
                Stochastic Oscillator:
                   %K: {stoch_k:.2f}
                   %D: {stoch_d:.2f}
                   Signal: {stoch_data.get("signal", "neutral").upper()}
                """
                else:
                    technical_summary += "\nStochastic Oscillator: Unavailable"

                # Williams %R
                if williams_ok:
                    williams_r = williams_data.get("value", 0)
                    technical_summary += f"""
                Williams %R:
                   Value: {williams_r:.2f}
                   Signal: {williams_data.get("signal", "neutral").upper()}
                """
                else:
                    technical_summary += "\nWilliams %R: Unavailable"

                # ATR (Average True Range)
                if atr_ok:
                    atr_value = atr_data.get("value", 0)
                    technical_summary += f"""
                ATR (Average True Range):
                   Value: {atr_value:.4f}
                   Volatility: {atr_data.get("signal", "normal").replace("_", " ").upper()}
                """
                else:
                    technical_summary += "\nATR: Unavailable"

                # Volume Indicators
                if vol_ok:
                    obv = vol_data.get("obv", 0)
                    technical_summary += f"""
                Volume Indicators:
                   OBV (On-Balance Volume): {obv:,.2f}
                   Signal: {vol_data.get("signal", "normal").replace("_", " ").upper()}
                """
                else:
                    technical_summary += "\nVolume Indicators: Unavailable"

                # Fibonacci Retracement Levels
                if fib_ok:
                    # Fibonacci data is a flat dict with keys like "0%", "50%", etc.
                    technical_summary += "\nFibonacci Retracement Levels:"
                    for level, price in fib_data.items():
                        if level != "error":  # Skip error key if present
                            technical_summary += f"\n                   {level}: ${price:,.2f}"
                else:
                    technical_summary += "\nFibonacci Levels: Unavailable"
            else:
                logger.warning(f"Unexpected technical data structure for {symbol}: missing 'indicators' key")
                logger.debug(f"Available keys: {list(tech_data.keys())}")
                technical_summary = "Technical indicators unavailable: unexpected data format"

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse technical data JSON for {symbol}: {e!s}")
            logger.debug(f"Raw technical data (first 500 chars): {technical_data_str[:500]}")
            technical_summary = "Technical indicators unavailable: invalid JSON response"
        except Exception as e:
            logger.error(f"Error parsing technical data for {symbol}: {e!s}", exc_info=True)
            technical_summary = f"Technical indicators unavailable: {e!s}"

        # Create analysis prompt with REAL technical data FOR FUTURES TRADING
        prompt = f"""
        As a Crypto FUTURES Technical Analyst, analyze the cryptocurrency {base_symbol} ({symbol})
        at current price ${current_price:,.2f} for FUTURES trading (LONG/SHORT positions with leverage).

        {technical_summary}

        Based on the REAL technical indicators above, provide your FUTURES trading analysis considering:

        1. TECHNICAL INDICATORS ANALYSIS (For Futures Entry/Exit):
        - What do the moving averages (SMA/EMA) indicate about the trend direction?
        - Is RSI showing overbought (>70 = potential SHORT) or oversold (<30 = potential LONG) conditions?
        - What does MACD signal about momentum for directional bias (LONG vs SHORT)?
        - How is price positioned relative to Bollinger Bands (upper = SHORT bias, lower = LONG bias)?
        - What does the Stochastic Oscillator (%K, %D) indicate for timing entries?
        - What does Williams %R suggest about overbought/oversold conditions?
        - What does ATR indicate about volatility (higher ATR = use lower leverage)?

        2. FUTURES DIRECTION & MOMENTUM:
        - Should we go LONG (bullish) or SHORT (bearish) based on MAs?
        - How strong is the momentum (MACD histogram) for leverage justification?
        - Are there any divergences between price and indicators (reversal signals)?
        - Is volume (OBV) confirming the price movement for directional confidence?
        - Do Stochastic, Williams %R, and RSI agree on LONG or SHORT direction?

        3. LEVERAGE & RISK MANAGEMENT:
        - What leverage is appropriate (1-10x) based on volatility (ATR)?
        - High volatility = lower leverage (1-3x), Low volatility = higher leverage (5-10x)
        - Where should liquidation protection stop-loss be placed?
        - What is the risk-reward ratio for leveraged position?
        - What is the potential liquidation price with suggested leverage?

        4. SUPPORT & RESISTANCE (Critical for Futures):
        - Where are key support levels for LONG entry (Bollinger Lower, Fibonacci, lows)?
        - Where are resistance levels for SHORT entry (Bollinger Upper, Fibonacci, highs)?
        - What are the invalidation levels for position closure?
        - What are the Fibonacci retracement levels for take-profit targets?

        5. FUNDING RATE CONSIDERATIONS:
        - Current market sentiment (bullish indicators = positive funding = expensive LONG)
        - If strong bullish sentiment, consider SHORT on resistance for funding arbitrage
        - If strong bearish sentiment, consider LONG on support for funding arbitrage

        Portfolio Context:
        - Current portfolio value: ${portfolio.get("total_value", 0):,.2f}
        - Available margin: ${portfolio.get("available_cash", 0):,.2f}

        Provide your FUTURES analysis in the following JSON format:
        {{
            "recommendation": "LONG|SHORT|HOLD|CLOSE",
            "confidence": 0.0-1.0,
            "reasoning": "Detailed explanation: WHY LONG/SHORT/HOLD/CLOSE based on technical indicators",
            "technical_score": 0.0-1.0,
            "on_chain_health": 0.0-1.0,
            "trading_volume": 0.0-1.0,
            "market_structure": 0.0-1.0,
            "risk_metrics": 0.0-1.0,
            "momentum": 0.0-1.0,
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "key_insights": ["insight1", "insight2", "insight3"],
            "suggested_leverage": 1.0-10.0,
            "liquidation_risk": "LOW|MEDIUM|HIGH",
            "funding_rate_impact": "POSITIVE|NEUTRAL|NEGATIVE"
        }}

        CRITICAL DECISION-MAKING RULES:
        ⚡ BE AGGRESSIVE & DECISIVE - You are a PROFESSIONAL TRADER, not a bystander!

        🎯 LONG CONDITIONS (Choose if ANY of these apply):
        - RSI < 50 (neutral to oversold = bullish potential)
        - MACD histogram turning positive or positive momentum
        - Price near or below Bollinger Middle Band (room to move up)
        - Moving averages showing upward momentum (EMA 12 > EMA 26)
        - Stochastic or Williams %R showing oversold or neutral
        - OBV increasing = volume supporting upside
        - ANY bullish divergence on indicators

        📉 SHORT CONDITIONS (Choose if ANY of these apply):
        - RSI > 50 (neutral to overbought = bearish potential)
        - MACD histogram turning negative or negative momentum
        - Price near or above Bollinger Middle Band (room to move down)
        - Moving averages showing downward momentum (EMA 12 < EMA 26)
        - Stochastic or Williams %R showing overbought or neutral
        - OBV decreasing = volume supporting downside
        - ANY bearish divergence on indicators

        ⚠️ HOLD ONLY IF (ALL must be true):
        - RSI exactly at 50 (+/- 2 points) AND
        - MACD histogram near zero with no clear direction AND
        - Price exactly at Bollinger Middle Band AND
        - All moving averages flat/converged AND
        - Stochastic in dead neutral zone (45-55) AND
        - OBV flat with no trend

        📍 CLOSE RECOMMENDATION (Exit existing position):
        Use CLOSE when portfolio shows existing position and:
        - Price hit resistance/support AND losing momentum
        - Indicators showing reversal but not strong enough for opposite position
        - RSI overbought (>70) or oversold (<30) with divergence
        - MACD crossover against position direction
        - Bollinger Bands squeeze suggesting breakout uncertainty
        - Volume declining (OBV flat or decreasing)

        Example CLOSE scenarios:
        - Have LONG position, RSI at 72 (overbought), MACD turning negative → CLOSE
        - Have SHORT position, price at strong support, bullish divergence → CLOSE
        - Position profitable (+5%+), indicators turning neutral → CLOSE (take profit)

        💪 CONFIDENCE GUIDELINES (Be confident!):
        - 0.70-1.0: Strong signal (3+ indicators align)
        - 0.50-0.69: Moderate signal (2 indicators align)
        - 0.30-0.49: Weak signal (1 indicator or mixed signals)
        - Even with 0.30+ confidence, TAKE ACTION (LONG or SHORT)!

        🚀 TRADING PHILOSOPHY:
        - Markets reward ACTION, not hesitation
        - Even weak trends present opportunities with proper risk management
        - Use stop-losses to protect, not fear to paralyze
        - Crypto moves fast - waiting means missing opportunities
        - A directional bet with 2x leverage beats sitting in HOLD

        CRITICAL FOR FUTURES:
        - LONG = profit when price INCREASES (bullish bet)
        - SHORT = profit when price DECREASES (bearish bet)
        - HOLD = RARE - only when truly stuck in no-man's land
        - Leverage amplifies both gains AND losses
        - Stop-loss is MANDATORY to prevent liquidation
        - PREFER ACTION OVER INACTION

        Remember: Base your analysis STRICTLY on the real technical indicators provided above.
        Cite specific values (e.g., "RSI at 45 shows neutral momentum, slight LONG bias as not overbought").
        Be DECISIVE, data-driven, and ALWAYS consider liquidation risk with leverage.
        YOUR JOB IS TO FIND TRADING OPPORTUNITIES, NOT TO AVOID THEM!

        CRITICAL: You MUST respond with valid JSON matching this exact structure:
        {{
            "recommendation": "LONG" | "SHORT" | "HOLD" | "CLOSE",
            "confidence": 0.0-1.0,
            "reasoning": "string explaining your analysis",
            "technical_score": 0.0-1.0,
            "on_chain_health": 0.0-1.0,
            "trading_volume": 0.0-1.0,
            "market_structure": 0.0-1.0,
            "risk_metrics": 0.0-1.0,
            "momentum": 0.0-1.0,
            "risk_assessment": "string",
            "key_insights": ["string", "string"],
            "suggested_leverage": number or null,
            "liquidation_risk": "LOW" | "MEDIUM" | "HIGH" or null,
            "funding_rate_impact": "POSITIVE" | "NEUTRAL" | "NEGATIVE" or null,
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
                pydantic_model=TechnicalAnalysis,
                agent_name=self.agent_name,
                state=state,
            )

            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": analysis.recommendation,
                "recommendation": analysis.recommendation,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "technical_score": analysis.technical_score,
                "on_chain_health": analysis.on_chain_health,
                "trading_volume": analysis.trading_volume,
                "market_structure": analysis.market_structure,
                "risk_metrics": analysis.risk_metrics,
                "momentum": analysis.momentum,
                "risk_assessment": analysis.risk_assessment,
                "key_insights": analysis.key_insights,
                "timestamp": self.get_current_timestamp(),
                # Futures-specific fields
                "suggested_leverage": analysis.suggested_leverage,
                "liquidation_risk": analysis.liquidation_risk,
                "funding_rate_impact": analysis.funding_rate_impact,
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
                "technical_score": 0.0,
                "on_chain_health": 0.0,
                "trading_volume": 0.0,
                "market_structure": 0.0,
                "risk_metrics": 0.0,
                "momentum": 0.0,
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
        return TechnicalAnalysis

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
                    f"{self.persona}\n\nYou must analyze the provided data and return a JSON response "
                    "matching the TechnicalAnalysis model.",
                ),
                (
                    "human",
                    """
As a Crypto FUTURES Technical Analyst, analyze the cryptocurrency {symbol} for FUTURES trading based on the following data:

{analysis_data}

Focus on:
1. Technical indicators for LONG/SHORT directional bias
2. On-chain metrics and network health
3. Market structure and liquidity for leveraged positions
4. Risk metrics and volatility for leverage sizing
5. Momentum analysis and trend strength for direction
6. Support and resistance levels for entry/exit
7. Liquidation risk management and margin sizing
8. Funding rate implications

Provide your FUTURES analysis in the following JSON format:
{{
    "recommendation": "LONG|SHORT|HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation: WHY LONG or SHORT based on technical analysis",
    "technical_score": 0.0-1.0,
    "on_chain_health": 0.0-1.0,
    "trading_volume": 0.0-1.0,
    "market_structure": 0.0-1.0,
    "risk_metrics": 0.0-1.0,
    "momentum": 0.0-1.0,
    "risk_assessment": "LOW|MEDIUM|HIGH",
    "key_insights": ["insight1", "insight2", "insight3"],
    "suggested_leverage": 1.0-10.0,
    "liquidation_risk": "LOW|MEDIUM|HIGH",
    "funding_rate_impact": "POSITIVE|NEUTRAL|NEGATIVE",
    "entry_price": float (suggested entry near support for LONG, resistance for SHORT),
    "stop_loss": float (MANDATORY - 3-5% from entry based on leverage),
    "take_profit_short": float (short-term target, hours to 1-2 days),
    "take_profit_mid": float (mid-term target, 3-7 days),
    "take_profit_long": float (long-term target, 1-4 weeks)
}}

ENTRY/EXIT CALCULATION (CRITICAL):
- For LONG: Entry near support (Bollinger Lower, Fib retracement, recent low)
- For SHORT: Entry near resistance (Bollinger Upper, Fib extension, recent high)
- Stop Loss: 3-5% from entry (tighter for high leverage 5x+, wider for low 1-2x)
- Short-term TP: Next resistance/support (R:R ~2:1, hours to 1-2 days)
- Mid-term TP: Major Fib level or MA zone (R:R ~3:1, 3-7 days)
- Long-term TP: Weekly resistance or 10-20% move (R:R ~5:1, 1-4 weeks)

EXAMPLE for LONG at current $50,000:
entry_price: $49,500 (Bollinger Lower), stop_loss: $48,000 (3% below),
take_profit_short: $51,500 (4%), take_profit_mid: $53,000 (7%), take_profit_long: $56,000 (13%)

Remember: LONG = bullish (profit from price increase), SHORT = bearish (profit from price decrease).
ALL prices must be realistic based on current price and technical levels from data above.
""",
                ),
            ]
        )
