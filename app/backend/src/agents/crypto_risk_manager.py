"""Simplified cryptocurrency risk management agent."""

import asyncio
import concurrent.futures
from typing import Any, Literal

from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, field_validator


class CryptoRiskSignal(BaseModel):
    """Signal output from crypto risk manager agent."""

    signal: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    confidence: float  # 0-100
    reasoning: str
    portfolio_risk: float | None = None
    position_risk: float | None = None
    market_risk: float | None = None
    liquidity_risk: float | None = None
    position_size: float | None = None
    max_position_size: float | None = None
    stop_loss: float | None = None
    warnings: list[str] = []
    alerts: list[str] = []

    @field_validator("signal", mode="before")
    @classmethod
    def normalize_signal(cls, v):
        """Normalize signal to lowercase (handles STRONG_BUY → strong_buy)."""
        if isinstance(v, str):
            return v.lower().replace(" ", "_")
        return v

    @field_validator(
        "portfolio_risk",
        "position_risk",
        "market_risk",
        "liquidity_risk",
        "position_size",
        "max_position_size",
        "stop_loss",
        mode="before",
    )
    @classmethod
    def coerce_to_float(cls, v):
        """Coerce numeric fields to float, handle strings and None."""
        if v is None or v == "None":
            return None
        if isinstance(v, str):
            if v in ["Error in analysis", "Unknown", ""]:
                return None
            try:
                return float(v)
            except ValueError:
                return None
        if isinstance(v, (int, float)):
            return float(v)
        return None

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v):
        """Coerce confidence to float, ensure 0-100 range."""
        if v is None:
            return 0.0
        if isinstance(v, str):
            try:
                val = float(v)
            except ValueError:
                return 0.0
        else:
            val = float(v) if isinstance(v, (int, float)) else 0.0
        return max(0.0, min(100.0, val))


class CryptoRiskManagerAgent(BaseCryptoAgent):
    """Simplified cryptocurrency risk management agent."""

    def __init__(self, model_name: str | None = None, model_provider: str | None = None):
        super().__init__(
            agent_id="crypto_risk_manager",
            agent_name="Crypto Risk Manager",
            model_name=model_name,
            model_provider=model_provider,
        )

    async def _analyze_symbol_manual(
        self,
        symbol: str,
        state: CryptoAgentState,
        progress_tracker=None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Analyze risk for a single crypto symbol using existing signals (manual mode).

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTCUSDT")
        state : CryptoAgentState
            The current agent state containing technical, sentiment, and persona signals
        progress_tracker : optional
            Progress tracker instance

        Returns
        -------
        dict[str, Any]
            Risk analysis results for the symbol
        """
        try:
            # Get existing signals from state
            technical_signals = state.get("technical_signals", {})
            sentiment_signals = state.get("sentiment_signals", {})
            persona_consensus = state.get("persona_consensus", {})

            # Extract signals for this symbol
            tech_signal = technical_signals.get("crypto_technical", {}).get(symbol, {})
            sent_signal = sentiment_signals.get("crypto_sentiment", {}).get(symbol, {})
            persona_signal = persona_consensus.get(symbol, {})

            # Compile signal data for LLM analysis
            signal_data = {
                "symbol": symbol,
                "technical_signal": {
                    "signal": tech_signal.get("signal", "HOLD"),
                    "confidence": tech_signal.get("confidence", 0.5),
                    "reasoning": tech_signal.get("reasoning", "No technical analysis available"),
                },
                "sentiment_signal": {
                    "signal": sent_signal.get("signal", "NEUTRAL"),
                    "confidence": sent_signal.get("confidence", 0.5),
                    "reasoning": sent_signal.get("reasoning", "No sentiment analysis available"),
                },
                "persona_consensus": {
                    "signal": persona_signal.get("signal", "HOLD"),
                    "confidence": persona_signal.get("confidence", 0.5),
                    "count": persona_signal.get("count", 0),
                    "personas": persona_signal.get("personas", []),
                },
            }

            # Generate comprehensive risk assessment using LLM
            risk_output = self.generate_llm_analysis(symbol, signal_data, state)
            # Convert to JSON-serializable dict
            return risk_output.model_dump()

        except Exception as e:
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": f"Error in risk analysis: {e!s}",
                "warnings": [f"Risk analysis failed: {e!s}"],
                "error": str(e),
            }

    def analyze_symbol(self, symbol: str, state: CryptoAgentState) -> dict[str, Any]:
        """
        Analyze risk for a single crypto symbol using existing signals (sync wrapper).

        Parameters
        ----------
        symbol : str
            The crypto symbol to analyze (e.g., "BTCUSDT")
        state : CryptoAgentState
            The current agent state containing technical, sentiment, and persona signals

        Returns
        -------
        dict[str, Any]
            Risk analysis results for the symbol
        """
        # Run the async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create a new loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._analyze_symbol_manual(symbol, state, None))
                    return future.result()
            return loop.run_until_complete(self._analyze_symbol_manual(symbol, state, None))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self._analyze_symbol_manual(symbol, state, None))

    def get_signal_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the agent's signal output."""
        return CryptoRiskSignal

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """Get the LLM prompt template for generating risk assessment."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AGGRESSIVE cryptocurrency FUTURES risk manager focused on MAXIMIZING RETURNS.
                    Your job is to ENABLE trades, not prevent them. Find reasons to TRADE, not reasons to HOLD.

📊 PORTFOLIO CONTEXT AWARENESS:

When analyzing risk, you will see current positions with these fields:
- `side`: "LONG" or "SHORT" - direction of position
- `unrealized_pnl`: Current profit/loss (monitor for risk)
- `leverage`: Multiplier (higher = more risky)
- `notional`: Total exposure in USDT
- `liquidation_price`: Danger zone price

**Risk Assessment for Existing Positions**:

1. **Position at Profit** (`unrealized_pnl` > 0):
   - If trend continues + high confidence → Recommend ADD_TO
   - If target reached → Recommend CLOSE (take profit)
   - If risk increases → Recommend REDUCE

2. **Position at Loss** (`unrealized_pnl` < 0):
   - If trend reversing → URGENT: Recommend CLOSE
   - If stop-loss hit → URGENT: Recommend CLOSE
   - If temporary dip in uptrend → Recommend HOLD or ADD_TO (averaging)

3. **High Leverage Risk** (leverage > 7x):
   - Monitor `liquidation_price` proximity
   - If price within 10% of liquidation → URGENT: Recommend REDUCE or CLOSE
   - Warn about margin calls

4. **Concentration Risk**:
   - If single position > 40% of total capital → Recommend diversify
   - If correlated positions → Warn about correlation risk

🎯 AGGRESSIVE FUTURES TRADING FOCUS:
- LONG positions (BUY): Profit when price INCREASES - recommend with ANY bullish edge
- SHORT positions (SELL): Profit when price DECREASES - recommend with ANY bearish edge
- Leverage aggressively: Higher leverage = HIGHER PROFITS (with proper stops)

Consider these factors:
- Technical analysis signals (PRIMARY - weighted 50%)
- Market sentiment and momentum (weighted 30%)
- Persona consensus (weighted 20%)
- Volatility = OPPORTUNITY not threat

⚠️ CRITICAL: Be MAXIMALLY AGGRESSIVE
- **Confidence >65%** = STRONG recommendation (strong_buy/strong_sell) with 7-10x leverage
- **Confidence 50-65%** = MODERATE recommendation (buy/sell) with 5-7x leverage
- **Confidence 45-50%** = STILL TRADE with 3-5x leverage (don't waste opportunities)
- **Confidence <45%** = HOLD only (very rare - signals must be truly unclear)
- **Mixed signals** = ALWAYS pick a direction (technical signal wins)

💡 AGGRESSIVE LEVERAGE RECOMMENDATIONS:
- **Low volatility + high confidence** = MAX 8-10x leverage (OPTIMAL for gains)
- **Medium volatility** = STRONG 5-8x leverage (still aggressive)
- **High volatility** = MODERATE 3-5x leverage (ride the waves)
- **Default bias**: HIGHER leverage when technical signals are clear

🛡️ AGGRESSIVE RISK MANAGEMENT:
- Set wider stop-loss levels (5-8% from entry for leveraged positions)
- Position size: 15-40% of available margin per trade (SIZE matters)
- Accept 3-5% account risk per position (MAXIMIZE opportunities)
- Liquidation price: Calculate but DON'T be overly conservative

**TRADING MINDSET**:
- IDLE CAPITAL = WASTED OPPORTUNITY
- In futures, BOTH directions profit - NEVER default to HOLD
- Take calculated risks - that's how you WIN BIG
- Trust the signals - if 50%+ confidence, TRADE IT

Return ONLY the JSON specified below.""",
                ),
                (
                    "human",
                    """Cryptocurrency: {symbol}

Signal Analysis Data:
{analysis_data}

🎯 DECISION FRAMEWORK FOR FUTURES:

**Analyze Signals:**
1. Technical signal direction and confidence
2. Sentiment signal direction and confidence
3. Persona consensus (majority opinion + avg confidence)

**Determine Recommendation:**

- **STRONG_BUY** (LONG with MAX leverage):
  - Technical + Sentiment + Persona ALL bullish (>65% confidence)
  - Clear uptrend with momentum
  - Suggest 7-10x leverage ALWAYS (maximize gains)

- **BUY** (LONG with high leverage):
  - Majority bullish OR technical bullish alone (50-65%)
  - Any upward bias detected
  - Suggest 5-7x leverage (still aggressive)

- **SELL** (SHORT with high leverage):
  - Majority bearish OR technical bearish alone (50-65%)
  - Any downward bias detected
  - Suggest 5-7x leverage (profit from drops)

- **STRONG_SELL** (SHORT with MAX leverage):
  - Technical + Sentiment + Persona ALL bearish (>65% confidence)
  - Clear downtrend with momentum
  - Suggest 7-10x leverage ALWAYS (maximize short gains)

- **HOLD** (No position - RARE):
  - All signals truly mixed with <45% confidence
  - Genuinely no directional bias whatsoever
  - DEFAULT: If unsure between HOLD and trade → TRADE

**Aggressive Risk Assessment:**
- Set stop_loss: 5-8% from current price (WIDER stops for volatility)
- Position size: LARGE based on confidence (15-40% margin per trade)
- Max position size: UP TO 40% for highest conviction trades
- Liquidation price: Calculate but prioritize PROFIT potential over safety

Respond EXACTLY in this JSON schema:
{{
  "signal": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
  "confidence": float (0-100),
  "reasoning": "string (MUST explain: signal analysis, why LONG/SHORT/HOLD, leverage rationale)",
  "portfolio_risk": float | null (0-1, overall portfolio risk level),
  "position_risk": float | null (0-1, this specific position risk),
  "market_risk": float | null (0-1, current market condition risk),
  "liquidity_risk": float | null (0-1, symbol liquidity risk),
  "position_size": float | null (suggested % of margin to use, 10-30%),
  "max_position_size": float | null (maximum % of margin, typically 30-40%),
  "stop_loss": float | null (% loss threshold, typically 3-5%),
  "warnings": ["string - leverage warnings, volatility alerts, etc."],
  "alerts": ["string - urgent issues requiring immediate attention"]
}}""",
                ),
            ]
        )
