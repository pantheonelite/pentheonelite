from .portfolio import Portfolio
from .types import Action, ActionLiteral


class TradeExecutor:
    """Executes trades against a Portfolio with Backtester-identical semantics."""

    def execute_trade(
        self,
        symbol: str,
        action: ActionLiteral,
        quantity: float,
        current_price: float,
        portfolio: Portfolio,
    ) -> int:
        """Execute a crypto trade for the given symbol."""
        if quantity is None or quantity <= 0:
            return 0

        # Coerce to enum if strings provided
        try:
            action_enum = Action(action) if not isinstance(action, Action) else action
        except Exception:
            action_enum = Action.HOLD

        # For crypto, we only support buy/sell/hold (no shorting in spot trading)
        if action_enum == Action.BUY:
            return portfolio.apply_long_buy(symbol, int(quantity), float(current_price))
        if action_enum == Action.SELL:
            return portfolio.apply_long_sell(symbol, int(quantity), float(current_price))

        # hold or unknown action
        return 0
