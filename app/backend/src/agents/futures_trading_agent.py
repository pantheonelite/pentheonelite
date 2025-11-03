"""Futures trading agent that integrates with Binance Futures."""

from typing import Any

import structlog
from app.backend.client.binance import (
    BinanceInsufficientBalanceError,
    BinanceOrderError,
    BinanceRateLimitError,
)
from app.backend.services.binance_futures_trading_service import BinanceFuturesTradingService

logger = structlog.get_logger(__name__)


class FuturesTradingAgent:
    """
    Agent for executing trades on Binance Futures.

    Integrates the completed Binance client with the agent decision-making system.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        enable_rate_limiting: bool = True,
    ):
        """
        Initialize futures trading agent.

        Parameters
        ----------
        config : dict[str, Any] | None
            Binance configuration (optional)
        enable_rate_limiting : bool
            Enable client-side rate limiting
        """
        self.service = BinanceFuturesTradingService(config)
        self.enable_rate_limiting = enable_rate_limiting

        logger.info("Futures trading agent initialized")

    async def execute_trading_decision(
        self,
        symbol: str,
        decision: dict[str, Any],
        portfolio_value: float,
        current_exposure: float = 0.0,
    ) -> dict[str, Any]:
        """
        Execute a trading decision from the agent system.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")
        decision : dict[str, Any]
            Trading decision from portfolio manager with keys:
            - action: "buy", "sell", "hold"
            - quantity: float
            - confidence: float (0-100)
            - leverage: float (1-10x, optional)
            - stop_loss: float (%, optional)
            - direction: "LONG", "SHORT", "NONE" (optional)
        portfolio_value : float
            Current portfolio value for risk checks
        current_exposure : float
            Current gross exposure (0.0-1.0)

        Returns
        -------
        dict[str, Any]
            Execution result with order details or error info
        """
        action = decision.get("action", "hold").lower()
        quantity = decision.get("quantity", 0.0)
        confidence = decision.get("confidence", 0.0)
        leverage = int(decision.get("leverage", 1))
        direction = decision.get("direction", "NONE")
        position_size = decision.get("position_size", 0.0)

        result: dict[str, Any] = {"symbol": symbol}

        if action == "hold" or confidence < 50.0:
            return self._build_skipped_result(result, action, confidence)

        side = {"buy": "BUY", "sell": "SELL"}.get(action)
        if not side:
            return self._build_skipped_result(result, action, confidence, unknown_action=True)

        try:
            await self.service.ainitialize_symbol(symbol, leverage=leverage)
            if quantity == 0.0 and position_size > 0.0:
                quantity = await self._calculate_quantity_from_position_size(symbol, position_size, leverage, result)
                if quantity is None:
                    return result

            logger.info(
                "Executing trading decision",
                symbol=symbol,
                action=action,
                quantity=quantity,
                confidence=confidence,
                leverage=leverage,
                direction=direction,
            )

            order = await self.service.aplace_order_with_limits(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                portfolio_value=portfolio_value,
                current_exposure=current_exposure,
                leverage=leverage,
            )

            result.update(self._build_order_result(order, side, quantity, leverage, direction))

            # Always place stop loss and take profit (derive from pct defaults when missing)
            entry_price = getattr(order, "average_price", None)
            if entry_price:
                # Stop Loss: use absolute price if provided, else compute from percentage
                stop_loss_price = decision.get("stop_loss")
                if stop_loss_price is None:
                    stop_loss_pct = float(decision.get("stop_loss_pct", 2.0))  # default 2%
                    stop_loss_price = self._calculate_stop_loss_price(entry_price, stop_loss_pct, side)
                await self._place_stop_loss_order(symbol, side, quantity, float(stop_loss_price), entry_price, result)

                # Take Profit: prefer absolute prices; otherwise compute from percentage defaults
                tp_short = decision.get("take_profit_short")
                tp_mid = decision.get("take_profit_mid")
                tp_long = decision.get("take_profit_long")

                if tp_short is None and tp_mid is None and tp_long is None:
                    tp_short_pct = float(decision.get("take_profit_short_pct", 1.0))  # 1%
                    tp_mid_pct = float(decision.get("take_profit_mid_pct", 2.0))  # 2%
                    tp_long_pct = float(decision.get("take_profit_long_pct", 3.0))  # 3%

                    if side == "BUY":
                        tp_short = entry_price * (1 + tp_short_pct / 100)
                        tp_mid = entry_price * (1 + tp_mid_pct / 100)
                        tp_long = entry_price * (1 + tp_long_pct / 100)
                    else:
                        tp_short = entry_price * (1 - tp_short_pct / 100)
                        tp_mid = entry_price * (1 - tp_mid_pct / 100)
                        tp_long = entry_price * (1 - tp_long_pct / 100)

                await self._place_take_profit_orders(symbol, side, quantity, tp_short, tp_mid, tp_long, result)

        except BinanceRateLimitError as e:
            logger.warning("Rate limit hit", symbol=symbol, error=str(e))
            result.update({"status": "rate_limited", "reason": str(e), "retry_after": getattr(e, "retry_after", None)})
        except BinanceInsufficientBalanceError as e:
            logger.warning("Insufficient balance", symbol=symbol, error=str(e))
            result.update({"status": "insufficient_balance", "reason": str(e)})
        except BinanceOrderError as e:
            logger.exception("Order error", symbol=symbol, error=str(e))
            result.update({"status": "order_error", "reason": str(e)})
        except Exception as e:
            logger.exception("Unexpected error executing trade", symbol=symbol)
            result.update({"status": "error", "reason": str(e)})

        if "status" not in result:
            result["status"] = "error"

        logger.info("Execution result", **result)
        return result

    def _build_skipped_result(
        self, result: dict[str, Any], action: str, confidence: float, *, unknown_action: bool = False
    ) -> dict[str, Any]:
        if unknown_action:
            result.update({"status": "skipped", "reason": f"Unknown action: {action}"})
        else:
            result.update(
                {
                    "status": "skipped",
                    "reason": f"Action is {action} with confidence {confidence}%",
                }
            )
        return result

    async def _calculate_quantity_from_position_size(
        self, symbol: str, position_size: float, leverage: int, result: dict[str, Any]
    ) -> float | None:
        current_price = await self.get_current_price(symbol)
        if current_price <= 0:
            result.update({"status": "error", "reason": f"Could not get current price for {symbol}"})
            return None
        quantity = position_size / current_price
        logger.info(
            "Calculated quantity from position size",
            symbol=symbol,
            position_size=position_size,
            current_price=current_price,
            leverage=leverage,
            quantity=quantity,
        )
        return quantity

    def _build_order_result(
        self, order: Any, side: str, quantity: float, leverage: int, direction: str
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "order_id": getattr(order, "order_id", None),
            "side": getattr(order, "side", side),
            "quantity": getattr(order, "quantity", quantity),
            "price": getattr(order, "average_price", None) or getattr(order, "price", None),
            "leverage": leverage,
            "direction": direction,
        }

    async def _place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss_price: float,
        entry_price: float,
        result: dict[str, Any],
    ) -> None:
        """
        Place a stop loss order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Original order side ("BUY" or "SELL")
        quantity : float
            Position quantity
        stop_loss_price : float
            Stop loss price (absolute price from LLM)
        entry_price : float
            Entry price for logging
        result : dict[str, Any]
            Result dictionary to update

        Returns
        -------
        None
        """
        try:
            stop_order = await self.service.client.aplace_order(
                symbol=symbol,
                side="SELL" if side == "BUY" else "BUY",  # Opposite side to close position
                order_type="STOP_MARKET",
                quantity=quantity,
                stop_price=stop_loss_price,
                reduce_only=True,
            )
            result["stop_loss_order_id"] = getattr(stop_order, "order_id", None)
            result["stop_loss_price"] = stop_loss_price
            logger.info(
                "Stop-loss order placed",
                order_id=stop_order.order_id,
                price=stop_loss_price,
                entry_price=entry_price,
            )
        except Exception as e:
            logger.warning("Failed to place stop-loss order", error=str(e))
            result["stop_loss_error"] = str(e)

    async def _place_take_profit_orders(
        self,
        symbol: str,
        side: str,
        quantity: float,
        tp_short: float | None,
        tp_mid: float | None,
        tp_long: float | None,
        result: dict[str, Any],
    ) -> None:
        """
        Place take profit orders at multiple levels.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Original order side ("BUY" or "SELL")
        quantity : float
            Position quantity
        tp_short : float | None
            Short-term take profit price
        tp_mid : float | None
            Mid-term take profit price
        tp_long : float | None
            Long-term take profit price
        result : dict[str, Any]
            Result dictionary to update

        Returns
        -------
        None
        """
        tp_orders = []

        # Calculate quantity per TP level (split position into 3 parts)
        tp_levels = [tp for tp in [tp_short, tp_mid, tp_long] if tp is not None]
        if not tp_levels:
            return

        quantity_per_tp = quantity / len(tp_levels)

        # Place TP orders
        for tp_price, tp_name in [(tp_short, "short"), (tp_mid, "mid"), (tp_long, "long")]:
            if tp_price is None:
                continue

            try:
                tp_order = await self.service.client.aplace_order(
                    symbol=symbol,
                    side="SELL" if side == "BUY" else "BUY",  # Opposite side to close position
                    order_type="TAKE_PROFIT_MARKET",
                    quantity=quantity_per_tp,
                    stop_price=tp_price,
                    reduce_only=True,
                )
                tp_orders.append(
                    {
                        "level": tp_name,
                        "order_id": getattr(tp_order, "order_id", None),
                        "price": tp_price,
                    }
                )
                logger.info(
                    "Take-profit order placed",
                    level=tp_name,
                    order_id=tp_order.order_id,
                    price=tp_price,
                    quantity=quantity_per_tp,
                )
            except Exception as e:
                logger.warning(
                    "Failed to place take-profit order",
                    level=tp_name,
                    error=str(e),
                )

        if tp_orders:
            result["take_profit_orders"] = tp_orders

    async def get_portfolio_state(self) -> dict[str, Any]:
        """
        Get current portfolio state from Binance Futures.

        Returns
        -------
        dict[str, Any]
            Portfolio state with balance and positions
        """
        try:
            balance = await self.service.aget_account_balance()
            positions = await self.service.aget_positions()

            return {
                "cash": balance["available_balance"],
                "total_balance": balance["total_balance"],
                "unrealized_pnl": balance["unrealized_pnl"],
                "positions": positions,
                "position_count": len(positions),
            }

        except Exception as e:
            logger.exception("Error getting portfolio state")
            return {
                "cash": 0.0,
                "total_balance": 0.0,
                "unrealized_pnl": 0.0,
                "positions": [],
                "position_count": 0,
                "error": str(e),
            }

    async def close_position(
        self,
        symbol: str,
        position_side: str = "BOTH",
    ) -> dict[str, Any]:
        """
        Close an open position.

        Parameters
        ----------
        symbol : str
            Trading symbol
        position_side : str
            Position side to close ("BOTH", "LONG", "SHORT")

        Returns
        -------
        dict[str, Any]
            Closure result
        """
        try:
            order = await self.service.aclose_position(symbol, position_side)
        except Exception as e:
            logger.exception("Error closing position", symbol=symbol)
            return {
                "status": "error",
                "reason": str(e),
                "symbol": symbol,
            }
        else:
            return {
                "status": "success",
                "symbol": symbol,
                "order_id": order.order_id,
                "side": order.side,
                "quantity": order.quantity,
                "position_side": position_side,
            }

    def _calculate_stop_loss_price(
        self,
        entry_price: float,
        stop_loss_pct: float,
        side: str,
    ) -> float:
        """
        Calculate stop-loss price based on entry and percentage.

        Parameters
        ----------
        entry_price : float
            Entry price
        stop_loss_pct : float
            Stop-loss percentage (e.g., 5.0 for 5%)
        side : str
            Order side ("BUY" or "SELL")

        Returns
        -------
        float
            Stop-loss trigger price
        """
        if side == "BUY":
            # Long position: stop below entry
            return entry_price * (1 - stop_loss_pct / 100)
        # Short position: stop above entry
        return entry_price * (1 + stop_loss_pct / 100)

    async def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        float
            Current price
        """
        try:
            return await self.service.aget_current_price(symbol)
        except Exception:
            logger.exception("Error getting current price", symbol=symbol)
            return 0.0

    async def aget_positions(self) -> list[dict[str, Any]]:
        """
        Asynchronously get current open positions.

        Returns
        -------
        list[dict[str, Any]]
            List of open positions
        """
        try:
            return await self.service.aget_positions()
        except Exception:
            logger.exception("Error getting positions")
            return []
