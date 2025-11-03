"""Enhanced technical analysis node integrating crypto agents and tools."""

from datetime import datetime
from typing import Any

import structlog
from app.backend.src.graph.enhanced_state import CryptoAgentState, SignalType, TechnicalSignal

from .base_node import BaseNode

logger = structlog.get_logger(__name__)


class EnhancedTechnicalAnalysisNode(BaseNode):
    """
    Enhanced technical analysis node using crypto trading tools.

    This node integrates:
    - Aster API tools for market data
    - Technical indicators for chart analysis
    - Trading strategy tools for decision making
    - News and sentiment data
    """

    def __init__(self):
        super().__init__(
            name="enhanced_technical_analysis",
            description="Performs comprehensive technical analysis using crypto trading tools and agents",
        )

    def get_required_data(self) -> list[str]:
        """Get required input data fields."""
        return ["symbols"]

    def get_output_data(self) -> list[str]:
        """Get output data fields produced by this node."""
        return ["technical_signals", "technical_indicators", "strategy_signals"]

    def execute(self, state: CryptoAgentState) -> CryptoAgentState:
        """
        Execute enhanced technical analysis using crypto tools.

        Parameters
        ----------
        state : CryptoAgentState
            Current workflow state

        Returns
        -------
        CryptoAgentState
            Updated state with technical analysis results
        """
        symbols = state["symbols"]
        timeframe = state.get("timeframe", "1h")
        technical_signals = {}
        technical_indicators = {}
        strategy_signals = {}

        for symbol in symbols:
            try:
                logger.info("Analyzing %s with technical tools", symbol)

                # Step 1: Fetch current price data
                price_data = self._fetch_price_data(symbol)
                if not price_data:
                    continue

                # Step 2: Fetch historical data
                historical_data = self._fetch_historical_data(symbol, timeframe, 100)
                if not historical_data:
                    continue

                # Step 3: Calculate technical indicators
                indicators = self._calculate_indicators(symbol, historical_data)
                technical_indicators[symbol] = indicators

                # Step 4: Analyze trading strategy
                strategy = self._analyze_strategy(symbol, price_data, indicators)
                strategy_signals[symbol] = strategy

                # Step 5: Determine overall signal
                signal = self._generate_signal(price_data, indicators, strategy)

                technical_signals[symbol] = TechnicalSignal(
                    signal=signal["signal_type"],
                    confidence=signal["confidence"],
                    indicators=indicators,
                    reasoning=signal["reasoning"],
                    timestamp=datetime.now(),
                )

            except Exception as e:
                logger.exception("Error analyzing %s: %s", symbol, e)
                technical_signals[symbol] = TechnicalSignal(
                    signal=SignalType.HOLD,
                    confidence=0.0,
                    indicators={},
                    reasoning=f"Error in technical analysis: {e!s}",
                    timestamp=datetime.now(),
                )

        state["technical_signals"] = technical_signals
        state["technical_indicators"] = technical_indicators
        state["strategy_signals"] = strategy_signals

        return state

    def _fetch_price_data(self, symbol: str) -> dict[str, Any] | None:
        """Fetch current price data using ToolManager."""
        aster_symbol = self.to_aster_symbol(symbol)
        return self.execute_tool_safely("aster_price", {"symbol": aster_symbol})

    def _fetch_historical_data(self, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]] | None:
        """Fetch historical data using ToolManager."""
        aster_symbol = self.to_aster_symbol(symbol)
        result = self.execute_tool_safely(
            "aster_history", {"symbol": aster_symbol, "timeframe": timeframe, "limit": limit}
        )
        return result if isinstance(result, list) else None

    def _calculate_indicators(self, symbol: str, historical_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate technical indicators using ToolManager."""
        result = self.execute_tool_safely("technical_indicators", {"symbol": symbol, "klines": historical_data})
        return result or {}

    def _analyze_strategy(self, symbol: str, price_data: dict[str, Any], indicators: dict[str, Any]) -> dict[str, Any]:
        """Analyze trading strategy using ToolManager."""
        result = self.execute_tool_safely(
            "trading_strategy", {"symbol": symbol, "indicators": indicators, "price_data": price_data}
        )
        return result or {}

    def _generate_signal(
        self, price_data: dict[str, Any], indicators: dict[str, Any], strategy: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate overall trading signal from analysis components.

        Parameters
        ----------
        price_data : dict
            Current price data
        indicators : dict
            Technical indicators
        strategy : dict
            Trading strategy analysis

        Returns
        -------
        dict
            Signal with type, confidence, and reasoning
        """
        # Simple signal generation logic
        # This can be enhanced with more sophisticated analysis

        # Get RSI if available
        rsi = indicators.get("rsi", 50.0)
        macd_signal = indicators.get("macd_signal", "neutral")

        # Determine signal based on indicators
        if rsi > 70:
            signal_type = SignalType.SELL
            confidence = min(0.9, (rsi - 50) / 50)
            reasoning = f"Overbought: RSI={rsi:.2f}"
        elif rsi < 30:
            signal_type = SignalType.BUY
            confidence = min(0.9, (50 - rsi) / 50)
            reasoning = f"Oversold: RSI={rsi:.2f}"
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
            reasoning = f"Neutral: RSI={rsi:.2f}, MACD={macd_signal}"

        # Incorporate strategy if available
        if strategy:
            strategy_signal = strategy.get("signal", "hold")
            strategy_confidence = strategy.get("confidence", 0.0)

            # Weight the signals
            if strategy_signal in ["buy", "strong_buy"] and signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                signal_type = SignalType.STRONG_BUY if strategy_confidence > 0.7 else SignalType.BUY
                confidence = (confidence + strategy_confidence) / 2
                reasoning += f", Strategy: {strategy_signal} (confidence={strategy_confidence:.2f})"

        return {
            "signal_type": signal_type,
            "confidence": max(0.0, min(1.0, confidence)),
            "reasoning": reasoning,
        }
