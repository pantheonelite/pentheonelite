"""
CZ (Changpeng Zhao) Agent - Binance Founder and Exchange Magnate.

This agent embodies the philosophy of Binance's founder, focusing on:
- Exchange operations and trading infrastructure
- Global market expansion and adoption
- User experience and accessibility
- Regulatory compliance and institutional adoption
- Market making and liquidity provision
- Strategic partnerships and ecosystem building
"""

import json
from typing import Any, Literal

import structlog
from app.backend.src.agents.base_agent import BaseCryptoAgent
from app.backend.src.graph.enhanced_state import CryptoAgentState
from app.backend.src.tools.crypto import aster_get_multi_price
from app.backend.src.utils.llm import call_llm_with_retry
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class CZAnalysis(BaseModel):
    """Analysis output from CZ Agent for FUTURES trading."""

    signal: Literal["LONG", "SHORT", "HOLD"]  # Futures positions
    confidence: float  # 0.0 to 1.0
    reasoning: str
    exchange_adoption: float | None = None  # 0.0 to 1.0
    liquidity_depth: float | None = None  # 0.0 to 1.0 (critical for futures)
    user_experience: float | None = None  # 0.0 to 1.0
    regulatory_compliance: float | None = None  # 0.0 to 1.0
    institutional_support: float | None = None  # 0.0 to 1.0
    market_accessibility: float | None = None  # 0.0 to 1.0
    key_insights: list[str] | None = None
    # Futures-specific fields
    futures_liquidity: float | None = None  # 0.0 to 1.0 (perpetuals liquidity)
    leverage_availability: str | None = None  # "HIGH", "MEDIUM", "LOW"


class CZBinanceAgent(BaseCryptoAgent):
    """
    CZ (Changpeng Zhao) Agent - Binance Founder and Exchange Magnate.

    This agent analyzes cryptocurrencies through the lens of a major exchange operator,
    focusing on trading infrastructure, market adoption, and user accessibility.
    """

    def __init__(
        self,
        agent_id: str = "cz_binance",
        use_langchain: bool = False,
        model_name: str | None = None,
        model_provider: str | None = None,
    ):
        super().__init__(
            agent_id,
            "CZ Binance Agent",
            use_langchain=use_langchain,
            model_name=model_name,
            model_provider=model_provider,
        )

    def _get_langchain_prompt(self) -> str:
        """Get custom LangChain prompt for CZ Binance agent."""
        return """You are Changpeng Zhao (CZ), founder of Binance.

Your expertise includes:
- Exchange operations and trading infrastructure
- Global market expansion and adoption
- User experience and accessibility
- Regulatory compliance and institutional adoption
- Market making and liquidity provision
- Strategic partnerships and ecosystem building

Your role is to analyze cryptocurrencies from an exchange operator's perspective:
1. Gather price, volume, and liquidity data
2. Evaluate exchange adoption and trading pairs
3. Assess market accessibility and user experience
4. Check regulatory compliance and institutional support
5. Provide clear trading signals for FUTURES positions

📊 PORTFOLIO AWARENESS:

Before analyzing {symbol}, check if there's an EXISTING position:

**If EXISTING LONG position**:
- Consider: Should we hold, add more, take profit, or reverse to SHORT?
- Factor in: Current profit/loss, your analysis alignment
- Your signal impacts: Whether to strengthen or close position

**If EXISTING SHORT position**:
- Consider: Should we hold, add more, cover (close), or reverse to LONG?
- Factor in: Current profit/loss, your analysis alignment
- Your signal impacts: Whether to strengthen or close position

**If NO position**:
- Your signal determines: Should we open LONG or SHORT?
- Normal analysis applies

Your recommendation should acknowledge existing positions when relevant.
Example: "Given existing LONG position with profit, exchange liquidity supports adding to position" or "Despite LONG position, declining exchange volumes suggest closing for profit"

Always provide:
- Signal: LONG, SHORT, or HOLD (for futures)
- Confidence: 0-1 (your certainty level)
- Reasoning: detailed market analysis
- Scores for exchange adoption, liquidity, regulatory compliance, and institutional support

Focus on projects with strong exchange support and liquidity."""

    async def _analyze_symbol_manual(
        self, symbol: str, state: CryptoAgentState, _progress_tracker=None
    ) -> dict[str, Any]:
        """
        Analyze a cryptocurrency symbol through CZ's lens.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol to analyze (e.g., "BNB/USDT")
        state : CryptoAgentState
            The current agent state with market data
        _progress_tracker : optional
            Progress tracker instance

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

            # Get portfolio data and check for existing position
            portfolio = state.get("data", {}).get("portfolio", {})
            total_value = portfolio.get("total_value", 0)
            cash = portfolio.get("cash", 0)
            positions = portfolio.get("positions", {})
            current_position = positions.get(symbol, {})

            # Extract position details if exists (available for future use)
            _ = current_position.get("side", "NONE") if current_position else "NONE"
            _ = current_position.get("unrealized_pnl", 0) if current_position else 0

            # Extract key metrics from collected data
            if hasattr(price_data, "price"):
                # PriceData object - access attributes directly
                current_price = price_data.price
                change_percent_24h = price_data.change_percent_24h
                high_24h = price_data.high_24h
                low_24h = price_data.low_24h
            else:
                # Dictionary - use get method
                current_price = price_data.get("price", 0)
                price_data.get("volume", 0)
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

            ADOPTION METRICS:
            - Price Trend: {"uptrend" if change_percent_24h > 0 else "downtrend" if change_percent_24h < 0 else "sideways"}
            - Volume Activity: {"high" if current_volume > avg_volume * 1.2 else "low" if current_volume < avg_volume * 0.8 else "normal"}
            - Market Interest: {"high" if news_count > 5 else "low" if news_count < 2 else "moderate"}
            """

            # Prepare prompt template
            prompt_template = self.get_llm_prompt_template()
            prompt = prompt_template.format_messages(
                base_symbol=base_symbol,
                symbol=symbol,
                current_price=current_price,
                market_data=analysis_context,
                total_value=total_value,
                cash=cash,
            )

            def default_signal():
                signal_model = self.get_signal_model()
                return signal_model(
                    signal="HOLD",
                    confidence=0.5,
                    reasoning="CZ Binance Agent incomplete; defaulting to hold",
                )

            # Call LLM for analysis
            crypto_output = call_llm_with_retry(
                prompt=prompt,
                pydantic_model=CZAnalysis,
                agent_name=self.agent_name,
                state=state,
                default_factory=default_signal,
            )

            return crypto_output.model_dump()

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "symbol": symbol,
                "signal": "HOLD",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Error in analysis: {e!s}",
                "exchange_adoption": 0.0,
                "liquidity_depth": 0.0,
                "user_experience": 0.0,
                "regulatory_compliance": 0.0,
                "institutional_support": 0.0,
                "market_accessibility": 0.0,
                "risk_assessment": "HIGH",
                "key_insights": ["Analysis failed"],
                "timestamp": self.get_current_timestamp(),
            }

    def get_llm_prompt_template(self) -> ChatPromptTemplate:
        """Get the LLM prompt template for generating analysis."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "user",
                    """As Changpeng Zhao (CZ), founder of Binance, analyze the cryptocurrency {base_symbol} ({symbol})
                    at current price ${current_price:,.2f} for FUTURES trading (LONG/SHORT positions with leverage).
                    {market_data}
                    Consider the following factors for FUTURES TRADING based on the data above:

                    1. FUTURES LIQUIDITY & DEPTH:
                    - Perpetual contract trading volume (higher = better for leverage)
                    - Order book depth for large leveraged orders
                    - Bid/Ask spread for efficient entry/exit with leverage
                    - Can we enter/exit 10x leveraged positions without slippage?

                    2. LEVERAGE AVAILABILITY:
                    - What leverage does Binance offer for this pair? (typically 1-125x)
                    - Trading volume supports what leverage level?
                    - High volume (>$100M/day) = safe for 10-20x leverage
                    - Low volume (<$10M/day) = caution, max 3-5x leverage

                    3. INSTITUTIONAL FUTURES PARTICIPATION:
                    - Volume metrics suggest institutional traders using leverage?
                    - Open interest growth indicates professional positioning?
                    - Large order flow patterns (institutional LONG or SHORT bias)?
                    - Funding rates history (institutional sentiment indicator)?

                    4. MARKET DIRECTION (LONG vs SHORT):
                    - Price trend: uptrend = LONG bias, downtrend = SHORT bias
                    - Volume confirmation: increasing volume with trend = strong directional signal
                    - Market momentum: strong momentum supports leveraged directional positions
                    - Should we go LONG (bullish) or SHORT (bearish)?

                    5. EXCHANGE ADOPTION FOR DERIVATIVES:
                    - Available on Binance Futures? (world's largest futures platform)
                    - Trading pairs availability (USDT-margined or coin-margined)?
                    - Perpetual contract features (funding rates, mark price system)?
                    - Global market reach for 24/7 liquidity?

                    6. REGULATORY & RISK MANAGEMENT:
                    - Exchange listings indicate regulatory approval for derivatives
                    - Insurance fund protection for liquidations?
                    - Auto-deleveraging (ADL) risk level?
                    - Institutional-grade risk management infrastructure?

                    7. USER EXPERIENCE FOR FUTURES:
                    - Volume trends: growing futures volume = bullish for LONG
                    - Accessibility: easy to trade with leverage?
                    - Liquidation engine performance: fair liquidation process?
                    - Funding rate stability: predictable carry costs?

                    8. LONG-TERM VIABILITY FOR LEVERAGED POSITIONS:
                    - Price trend (30-day): can sustain LONG or SHORT direction?
                    - Volatility: lower volatility = safer for higher leverage
                    - Market adoption: growing = LONG bias, declining = SHORT bias

                    Portfolio Context:
                    - Current portfolio value: ${total_value:,.2f}
                    - Available margin: ${cash:,.2f}

                    Based on the comprehensive futures market data above, provide your analysis as CZ in the following format:
                    {{
                        "signal": "LONG|SHORT|HOLD",
                        "confidence": float (0.0-1.0),
                        "reasoning": "Detailed explanation: WHY LONG or SHORT based on futures market data",
                        "exchange_adoption": float (0.0-1.0),
                        "liquidity_depth": float (0.0-1.0),
                        "user_experience": float (0.0-1.0),
                        "regulatory_compliance": float (0.0-1.0),
                        "institutional_support": float (0.0-1.0),
                        "market_accessibility": float (0.0-1.0),
                        "risk_assessment": "LOW|MEDIUM|HIGH",
                        "key_insights": ["insight1", "insight2", "insight3"],
                        "futures_liquidity": float (0.0-1.0),
                        "leverage_availability": "HIGH|MEDIUM|LOW"
                    }}

                    CRITICAL FOR FUTURES:
                    - LONG = bullish, profit when price increases (use on uptrends with volume confirmation)
                    - SHORT = bearish, profit when price decreases (use on downtrends with volume confirmation)
                    - HOLD = unclear direction or insufficient liquidity for leveraged positions
                    - Higher volume = safer for higher leverage
                    - Lower volume = more risk, use lower leverage or avoid

                    Remember: You are the founder of Binance, the world's largest crypto futures exchange.
                    Focus on REAL futures market data - perpetual contract liquidity, open interest, funding rates,
                    and leverage availability. Value assets with deep futures liquidity for safe leveraged trading.
                    Make data-driven decisions for LONG or SHORT based on exchange metrics and volume trends.""",
                )
            ]
        )

    def get_signal_model(self) -> type[BaseModel]:
        """Get the Pydantic model for the agent's signal output."""
        return CZAnalysis

    async def afetch_market_data(self, symbol: str, exchange: str = "binance") -> dict[str, Any]:
        """
        Fetch comprehensive market data for CZ analysis.

        Parameters
        ----------
        symbol : str
            The cryptocurrency symbol (e.g., "BTC/USDT")
        exchange : str
            Exchange to fetch data from (default: "binance")

        Returns
        -------
        dict[str, Any]
            Comprehensive market data including ticker, order book, and liquidity metrics

        """
        try:
            # Fetch data using @tool decorator functions
            # Note: @tool decorator functions return JSON strings that need to be parsed
            ticker_data_str = aster_get_multi_price.invoke({"symbols": symbol, "exchange": "aster"})
            ticker_data = json.loads(ticker_data_str)

            # For order book and OHLCV, we would use other tools
            # For now, extract from the multi-price response if available
            order_book_data = {}
            ohlcv_data = {}

            # Calculate liquidity metrics
            liquidity_metrics = self._calculate_liquidity_metrics(order_book_data) if order_book_data else {}

            # Calculate volume metrics
            volume_metrics = self._calculate_volume_metrics(ticker_data, ohlcv_data)

            # Calculate adoption metrics
            adoption_metrics = self._calculate_adoption_metrics(ticker_data, ohlcv_data)

            return {
                "ticker": {
                    "price": ticker_data.get("price", 0) if isinstance(ticker_data, dict) else 0,
                    "volume_24h": ticker_data.get("volume", 0) if isinstance(ticker_data, dict) else 0,
                    "change_24h": ticker_data.get("change_24h", 0) if isinstance(ticker_data, dict) else 0,
                    "change_percent_24h": ticker_data.get("change_percent_24h", 0)
                    if isinstance(ticker_data, dict)
                    else 0,
                    "high_24h": ticker_data.get("high_24h", 0) if isinstance(ticker_data, dict) else 0,
                    "low_24h": ticker_data.get("low_24h", 0) if isinstance(ticker_data, dict) else 0,
                }
                if ticker_data
                else {},
                "liquidity": liquidity_metrics,
                "volume": volume_metrics,
                "adoption": adoption_metrics,
                "exchange": "aster",
            }

        except Exception as e:
            logger.exception("Error fetching market data", symbol=symbol, exchange=exchange, error=str(e))
            return {
                "error": str(e),
                "ticker": {},
                "liquidity": {},
                "volume": {},
                "adoption": {},
                "exchange": exchange,
            }

    def _calculate_liquidity_metrics(self, order_book) -> dict[str, Any]:
        """
        Calculate liquidity metrics from order book data.

        Parameters
        ----------
        order_book : dict
            Order book data from Aster

        Returns
        -------
        dict[str, Any]
            Liquidity metrics including depth, spread, and order book analysis
        """
        try:
            # Aster returns dict with bids and asks
            bids = (
                order_book.get("bids", [])[:10]
                if isinstance(order_book, dict)
                else order_book.bids[:10]
                if hasattr(order_book, "bids")
                else []
            )
            asks = (
                order_book.get("asks", [])[:10]
                if isinstance(order_book, dict)
                else order_book.asks[:10]
                if hasattr(order_book, "asks")
                else []
            )

            if not bids or not asks:
                return {
                    "depth_score": 0.0,
                    "spread": 0.0,
                    "spread_percent": 0.0,
                    "bid_depth": 0.0,
                    "ask_depth": 0.0,
                }

            best_bid = bids[0][0] if bids else 0
            best_ask = asks[0][0] if asks else 0

            # Calculate spread
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            spread_percent = (spread / mid_price * 100) if mid_price > 0 else 0

            # Calculate order book depth (total volume in top 10 levels)
            bid_depth = sum(bid[1] * bid[0] for bid in bids)  # price * quantity
            ask_depth = sum(ask[1] * ask[0] for ask in asks)

            # Depth score (0-1) based on total liquidity
            total_depth = bid_depth + ask_depth
            depth_score = min(1.0, total_depth / 1_000_000)  # Normalize to $1M

            return {
                "depth_score": depth_score,
                "spread": spread,
                "spread_percent": spread_percent,
                "bid_depth": bid_depth,
                "ask_depth": ask_depth,
                "bid_levels": len(bids),
                "ask_levels": len(asks),
            }

        except Exception as e:
            logger.exception("Error calculating liquidity metrics", error=str(e))
            return {
                "depth_score": 0.0,
                "spread": 0.0,
                "spread_percent": 0.0,
                "bid_depth": 0.0,
                "ask_depth": 0.0,
            }

    def _calculate_volume_metrics(self, ticker, ohlcv: list) -> dict[str, Any]:
        """
        Calculate volume metrics from ticker and historical data.

        Parameters
        ----------
        ticker : CryptoData
            Current ticker data
        ohlcv : list[OHLCVData]
            Historical OHLCV data

        Returns
        -------
        dict[str, Any]
            Volume metrics including trends and analysis
        """
        try:
            current_volume = ticker.get("volume", 0) if ticker else 0

            if not ohlcv or len(ohlcv) < 7:
                return {
                    "volume_24h": current_volume,
                    "volume_7d_avg": 0,
                    "volume_trend": "unknown",
                    "volume_score": 0.0,
                }

            # Calculate 7-day average volume
            volumes_7d = [candle.volume for candle in ohlcv[-7:]]
            avg_volume_7d = sum(volumes_7d) / len(volumes_7d)

            # Calculate 30-day average volume
            volumes_30d = [candle.volume for candle in ohlcv]
            avg_volume_30d = sum(volumes_30d) / len(volumes_30d)

            # Volume trend
            if avg_volume_7d > avg_volume_30d * 1.2:
                volume_trend = "increasing"
            elif avg_volume_7d < avg_volume_30d * 0.8:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"

            # Volume score (0-1) based on 24h volume
            # High volume = better liquidity and adoption
            volume_score = min(1.0, current_volume / 100_000_000)  # Normalize to $100M daily volume

            return {
                "volume_24h": current_volume,
                "volume_7d_avg": avg_volume_7d,
                "volume_30d_avg": avg_volume_30d,
                "volume_trend": volume_trend,
                "volume_score": volume_score,
            }

        except Exception as e:
            logger.exception("Error calculating volume metrics", error=str(e))
            return {
                "volume_24h": 0,
                "volume_7d_avg": 0,
                "volume_trend": "unknown",
                "volume_score": 0.0,
            }

    def _calculate_adoption_metrics(self, ticker, ohlcv: list) -> dict[str, Any]:
        """
        Calculate adoption metrics from market data.

        Parameters
        ----------
        ticker : CryptoData
            Current ticker data
        ohlcv : list[OHLCVData]
            Historical OHLCV data

        Returns
        -------
        dict[str, Any]
            Adoption metrics including market trends and accessibility
        """
        try:
            if not ticker or not ohlcv:
                return {
                    "price_trend": "unknown",
                    "volatility": 0.0,
                    "momentum": 0.0,
                    "adoption_score": 0.0,
                }

            # Calculate price trend over 30 days
            if len(ohlcv) >= 30:
                price_30d_ago = ohlcv[0].close
                current_price = ticker.get("price", 0)
                price_change_30d = ((current_price - price_30d_ago) / price_30d_ago * 100) if price_30d_ago > 0 else 0

                if price_change_30d > 20:
                    price_trend = "strong_uptrend"
                elif price_change_30d > 5:
                    price_trend = "uptrend"
                elif price_change_30d < -20:
                    price_trend = "strong_downtrend"
                elif price_change_30d < -5:
                    price_trend = "downtrend"
                else:
                    price_trend = "sideways"
            else:
                price_trend = "unknown"
                price_change_30d = 0

            # Calculate volatility (standard deviation of returns)
            if len(ohlcv) >= 7:
                closes = [candle.close for candle in ohlcv[-30:]]
                returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
                volatility = (sum([(r - sum(returns) / len(returns)) ** 2 for r in returns]) / len(returns)) ** 0.5
                volatility_percent = volatility * 100
            else:
                volatility_percent = 0

            # Momentum score based on recent performance
            momentum = ticker.get("change_percent_24h", 0) if ticker else 0

            # Overall adoption score (0-1) - combination of trend, volume, and stability
            adoption_score = 0.5  # Base score
            if price_trend in ["uptrend", "strong_uptrend"]:
                adoption_score += 0.2
            if volatility_percent < 5:  # Low volatility = stability
                adoption_score += 0.15
            if momentum > 0:
                adoption_score += 0.15

            adoption_score = min(1.0, max(0.0, adoption_score))

            return {
                "price_trend": price_trend,
                "price_change_30d": price_change_30d,
                "volatility": volatility_percent,
                "momentum": momentum,
                "adoption_score": adoption_score,
            }

        except Exception as e:
            logger.exception("Error calculating adoption metrics", error=str(e))
            return {
                "price_trend": "unknown",
                "volatility": 0.0,
                "momentum": 0.0,
                "adoption_score": 0.0,
            }
