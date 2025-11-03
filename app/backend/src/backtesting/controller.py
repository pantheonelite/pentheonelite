from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from app.backend.src.agents.agent_manager import AgentManager
from app.backend.src.agents.crypto_risk_manager import CryptoRiskManagerAgent
from app.backend.src.agents.portfolio_manager import CryptoPortfolioManagerAgent

from .portfolio import Portfolio
from .types import Action, AgentDecisions, AgentOutput, PortfolioSnapshot

if TYPE_CHECKING:
    from app.backend.src.graph.state import CryptoAgentState


class AgentController:
    """Responsible for invoking the crypto trading agents and normalizing outputs."""

    def __init__(self):
        """Initialize the agent controller with agent instances."""
        self._risk_manager = CryptoRiskManagerAgent()
        self._portfolio_manager = CryptoPortfolioManagerAgent()

    def run_crypto_agents(
        self,
        *,
        symbols: Sequence[str],
        start_date: str,
        end_date: str,
        portfolio: Portfolio | PortfolioSnapshot,
        model_name: str,
        model_provider: str,
        selected_analysts: Sequence[str] | None,  # noqa: ARG002
    ) -> AgentOutput:
        """Run the crypto agent workflow and return normalized output."""
        # Ensure we pass a plain snapshot dict to preserve legacy expectations
        if isinstance(portfolio, Portfolio):
            portfolio_payload: PortfolioSnapshot = portfolio.get_snapshot()
        else:
            portfolio_payload = portfolio

        # Convert portfolio to crypto format
        crypto_portfolio = self._convert_to_crypto_portfolio(portfolio_payload, symbols)

        # Create crypto agent state
        state: CryptoAgentState = {
            "messages": [],
            "data": {
                "symbols": list(symbols),
                "portfolio": crypto_portfolio,
                "current_prices": dict.fromkeys(symbols, 0.0),  # Will be populated by engine
                "start_date": start_date,
                "end_date": end_date,
                "analyst_signals": {},
                "risk_signals": {},
                "portfolio_signals": {},
            },
            "metadata": {
                "show_reasoning": False,
                "model_name": model_name,
                "model_provider": model_provider,
            },
        }

        try:
            # Run analyst agent through AgentManager
            analyst_agent_func = AgentManager.get_agent_function("crypto_analyst")
            if analyst_agent_func:
                analyst_state = analyst_agent_func(state)
                state["data"]["analyst_signals"] = analyst_state["data"]["analyst_signals"]

            # Run risk manager agent
            risk_state = self._risk_manager.run_agent(state)
            state["data"]["risk_signals"] = risk_state["data"]["risk_signals"]

            # Run portfolio manager agent
            portfolio_state = self._portfolio_manager.run_agent(state)
            state["data"]["portfolio_signals"] = portfolio_state["data"]["portfolio_signals"]

            # Extract decisions from portfolio manager
            portfolio_output = portfolio_state["data"]["portfolio_signals"].get("crypto_portfolio_manager", {})
            decisions = portfolio_output.get("decisions", {})

            # Normalize decisions to the expected format
            normalized_decisions: AgentDecisions = {}
            for symbol in symbols:
                if symbol in decisions:
                    decision = decisions[symbol]
                    action = decision.get("action", "hold")
                    qty = decision.get("quantity", 0)

                    # Basic coercions
                    try:
                        qty_val = float(qty)
                    except Exception:
                        qty_val = 0.0
                    try:
                        action = Action(action).value  # validate/coerce
                    except Exception:
                        action = Action.HOLD.value  # type: ignore[assignment]

                    normalized_decisions[symbol] = {"action": action, "quantity": qty_val}  # type: ignore[assignment]
                else:
                    normalized_decisions[symbol] = {"action": "hold", "quantity": 0.0}

            # Preserve any agent-provided signals
            normalized_output: AgentOutput = {
                "decisions": normalized_decisions,
                "analyst_signals": state["data"]["analyst_signals"],
                "risk_signals": state["data"]["risk_signals"],
                "portfolio_signals": state["data"]["portfolio_signals"],
            }
            return normalized_output

        except Exception:
            # Return default decisions on error
            default_decisions = {symbol: {"action": "hold", "quantity": 0.0} for symbol in symbols}
            return {
                "decisions": default_decisions,
                "analyst_signals": {},
                "risk_signals": {},
                "portfolio_signals": {},
            }

    def _convert_to_crypto_portfolio(self, portfolio: PortfolioSnapshot, symbols: Sequence[str]) -> dict[str, Any]:
        """Convert portfolio snapshot to crypto portfolio format."""
        positions = {}
        for symbol in symbols:
            pos = portfolio["positions"].get(symbol, {})
            positions[symbol] = {
                "amount": pos["long"] - pos["short"],  # Net position
                "cost_basis": pos["long_cost_basis"] if pos["long"] > 0 else pos["short_cost_basis"],
                "current_price": 0.0,  # Will be set by the engine
                "market_value": 0.0,  # Will be calculated
                "unrealized_pnl": 0.0,  # Will be calculated
            }

        return {
            "cash": portfolio["cash"],
            "positions": positions,
            "total_value": portfolio["cash"],  # Will be updated with market values
        }
