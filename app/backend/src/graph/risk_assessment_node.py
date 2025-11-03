"""Risk assessment node for crypto trading workflow."""

from datetime import datetime

from .base_node import safe_execute_node
from .enhanced_state import CryptoAgentState, RiskAssessment, RiskLevel


def risk_assessment_node(state: CryptoAgentState) -> CryptoAgentState:
    """
    Perform risk assessment on all symbols.

    Parameters
    ----------
    state : CryptoAgentState
        Current workflow state

    Returns
    -------
    CryptoAgentState
        Updated state with risk assessments
    """
    required_fields = ["symbols", "technical_signals", "sentiment_signals"]

    def execute_risk_assessment(state: CryptoAgentState) -> CryptoAgentState:
        symbols = state["symbols"]
        technical_signals = state.get("technical_signals", {})
        sentiment_signals = state.get("sentiment_signals", {})
        risk_assessments = {}

        for symbol in symbols:
            try:
                # Get technical and sentiment signals
                tech_signal = technical_signals.get(symbol)
                sent_signal = sentiment_signals.get(symbol)

                # Calculate risk metrics
                portfolio_risk = 0.1  # Default 10% portfolio risk
                position_risk = 0.05  # Default 5% position risk
                market_risk = 0.15  # Default 15% market risk
                liquidity_risk = 0.05  # Default 5% liquidity risk

                # Adjust risk based on signals
                if tech_signal and sent_signal:
                    # High confidence signals reduce risk
                    avg_confidence = (tech_signal.confidence + sent_signal.confidence) / 2.0
                    risk_reduction = avg_confidence * 0.1

                    portfolio_risk = max(0.05, portfolio_risk - risk_reduction)
                    position_risk = max(0.02, position_risk - risk_reduction)
                    market_risk = max(0.10, market_risk - risk_reduction)

                # Calculate overall risk level
                overall_risk = (portfolio_risk + position_risk + market_risk + liquidity_risk) / 4.0

                if overall_risk > 0.15:
                    risk_level = RiskLevel.HIGH
                elif overall_risk > 0.10:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.LOW

                # Calculate position sizing
                max_position_size = min(0.1, 0.2 - overall_risk)  # Max 10-20% position
                stop_loss = min(0.1, overall_risk * 2)  # Stop loss based on risk

                risk_assessments[symbol] = RiskAssessment(
                    risk_level=risk_level,
                    portfolio_risk=portfolio_risk,
                    position_risk=position_risk,
                    market_risk=market_risk,
                    liquidity_risk=liquidity_risk,
                    max_position_size=max_position_size,
                    stop_loss=stop_loss,
                    reasoning=f"Risk assessment: overall={overall_risk:.3f}, level={risk_level.value}, max_position={max_position_size:.3f}",
                    timestamp=datetime.now(),
                )

            except Exception as e:
                risk_assessments[symbol] = RiskAssessment(
                    risk_level=RiskLevel.HIGH,
                    portfolio_risk=0.2,
                    position_risk=0.1,
                    market_risk=0.2,
                    liquidity_risk=0.1,
                    max_position_size=0.05,
                    stop_loss=0.1,
                    reasoning=f"Error in risk assessment: {e!s}",
                    timestamp=datetime.now(),
                )

        state["risk_assessments"] = risk_assessments
        return state

    return safe_execute_node(
        node_name="risk_assessment",
        execute_func=execute_risk_assessment,
        state=state,
        required_fields=required_fields,
        progress_update=0.8,
    )
