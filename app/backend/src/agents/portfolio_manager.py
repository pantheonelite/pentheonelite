"""Refactored cryptocurrency portfolio management agent using OOP design patterns."""

import json
from typing import Any, Literal, cast

import structlog
from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.tools.crypto import (
    aster_get_history,
    aster_get_price,
    technical_indicators_analysis,
    trading_strategy_analysis,
)
from app.backend.src.tools.web import crypto_news_search, crypto_web_sentiment
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, field_validator

logger = structlog.get_logger(__name__)


class CryptoPortfolioDecision(BaseModel):
    """Portfolio decision for a specific crypto futures symbol."""

    symbol: str
    action: Literal["buy", "sell", "hold"]
    quantity: float
    reasoning: str
    confidence: float  # 0-100
    target_price: float | None = None
    stop_loss: float | None = None
    position_size: float | None = None
    risk_level: str | None = None
    leverage: float | None = None  # Suggested leverage (1-10x)
    direction: Literal["LONG", "SHORT", "NONE"] | None = None  # Position direction for clarity
    # Multi-timeframe targets
    entry_price: float | None = None  # Optimal entry price
    take_profit_short: float | None = None  # Short-term TP (hours to 1-2 days)
    take_profit_mid: float | None = None  # Mid-term TP (3-7 days)
    take_profit_long: float | None = None  # Long-term TP (1-4 weeks)

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, v):
        """Normalize action to lowercase."""
        if isinstance(v, str):
            return v.lower().strip()
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v):
        """Normalize direction to uppercase."""
        if isinstance(v, str):
            return v.upper().strip()
        return v

    @field_validator(
        "quantity",
        "confidence",
        "target_price",
        "stop_loss",
        "position_size",
        "leverage",
        "entry_price",
        "take_profit_short",
        "take_profit_mid",
        "take_profit_long",
        mode="before",
    )
    @classmethod
    def coerce_to_float(cls, v):
        """Coerce numeric fields to float, handle various input types."""
        if v is None or v == "None":
            return None
        if isinstance(v, str):
            if v in ["Error in analysis", "Unknown", "", "Error in analysis, using default"]:
                return None
            try:
                return float(v)
            except ValueError:
                return None
        if isinstance(v, (int, float)):
            return float(v)
        # Handle type objects (from buggy defaults)
        if v in (float, int):
            return None
        return None

    @field_validator("risk_level", mode="before")
    @classmethod
    def normalize_risk_level(cls, v):
        """Normalize risk level to string, handle numeric values."""
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() if v not in ["Error in analysis", "Unknown"] else None
        if isinstance(v, (int, float)):
            # Convert numeric to risk level
            if v <= 0.3:
                return "low"
            if v <= 0.7:
                return "medium"
            return "high"
        # Handle type objects
        if v in (str, float):
            return None
        return None


class CryptoPortfolioManagerOutput(BaseModel):
    """Output from crypto portfolio manager agent."""

    decisions: dict[str, CryptoPortfolioDecision]
    portfolio_summary: dict[str, Any]
    risk_assessment: dict[str, Any]
    strategy_recommendations: list[str]
    warnings: list[str] = []
    alerts: list[str] = []


class CryptoPortfolioManagerAgent(BaseCryptoAgent):
    """Cryptocurrency portfolio management agent."""

    def __init__(self, model_name: str | None = None, model_provider: str | None = None):
        super().__init__(
            agent_id="crypto_portfolio_manager",
            agent_name="Crypto Portfolio Manager",
            model_name=model_name,
            model_provider=model_provider,
        )
        # Note: Tools are now @tool decorator functions, not class instances
        logger.info("Portfolio manager initialized with model=%s, provider=%s", model_name, model_provider)

    async def analyze_symbol(self, symbol: str, state: CryptoAgentState, progress_tracker=None) -> dict[str, Any]:  # noqa: ARG002
        """
        Analyze a single crypto symbol for portfolio management using LLM.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTC/USDT")
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance (unused but required by base class)

        Returns
        -------
        Dict[str, Any]
            Analysis results for the symbol
        """
        # For portfolio management, we analyze per-symbol for parallel execution
        # but use portfolio-wide context
        try:
            # Get portfolio context
            portfolio = state.get("portfolio", {})
            analyst_signals = state.get("technical_signals", {})
            risk_signals = state.get("risk_assessments", {})

            # Generate trading decision using LLM
            decision = await self._generate_symbol_decision_llm(
                symbol, portfolio, analyst_signals, risk_signals, state
            )

        except Exception as e:
            logger.exception("Error analyzing symbol %s in portfolio manager", symbol)
            return {
                "symbol": symbol,
                "action": "hold",
                "quantity": 0.0,
                "reasoning": f"Error in portfolio analysis: {e!s}",
                "confidence": 0.0,
                "risk_level": "high",
                "error": str(e),
            }
        else:
            return decision

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze symbol using manual workflow (delegates to analyze_symbol).

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze
        state : CryptoAgentState
            The current agent state
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Analysis result containing signal, confidence, reasoning
        """
        # Portfolio manager doesn't have a separate manual mode
        # Just delegate to the main analyze_symbol method
        return await self.analyze_symbol(symbol, state, progress_tracker)

    async def _fetch_market_data(self, symbol: str) -> dict[str, Any]:
        """Fetch comprehensive market data for portfolio analysis."""
        try:
            logger.info("Fetching market data for %s", symbol)

            # Get current price
            logger.debug("Getting current price for %s", symbol)
            price_data = json.loads(aster_get_price.invoke({"symbol": symbol, "exchange": "aster"}))
            logger.info("Price data for %s: %s", symbol, json.dumps(price_data, indent=2))

            # Get historical data for trend analysis
            logger.debug("Getting historical data for %s", symbol)
            history_data = json.loads(
                aster_get_history.invoke({"symbol": symbol, "timeframe": "1h", "limit": 168, "exchange": "aster"})
            )
            logger.info("Historical data for %s: %s", symbol, json.dumps(history_data, indent=2))

            # Get technical indicators
            logger.debug("Getting technical indicators for %s", symbol)
            technical_data = json.loads(
                technical_indicators_analysis.invoke(
                    {"symbol": symbol, "timeframe": "1h", "period": 100, "exchange": "aster"}
                )
            )
            logger.info("Technical indicators for %s: %s", symbol, json.dumps(technical_data, indent=2))

            # Get trading strategy analysis
            logger.debug("Getting trading strategy for %s", symbol)
            strategy_data = json.loads(
                trading_strategy_analysis.invoke(
                    {
                        "symbol": symbol,
                        "timeframe": "1h",
                        "period": 100,
                        "exchange": "aster",
                        "analysis_type": "comprehensive",
                    }
                )
            )
            logger.info("Trading strategy for %s: %s", symbol, json.dumps(strategy_data, indent=2))

            logger.info("Successfully fetched market data for %s", symbol)
            return {
                "price": price_data,
                "history": history_data,
                "technical": technical_data,
                "strategy": strategy_data,
            }
        except Exception:
            logger.exception("Error fetching market data for %s", symbol)
            return {}

    async def _analyze_market_sentiment(self, symbol: str) -> dict[str, Any]:
        """Analyze market sentiment using web sources."""
        try:
            logger.info("Analyzing market sentiment for %s", symbol)

            # Get news sentiment
            logger.debug("Getting news sentiment for %s", symbol)
            news_sentiment = crypto_news_search(symbol, 5)
            logger.info("News sentiment for %s: %s", symbol, news_sentiment)

            # Get web sentiment analysis
            logger.debug("Getting web sentiment for %s", symbol)
            web_sentiment = crypto_web_sentiment(symbol, 5)
            logger.info("Web sentiment for %s: %s", symbol, web_sentiment)

            logger.info("Successfully analyzed sentiment for %s", symbol)
            return {"news": news_sentiment, "web_sentiment": web_sentiment}
        except Exception:
            logger.exception("Error analyzing sentiment for %s", symbol)
            return {}

    def analyze_portfolio(self, state: CryptoAgentState, progress_tracker=None) -> dict[str, Any]:
        """
        Analyze the entire crypto portfolio and make trading decisions.

        Parameters
        ----------
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        Dict[str, Any]
            Portfolio analysis and trading decisions
        """
        try:
            # Enhanced state structure - data is directly in state
            symbols = state.get("symbols", [])
            portfolio = state.get("portfolio", {})  # {"cash", "positions", "realized_gains"}

            # Update progress for portfolio analysis
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Analyzing portfolio composition...")
            analyst_signals = state.get("technical_signals", {})
            risk_signals = state.get("risk_assessments", {})

            # Analyze market conditions
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Analyzing market conditions...")
            market_analysis = self._analyze_market_conditions(symbols)

            # Analyze agent signals
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Analyzing agent signals...")
            signal_analysis = self._analyze_agent_signals(analyst_signals, risk_signals, symbols)

            # Generate trading decisions using LLM (per symbol)
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Generating trading decisions with LLM...")

            # Note: This is a synchronous wrapper - the actual decisions are made via analyze_symbol
            # which is called asynchronously in the graph execution
            # For now, we'll pass empty decisions here and let the LLM analysis handle it
            trading_decisions = {}

            # Compile portfolio data
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Compiling portfolio data...")
            portfolio_data = {
                "portfolio_analysis": portfolio,
                "market_analysis": market_analysis,
                "signal_analysis": signal_analysis,
                "trading_decisions": trading_decisions,
            }

            # Generate comprehensive portfolio management output using LLM
            if progress_tracker:
                progress_tracker.update_status(self.agent_id, None, "Generating portfolio analysis...")

            logger.debug("Portfolio data: %s", json.dumps(portfolio_data, indent=2))

            portfolio_output = self._generate_portfolio_llm_analysis(portfolio_data, state)

            # Convert to JSON-serializable dict
            output_dict = portfolio_output.model_dump()

            # Convert nested Pydantic objects to dicts
            if "decisions" in output_dict:
                decisions_dict = {}
                for symbol, decision in output_dict["decisions"].items():
                    if hasattr(decision, "model_dump"):
                        decisions_dict[symbol] = decision.model_dump()
                    elif hasattr(decision, "dict"):
                        decisions_dict[symbol] = decision.dict()
                    else:
                        decisions_dict[symbol] = decision
                output_dict["decisions"] = decisions_dict

            return output_dict

        except Exception as e:
            return {
                "decisions": {},
                "portfolio_summary": {"error": str(e)},
                "risk_assessment": {"error": str(e)},
                "strategy_recommendations": [],
                "warnings": [f"Portfolio analysis failed: {e!s}"],
                "error": str(e),
            }

    def get_signal_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the agent's signal output."""
        return CryptoPortfolioManagerOutput

    def _generate_portfolio_llm_analysis(  # noqa: PLR0912, PLR0915
        self, portfolio_data: dict[str, Any], state: CryptoAgentState
    ) -> BaseModel:
        """
        Generate portfolio analysis using LLM with proper portfolio variables.

        Parameters
        ----------
        portfolio_data : dict[str, Any]
            Raw portfolio analysis data
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        BaseModel
            Generated portfolio analysis result
        """
        # Extract portfolio information
        portfolio = state.get("portfolio", {})
        cash = portfolio.get("cash", 0)
        positions = portfolio.get("positions", {})

        # Calculate portfolio metrics
        total_position_value = 0
        for position in positions.values():
            if "long" in position or "short" in position:
                # Long/Short structure
                long_amount = position.get("long", 0)
                short_amount = position.get("short", 0)
                current_price = position.get("current_price", 0)
                net_amount = long_amount - short_amount
                total_position_value += abs(net_amount) * current_price
            else:
                # Simple structure
                amount = position.get("amount", 0)
                current_price = position.get("current_price", 0)
                total_position_value += amount * current_price

        total_value = cash + total_position_value
        cash_ratio = (cash / total_value * 100) if total_value > 0 else 100

        # Prepare portfolio variables for the prompt
        portfolio_vars = {
            "analysis_data": json.dumps(portfolio_data, indent=2),
            "portfolio_cash": cash,
            "portfolio_position_value": total_position_value,
            "portfolio_total_value": total_value,
            "cash_ratio": cash_ratio,
            "portfolio_positions": json.dumps(positions, indent=2),
        }

        template = self.get_llm_prompt_template()
        prompt = template.invoke(portfolio_vars)

        try:
            result = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=self.get_signal_model(),
                agent_name=self.agent_id,
                state=state,
            )

            # 🔥 AGGRESSIVE MODE ENFORCEMENT 🔥
            # Force trades when cash ratio >70% and confidence >45%
            # This GUARANTEES aggressive behavior regardless of LLM output
            if cash_ratio > 70:
                logger.info(
                    "Aggressive mode active: portfolio %.1f%% cash - enforcing mandatory trading",
                    cash_ratio,
                )

                for symbol, decision in result.decisions.items():
                    confidence = decision.confidence
                    action = decision.action

                    # If LLM chose HOLD but we have sufficient confidence, FORCE a trade
                    if action == "hold" and confidence >= 45:
                        # Determine direction from signals
                        signals = portfolio_data.get("signal_analysis", {}).get(symbol, {})
                        analyst_signals = signals.get("analyst_signals", [])
                        risk_signals = signals.get("risk_signals", [])

                        # Count bullish vs bearish signals
                        bullish_count = sum(
                            1
                            for sig in analyst_signals + risk_signals
                            if sig.get("signal", "").lower() in ["buy", "strong_buy"]
                        )
                        bearish_count = sum(
                            1
                            for sig in analyst_signals + risk_signals
                            if sig.get("signal", "").lower() in ["sell", "strong_sell"]
                        )

                        # Force direction (default to LONG if equal)
                        if bearish_count > bullish_count:
                            forced_action = "sell"
                            forced_direction = "SHORT"
                            logger.warning(
                                "FORCING SHORT for %s (confidence: %.1f%%, bearish signals: %d)",
                                symbol,
                                confidence,
                                bearish_count,
                            )
                        else:
                            forced_action = "buy"
                            forced_direction = "LONG"
                            logger.warning(
                                "FORCING LONG for %s (confidence: %.1f%%, bullish signals: %d)",
                                symbol,
                                confidence,
                                bullish_count,
                            )

                        # Update decision
                        decision.action = forced_action
                        decision.direction = forced_direction

                        # Calculate aggressive leverage based on confidence
                        if confidence >= 65:
                            leverage = 7.0  # High confidence = 7x
                        elif confidence >= 55:
                            leverage = 5.0  # Medium-high confidence = 5x
                        else:
                            leverage = 3.0  # Minimum aggressive leverage = 3x

                        decision.leverage = leverage
                        decision.reasoning += (
                            f" [AGGRESSIVE MODE ENFORCED: Portfolio {cash_ratio:.1f}% cash "
                            f"requires mandatory trading. Forced {forced_direction} with "
                            f"{leverage}x leverage based on {confidence:.1f}% confidence.]"
                        )

                        # Update position size for leverage
                        if decision.position_size:
                            decision.position_size = decision.position_size * (leverage / 2)

                        logger.info(
                            "Enforced %s %s for %s: leverage=%.1fx, confidence=%.1f%%",
                            forced_action.upper(),
                            forced_direction,
                            symbol,
                            leverage,
                            confidence,
                        )

        except Exception:
            logger.exception("Error in portfolio LLM analysis")
            raise
        return result

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """Get the LLM prompt template for generating portfolio decisions."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AGGRESSIVE cryptocurrency FUTURES portfolio manager with expertise in:
                - Futures trading strategies (LONG and SHORT positions)
                - Leverage and margin management (1x-10x leverage)
                - Technical analysis for entry/exit timing
                - Risk-adjusted position sizing for leveraged trading
                - Stop-loss and take-profit placement

                🎯 YOUR PRIMARY GOAL: MAXIMIZE RETURNS through active LONG and SHORT positions

                📊 PORTFOLIO CONTEXT YOU RECEIVE:

                You will receive current portfolio state with these key fields:

                **Position Fields Explained**:
                - `side`: "LONG" (profit when price ↑) or "SHORT" (profit when price ↓)
                - `position_amt`: Quantity of crypto held (e.g., 0.5 BTC)
                - `entry_price`: Price you bought/shorted at
                - `current_price`: Current market price
                - `unrealized_pnl`: Profit/loss if closed now (positive = profit, negative = loss)
                - `leverage`: Position multiplier (10x means 10x exposure and risk)
                - `notional`: Total position value in USDT (your real exposure)
                - `liquidation_price`: Price at which exchange auto-closes your position

                **Position Management Decisions**:

                When you see an EXISTING position for a symbol, you must decide:

                1. **ADD_TO_POSITION** (action: "buy" if LONG, "sell" if SHORT):
                   - Increases position size in same direction
                   - Use when: Trend continues, high confidence, position not max size yet
                   - Example: Have LONG 0.5 BTC, add 0.2 BTC more → total 0.7 BTC LONG

                2. **CLOSE_POSITION** (action: opposite of current side):
                   - Closes entire position to realize profit/loss
                   - Use when: Target reached, trend reversal, risk too high
                   - Example: Have LONG 0.5 BTC → SELL 0.5 BTC to close

                3. **REVERSE_POSITION** (action: opposite, quantity > current position):
                   - Closes current position AND opens opposite direction
                   - Use when: Strong reversal signal, flip from bullish to bearish
                   - Example: Have LONG 0.5 BTC → SELL 1.0 BTC = close LONG, open SHORT 0.5 BTC

                4. **HOLD_POSITION** (action: "hold"):
                   - Keep existing position unchanged
                   - Use when: Position is good, no strong new signals, waiting for target
                   - Example: Have LONG 0.5 BTC with profit → keep holding

                5. **REDUCE_POSITION** (action: partial close):
                   - Take partial profits or reduce risk
                   - Use when: Target partially hit, reduce exposure
                   - Example: Have LONG 1.0 BTC → SELL 0.5 BTC = keep LONG 0.5 BTC

                **Decision Framework for Existing Positions**:
                - Check `unrealized_pnl`: If profitable and at target → CLOSE or REDUCE
                - Check trend alignment: If trend changed → REVERSE or CLOSE
                - Check risk: If `liquidation_price` too close → REDUCE or CLOSE
                - Check signals: If signals stronger → ADD_TO
                - Default: If neutral signals and position profitable → HOLD

                ⚠️ CRITICAL FUTURES TRADING RULES:
                1. **BUY = OPEN LONG** (profit when price INCREASES)
                   - Use when: Bullish technical signals, positive sentiment, uptrend momentum
                   - Target: Enter at support, exit at resistance

                2. **SELL = OPEN SHORT** (profit when price DECREASES)
                   - Use when: Bearish technical signals, negative sentiment, downtrend momentum
                   - Target: Enter at resistance, exit at support

                3. **HOLD = WAIT** only when:
                   - Extremely mixed/conflicting signals with no clear direction
                   - Already at maximum position size for the symbol
                   - Waiting for better entry point (near support/resistance)

                4. **POSITION BIAS when portfolio is >70% cash:**
                   - STRONGLY PREFER opening positions (LONG or SHORT) over HOLD
                   - Empty portfolio = missed opportunity cost
                   - Even weak signals (50%+ confidence) should trigger positions
                   - BIAS TOWARD ACTION: Default to trading unless clearly wrong

                📊 SIGNAL INTERPRETATION FOR FUTURES (AGGRESSIVE):
                - Technical "BUY/STRONG_BUY" + Risk "BUY/HOLD" → **BUY (LONG)** with 5-10x leverage
                - Technical "SELL/STRONG_SELL" + Risk "SELL/HOLD" → **SELL (SHORT)** with 5-10x leverage
                - Technical "BUY" + Risk "SELL" → **BUY (LONG)** if tech confidence >55%
                - Technical "SELL" + Risk "BUY" → **SELL (SHORT)** if tech confidence >55%
                - Technical "HOLD" + Risk "HOLD" + Portfolio empty → **ALWAYS BUY or SELL**
                  (pick ANY direction with slight edge)
                - Single strong signal → **FOLLOW IT** even if others neutral

                💡 AGGRESSIVE LEVERAGE STRATEGY:
                - Low volatility (< 2% daily) → MAX leverage (8-10x) - MAXIMIZE GAINS
                - Medium volatility (2-5% daily) → HIGH leverage (5-8x) - STRONG POSITIONS
                - High volatility (> 5% daily) → MODERATE leverage (3-5x) - STILL AGGRESSIVE

                🛡️ AGGRESSIVE RISK MANAGEMENT:
                - ALWAYS set stop-loss (5-7% from entry for leveraged positions - WIDER stops)
                - Position size: 15-40% of available margin per trade (LARGER positions)
                - Risk up to 3-5% of portfolio per position (MORE aggressive)
                - Diversify but PRIORITIZE high-conviction trades

                ❌ AVOID:
                - HOLD when portfolio has >70% cash (UNACCEPTABLE - missed opportunities)
                - Hesitating with 50%+ confidence signals (TAKE THE TRADE)
                - Ignoring momentum - ride trends aggressively
                - Under-leveraging winning strategies

                Return ONLY the JSON specified below. Be AGGRESSIVE but CALCULATED.""",
                ),
                (
                    "human",
                    """📊 FUTURES Portfolio Analysis:
                {analysis_data}

                💰 Current Portfolio State:
                - Available Margin: {portfolio_cash} USDT
                - Position Value: {portfolio_position_value} USDT
                - Total Value: {portfolio_total_value} USDT
                - Cash Ratio: {cash_ratio}%
                - Active Positions: {portfolio_positions}

                🎯 DECISION FRAMEWORK:

                **AGGRESSIVE MODE ACTIVATED - Portfolio >70% cash:**
                →  **MANDATORY**: MUST open positions (BUY or SELL, NEVER HOLD)
                → Trade with >45% confidence (lower threshold than normal)
                → **CRITICAL**: Empty portfolio = UNACCEPTABLE - ALWAYS find a direction
                → Mixed signals? Pick the STRONGEST one (even if barely stronger)
                → All neutral? DEFAULT to LONG on momentum (BTC bias) or SHORT on weakness
                → **NO EXCUSES**: Find ANY reason to trade - this is FUTURES, profit both ways!

                **For Each Symbol, Evaluate:**
                1. Technical Signal Direction (BUY/SELL/HOLD)
                2. Risk Assessment (BUY/SELL/HOLD)
                3. Sentiment/Momentum
                4. Current Price vs Support/Resistance

                **Then Decide (AGGRESSIVE BIAS):**
                - Both Bullish → **BUY (LONG)** with 5-10x leverage
                - Both Bearish → **SELL (SHORT)** with 5-10x leverage
                - One Bullish, One Neutral → **BUY (LONG)** with 3-5x leverage
                - One Bearish, One Neutral → **SELL (SHORT)** with 3-5x leverage
                - One Bullish, One Bearish → **FOLLOW TECHNICAL SIGNAL** (higher weight)
                - Both HOLD + Empty Portfolio → **MUST TRADE** - pick direction with ANY edge
                - Both HOLD + Already positioned → Consider adding to position or **HOLD**

                **AGGRESSIVE Position Sizing:**
                - High confidence (>75%): 25-40% of available margin (MAX CONVICTION)
                - Medium confidence (55-75%): 15-25% of available margin (STRONG)
                - Low confidence (50-55%): 10-15% of available margin (STILL TRADE)

                **Stop Loss (REQUIRED):**
                - LONG: 3-5% below entry (or below recent support)
                - SHORT: 3-5% above entry (or above recent resistance)

                ⚠️ REMEMBER: This is FUTURES - you CAN and SHOULD open SHORT positions when bearish!

                Respond EXACTLY in this JSON schema:
                {{
                  "decisions": {{
                    "SYMBOL": {{
                      "symbol": "string",
                      "action": "buy" | "sell" | "hold",
                      "quantity": float,
                      "reasoning": "string (MUST include: signal analysis, direction bias, why LONG/SHORT/HOLD)",
                      "confidence": float (0-100),
                      "target_price": float (take-profit level - deprecated, use take_profit_* instead),
                      "stop_loss": float (REQUIRED - risk management),
                      "position_size": float (margin to use in USDT),
                      "risk_level": "low" | "medium" | "high",
                      "leverage": float (suggested 1-10x),
                      "direction": "LONG" | "SHORT" | "NONE" (clarify position type),
                      "entry_price": float (optimal entry price based on analyst signals),
                      "take_profit_short": float (short-term TP, hours to 1-2 days),
                      "take_profit_mid": float (mid-term TP, 3-7 days),
                      "take_profit_long": float (long-term TP, 1-4 weeks)
                    }}
                  }},
                  "portfolio_summary": {{
                    "total_value": float,
                    "cash_balance": float (available margin),
                    "position_value": float (total notional value),
                    "unrealized_pnl": float,
                    "diversification_score": float (0-1),
                    "margin_usage_ratio": float (used/total margin)
                  }},
                  "risk_assessment": {{
                    "overall_risk": "low" | "medium" | "high",
                    "concentration_risk": float (0-1),
                    "correlation_risk": float (0-1),
                    "liquidity_risk": float (0-1),
                    "leverage_risk": "low" | "medium" | "high",
                    "liquidation_risk": "low" | "medium" | "high"
                  }},
                  "strategy_recommendations": [
                    "string - specific actionable futures strategies",
                    "Consider market conditions and funding rates",
                    "Hedging recommendations if needed"
                  ],
                  "warnings": [
                    "string - IMPORTANT: leverage warnings",
                    "Liquidation price warnings",
                    "Market volatility alerts"
                  ],
                  "alerts": [
                    "string - URGENT: immediate action needed",
                    "Stop-loss hit alerts",
                    "Margin call warnings"
                  ]
                }}

                ENTRY/EXIT TARGET SYNTHESIS (CRITICAL):
                - Aggregate entry_price, stop_loss, and TP targets from analyst signals
                - Use weighted average based on analyst confidence scores
                - Technical agent's levels > Sentiment agent's levels (technical has priority)
                - Ensure stop_loss is ALWAYS 3-5% from entry_price
                - Short-term TP should be 2-4% profit (hours to 1-2 days)
                - Mid-term TP should be 5-10% profit (3-7 days)
                - Long-term TP should be 10-20% profit (1-4 weeks)

                EXAMPLE TARGET AGGREGATION:
                If Technical suggests: entry $50,000, TP_short $51,500, TP_mid $53,000
                And Sentiment suggests: entry $49,500, TP_short $51,000, TP_mid $52,500
                Then use: entry $49,750 (average), TP_short $51,250, TP_mid $52,750

                💪 BE DECISIVE: Don't over-use HOLD when portfolio is empty. Take calculated risks!""",
                ),
            ]
        )

    def _analyze_portfolio_composition(self, portfolio: dict[str, Any], symbols: list[str]) -> dict[str, Any]:
        """Analyze the current portfolio composition."""
        cash = portfolio.get("cash", 0)
        positions = portfolio.get("positions", {})

        # Calculate portfolio metrics
        total_position_value = 0
        position_count = 0
        concentration_risk = 0

        for symbol in symbols:
            position = positions.get(symbol, {})

            # Handle both simple and long/short position structures
            if "long" in position or "short" in position:
                # Long/Short structure from PortfolioService
                long_amount = position.get("long", 0)
                short_amount = position.get("short", 0)
                current_price = position.get("current_price", 0)

                # If current_price is 0, try to fetch it from market
                if current_price == 0 and (long_amount != 0 or short_amount != 0):
                    try:
                        price_data = json.loads(aster_get_price.invoke({"symbol": symbol, "exchange": "aster"}))
                        current_price = price_data.get("price", 0)
                        logger.info("Fetched current price for %s: %s", symbol, current_price)
                    except Exception as e:
                        logger.warning("Failed to fetch current price for %s: %s", symbol, e)
                        current_price = 0

                # Calculate net position value (long - short)
                net_amount = long_amount - short_amount
                position_value = abs(net_amount) * current_price
            else:
                # Simple structure from CLI
                amount = position.get("amount", 0)
                current_price = position.get("current_price", 0)

                # If current_price is 0, try to fetch it from market
                if current_price == 0 and amount != 0:
                    try:
                        price_data = json.loads(aster_get_price.invoke({"symbol": symbol, "exchange": "aster"}))
                        current_price = price_data.get("price", 0)
                        logger.info("Fetched current price for %s: %s", symbol, current_price)
                    except Exception as e:
                        logger.warning("Failed to fetch current price for %s: %s", symbol, e)
                        current_price = 0

                position_value = amount * current_price

            if position_value > 0:
                total_position_value += position_value
                position_count += 1

                # Calculate concentration risk
                if total_position_value > 0:
                    concentration = position_value / total_position_value
                    if concentration > 0.3:  # > 30% concentration
                        concentration_risk += concentration - 0.3

        total_value = cash + total_position_value

        # Diversification score
        diversification_score = min(100, position_count * 20)  # Max 100 for 5+ positions

        return {
            "cash_balance": cash,
            "total_position_value": total_position_value,
            "total_value": total_value,
            "position_count": position_count,
            "concentration_risk": concentration_risk,
            "diversification_score": diversification_score,
            "cash_percentage": (cash / total_value * 100) if total_value > 0 else 100,
        }

    def _analyze_market_conditions(self, symbols: list[str]) -> dict[str, Any]:
        """Analyze current market conditions."""
        market_sentiment = "neutral"
        volatility_level = "medium"
        trend_direction = "sideways"

        # Simplified market analysis
        # In a real implementation, this would analyze market data
        bullish_signals = 0
        bearish_signals = 0

        for symbol in symbols:
            # This would typically analyze price data, volume, etc.
            # For now, we'll use a simplified approach
            if "BTC" in symbol.upper() or "ETH" in symbol.upper():
                bullish_signals += 1
            else:
                bearish_signals += 1

        if bullish_signals > bearish_signals:
            market_sentiment = "bullish"
            trend_direction = "upward"
        elif bearish_signals > bullish_signals:
            market_sentiment = "bearish"
            trend_direction = "downward"

        return {
            "market_sentiment": market_sentiment,
            "volatility_level": volatility_level,
            "trend_direction": trend_direction,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
        }

    def _analyze_agent_signals(
        self,
        analyst_signals: dict[str, Any],
        risk_signals: dict[str, Any],
        symbols: list[str],
    ) -> dict[str, Any]:
        """Analyze signals from other agents."""
        signal_summary = {}

        for symbol in symbols:
            symbol_signals = {
                "analyst_signals": [],
                "risk_signals": [],
                "consensus": "hold",
                "confidence": 0.0,
            }

            # Collect analyst signals
            for agent, signals in analyst_signals.items():
                if symbol in signals:
                    signal_data = signals[symbol]
                    symbol_signals["analyst_signals"].append(
                        {
                            "agent": agent,
                            "signal": signal_data.get("signal", "hold"),
                            "confidence": signal_data.get("confidence", 0.0),
                        }
                    )

            # Collect risk signals
            for agent, signals in risk_signals.items():
                if symbol in signals:
                    signal_data = signals[symbol]
                    symbol_signals["risk_signals"].append(
                        {
                            "agent": agent,
                            "signal": signal_data.get("signal", "hold"),
                            "confidence": signal_data.get("confidence", 0.0),
                        }
                    )

            # Calculate consensus
            all_signals = cast("list[Any]", symbol_signals["analyst_signals"]) + cast(
                "list[Any]", symbol_signals["risk_signals"]
            )
            if all_signals:
                buy_signals = sum(1 for s in all_signals if s["signal"] in ["buy", "strong_buy"])
                sell_signals = sum(1 for s in all_signals if s["signal"] in ["sell", "strong_sell"])
                avg_confidence = sum(s["confidence"] for s in all_signals) / len(all_signals)

                if buy_signals > sell_signals:
                    symbol_signals["consensus"] = "buy"
                elif sell_signals > buy_signals:
                    symbol_signals["consensus"] = "sell"
                else:
                    symbol_signals["consensus"] = "hold"

                symbol_signals["confidence"] = avg_confidence

            signal_summary[symbol] = symbol_signals

        return signal_summary

    async def _generate_symbol_decision_llm(  # noqa: PLR0912, PLR0915
        self,
        symbol: str,
        portfolio: dict[str, Any],
        analyst_signals: dict[str, Any],
        risk_signals: dict[str, Any],
        state: CryptoAgentState,
    ) -> dict[str, Any]:
        """
        Generate trading decision for a single symbol using LLM.

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze
        portfolio : dict[str, Any]
            Current portfolio state
        analyst_signals : dict[str, Any]
            Technical analyst signals from other agents
        risk_signals : dict[str, Any]
            Risk assessment signals from other agents
        state : CryptoAgentState
            The current agent state

        Returns
        -------
        dict[str, Any]
            Trading decision for the symbol
        """
        # Collect all signals for this symbol
        symbol_analyst_signals = {}
        symbol_risk_signals = {}

        for agent_id, signals in analyst_signals.items():
            if symbol in signals:
                symbol_analyst_signals[agent_id] = signals[symbol]

        for agent_id, signals in risk_signals.items():
            if symbol in signals:
                symbol_risk_signals[agent_id] = signals[symbol]

        # Get current position
        positions = portfolio.get("positions", {})
        current_position = positions.get(symbol, {})
        cash = portfolio.get("cash", 0)

        # Calculate available metrics
        if "long" in current_position or "short" in current_position:
            long_amount = current_position.get("long", 0)
            short_amount = current_position.get("short", 0)
            current_price = current_position.get("current_price", 0)
        else:
            long_amount = current_position.get("amount", 0)
            short_amount = 0
            current_price = current_position.get("current_price", 0)

        # If current_price is 0, fetch from state's price_data
        if current_price == 0:
            price_data = state.get("price_data", {})
            if symbol in price_data:
                price_obj = price_data[symbol]
                if hasattr(price_obj, "price"):
                    current_price = price_obj.price
                elif isinstance(price_obj, dict):
                    current_price = price_obj.get("price", 0)
                logger.info("Fetched current price for %s from state: $%.2f", symbol, current_price)

        # Calculate portfolio metrics for LLM context
        total_value = portfolio.get("total_value", cash)
        unrealized_pnl = portfolio.get("unrealized_pnl", 0)
        available_margin = portfolio.get("available_margin", cash)

        # Calculate current exposure from all positions
        total_exposure = 0
        positions_count = 0
        for pos_data in positions.values():
            if pos_data:
                positions_count += 1
                # Calculate notional value of position
                pos_amount = pos_data.get("amount", 0)
                pos_price = pos_data.get("current_price", 0)
                pos_leverage = pos_data.get("leverage", 1)
                if pos_amount > 0 and pos_price > 0:
                    notional = pos_amount * pos_price * pos_leverage
                    total_exposure += notional

        current_exposure_pct = (total_exposure / total_value * 100) if total_value > 0 else 0
        remaining_capacity_pct = max(0, 80 - current_exposure_pct)  # 80% max safe exposure

        # Prepare prompt data with comprehensive portfolio state
        prompt_data = {
            "symbol": symbol,
            "analyst_signals": json.dumps(symbol_analyst_signals, indent=2),
            "risk_signals": json.dumps(symbol_risk_signals, indent=2),
            "current_position_long": long_amount,
            "current_position_short": short_amount,
            "current_price": current_price,
            "available_cash": cash,
            "portfolio_total": total_value,
            "unrealized_pnl": unrealized_pnl,
            "available_margin": available_margin,
            "positions_count": positions_count,
            "current_exposure_pct": f"{current_exposure_pct:.1f}",
            "remaining_capacity_pct": f"{remaining_capacity_pct:.1f}",
        }

        # Create prompt template for single symbol decision
        template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AGGRESSIVE FUTURES TRADER with a HIGH RISK, HIGH RETURN mandate.

🔥 TRADING PHILOSOPHY:
- MAXIMIZE PROFITS through aggressive positioning
- CAPITALIZE on every opportunity with significant leverage
- TAKE BOLD POSITIONS when signals align
- HOLD is for the weak - trade frequently and decisively

⚡ AGGRESSIVE DECISION RULES:
1. ANY bullish signal → BUY LONG immediately
2. ANY bearish signal → SELL SHORT immediately
3. Confidence >45% → MANDATORY TRADE
4. Confidence >60% → INCREASE POSITION SIZE by 50%
5. Confidence >75% → GO ALL IN with maximum leverage

 MAXIMUM LEVERAGE STRATEGY:
- Confidence >75%: 8-10x leverage (MAXIMUM AGGRESSION)
- Confidence 60-75%: 5-8x leverage (STRONG POSITION)
- Confidence 50-60%: 3-5x leverage (BALANCED AGGRESSION)
- Confidence 45-50%: 2-3x leverage (MINIMUM ENTRY)

⚠️ CRITICAL: POSITION SIZING WITH LEVERAGE
ALWAYS use this formula to calculate position_size in your JSON response:

position_size = (Available_Cash * Desired_Exposure_Percentage) / Leverage

Example 1: Want 40% exposure with 5x leverage:
- Cash: $10,000
- Exposure: 40% = 0.40
- Leverage: 5x
- position_size = ($10,000 * 0.40) / 5 = $800 ✅
- This creates $4,000 notional (40% of portfolio)

Example 2: Want 70% exposure with 8x leverage:
- Cash: $10,000
- Exposure: 70% = 0.70
- Leverage: 8x
- position_size = ($10,000 * 0.70) / 8 = $875 ✅
- This creates $7,000 notional (70% of portfolio)

🎯 TARGET EXPOSURE BY CONFIDENCE:
- Confidence >75%: Target 60-80% exposure (GO ALL IN)
- Confidence 60-75%: Target 40-60% exposure (STRONG)
- Confidence 50-60%: Target 25-40% exposure (MODERATE)
- Confidence 45-50%: Target 15-25% exposure (CAUTIOUS ENTRY)

MAXIMUM SAFE EXPOSURE: 80% of portfolio (to avoid liquidation)

REMEMBER: Fortune favors the bold. Your job is to make MONEY, not sit on cash!
""",
                ),
                (
                    "user",
                    """Analyze {symbol} and make a trading decision.

ANALYST SIGNALS:
{analyst_signals}

RISK SIGNALS:
{risk_signals}

📊 PORTFOLIO STATE:
- Portfolio Total Value: ${portfolio_total}
- Available Cash: ${available_cash}
- Available Margin: ${available_margin}
- Unrealized PnL: ${unrealized_pnl}
- Open Positions: {positions_count}
- Current Exposure: {current_exposure_pct}% of portfolio
- Remaining Capacity: {remaining_capacity_pct}% (max 80% total exposure)

📍 CURRENT POSITION FOR {symbol}:
- Long: {current_position_long}
- Short: {current_position_short}
- Current Price: ${current_price}

⚠️ CRITICAL POSITION SIZING FORMULA (TO AVOID LIQUIDATION):
position_size = (Portfolio_Total * Desired_Exposure_Percentage) / Leverage

⚠️ YOU HAVE {remaining_capacity_pct}% REMAINING CAPACITY (Current exposure: {current_exposure_pct}%)

Example: Want 40% exposure with 5x leverage on ${portfolio_total} portfolio:
- Portfolio Total: ${portfolio_total}
- Desired Exposure: 40% = 0.40
- Leverage: 5x
- position_size = (${portfolio_total} * 0.40) / 5 = ${portfolio_total} * 0.08 ✅
- This creates 40% notional exposure

QUICK REFERENCE FOR POSITION SIZING:
- With 5x leverage: position_size = portfolio * (exposure% / 5)
- With 8x leverage: position_size = portfolio * (exposure% / 8)
- With 10x leverage: position_size = portfolio * (exposure% / 10)

⚠️ DO NOT EXCEED {remaining_capacity_pct}% exposure for this trade!
Maximum safe position_size with 5x leverage: ${portfolio_total} * {remaining_capacity_pct}% / 5

Provide your decision in JSON format:
{{
  "symbol": "{symbol}",
  "action": "buy|sell|hold",
  "quantity": float (amount to buy/sell),
  "reasoning": "Detailed explanation of decision based on signals",
  "confidence": float (0-100),
  "target_price": float (deprecated, use take_profit_mid),
  "stop_loss": float (REQUIRED - absolute price),
  "position_size": float (USDT value of position - MUST follow formula above),
  "risk_level": "low|medium|high",
  "leverage": float (2-10x recommended for aggressive trading),
  "direction": "LONG|SHORT|NONE",
  "entry_price": float (optimal entry - current price is ${current_price}),
  "take_profit_short": float (absolute price for quick profit 3-6%),
  "take_profit_mid": float (absolute price for medium profit 8-15%),
  "take_profit_long": float (absolute price for extended profit 15-30%)
}}
""",
                ),
            ]
        )

        prompt = template.invoke(prompt_data)

        try:
            # Use LLM with structured output to ensure JSON response
            decision = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=CryptoPortfolioDecision,
                agent_name=self.agent_id,
                state=state,
            )

            # Convert to dict - let LLM decide everything
            decision_dict = decision.model_dump()

            # Log the LLM decision
            logger.info(
                "LLM decision for %s: action=%s, confidence=%.1f%%, leverage=%.1fx",
                symbol,
                decision_dict.get("action", "hold"),
                decision_dict.get("confidence", 0),
                decision_dict.get("leverage", 1),
            )

            # 💰 POSITION SIZING ENFORCEMENT 💰
            # Set default position size and recalculate quantity to prevent excessive exposure
            action = decision_dict.get("action", "hold")

            if action in ["buy", "sell"]:
                # Get leverage for exposure calculation
                leverage = decision_dict.get("leverage", 1.0)

                # Get position_size or set default to 15% of cash (aggressive but safe)
                position_size = decision_dict.get("position_size")

                if position_size is None or position_size <= 0:
                    # Default to 15% of available cash (BEFORE leverage)
                    position_size = cash * 0.15
                    logger.info(
                        "Setting default position size for %s: $%.2f (15%% of cash, %sx leverage)",
                        symbol,
                        position_size,
                        leverage,
                    )
                    decision_dict["position_size"] = position_size

                # ⚠️ CRITICAL: Validate position_size with leverage to prevent liquidation
                # Use PORTFOLIO VALUE (not just cash) to calculate exposure correctly
                leverage = decision_dict.get("leverage", 1.0)
                portfolio_value = portfolio.get("total_value", cash)

                if portfolio_value > 0 and leverage > 0:
                    # Calculate notional value that would be created
                    notional_value = position_size * leverage
                    exposure_pct = notional_value / portfolio_value

                    # If exposure exceeds 80%, adjust position_size
                    max_safe_exposure = 0.80  # 80% maximum for safety
                    if exposure_pct > max_safe_exposure:
                        old_position_size = position_size
                        # Recalculate position_size using the correct formula
                        position_size = (portfolio_value * max_safe_exposure) / leverage
                        decision_dict["position_size"] = position_size

                        logger.warning(
                            "LLM position_size exceeded safe limits for %s. "
                            "Adjusted: $%.2f (was $%.2f) with %dx leverage to achieve %.1f%% exposure "
                            "(notional $%.2f / portfolio $%.2f)",
                            symbol,
                            position_size,
                            old_position_size,
                            leverage,
                            max_safe_exposure * 100,
                            position_size * leverage,
                            portfolio_value,
                        )

                # Calculate quantity from position_size (USDT value) and current price
                # This ensures quantity is in coin units, not USDT
                if current_price > 0:
                    # quantity = position_size (USDT) / price (USDT per coin) = coins
                    calculated_quantity = position_size / current_price

                    # Update quantity with calculated value
                    decision_dict["quantity"] = calculated_quantity

                    logger.info(
                        "Position sizing for %s: position_size=$%.2f, price=$%.2f, quantity=%.6f %s, "
                        "leverage=%.1fx, notional=$%.2f (%.1f%% exposure)",
                        symbol,
                        position_size,
                        current_price,
                        calculated_quantity,
                        symbol,
                        leverage,
                        position_size * leverage,
                        (position_size * leverage / cash * 100) if cash > 0 else 0,
                    )
                else:
                    logger.warning("Current price is 0 for %s, cannot calculate quantity", symbol)
                    decision_dict["quantity"] = 0.0

            return decision_dict

        except Exception as e:
            logger.exception("Error in LLM symbol decision for %s", symbol)
            return {
                "symbol": symbol,
                "action": "hold",
                "quantity": 0.0,
                "reasoning": f"LLM decision error: {e!s}",
                "confidence": 0.0,
                "risk_level": "high",
                "error": str(e),
            }

    def _generate_trading_decisions(
        self,
        symbols: list[str],  # noqa: ARG002
        portfolio: dict[str, Any],  # noqa: ARG002
        analyst_signals: dict[str, Any],  # noqa: ARG002
        risk_signals: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, dict[str, Any]]:
        """
        Generate trading decisions for each symbol (DEPRECATED).

        This method is deprecated in favor of LLM-based decisions via analyze_symbol.
        Kept for backward compatibility but returns empty dict.
        """
        logger.warning("_generate_trading_decisions is deprecated, use analyze_symbol with LLM instead")
        return {}

    def _calculate_position_size(self, symbol: str, portfolio: dict[str, Any], action: str) -> float:
        """
        Calculate appropriate position size for a trading decision.

        Parameters
        ----------
        symbol : str
            Symbol to calculate position for
        portfolio : dict
            Current portfolio state
        action : str
            Trading action ("buy" or "sell")

        Returns
        -------
        float
            Position size (number of units)
        """
        positions = portfolio.get("positions", {})
        position = positions.get(symbol, {})
        cash = portfolio.get("cash", 0)

        # Handle both simple and long/short position structures
        if "long" in position or "short" in position:
            # Long/Short structure from PortfolioService
            long_amount = position.get("long", 0)
            # Net amount available to sell (long positions only)
            amount = long_amount
            current_price = position.get("current_price", 0)
        else:
            # Simple structure from CLI
            amount = position.get("amount", 0)
            current_price = position.get("current_price", 0)

        # If current_price is 0, try to fetch it from market
        if current_price == 0:
            try:
                price_data = json.loads(aster_get_price.invoke({"symbol": symbol, "exchange": "aster"}))
                current_price = price_data.get("price", 0)
                logger.info("Fetched current price for position sizing %s: %s", symbol, current_price)
            except Exception as e:
                logger.warning("Failed to fetch current price for %s: %s", symbol, e)
                current_price = 0

        if action == "buy":
            # Use 10% of available cash for new positions
            max_position_value = cash * 0.10

            if current_price > 0:
                return min(max_position_value / current_price, 1000)  # Cap at 1000 units
            return 0.0

        if action == "sell":
            # Sell 50% of current position
            return amount * 0.50

        return 0.0
