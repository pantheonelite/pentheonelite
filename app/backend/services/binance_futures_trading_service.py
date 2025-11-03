"""Binance Testnet Futures trading service with risk management."""

from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Any

import structlog
from app.backend.client.binance import BinanceClient, BinanceFuturesOrder
from app.backend.config.binance import BinanceConfig, get_binance_settings

logger = structlog.get_logger(__name__)


class OrderValidationError(Exception):
    """Exception raised when order validation fails."""


class InsufficientBalanceError(OrderValidationError):
    """Exception raised when insufficient balance for order."""


class PositionLimitError(OrderValidationError):
    """Exception raised when position limit exceeded."""


class BinanceFuturesTradingService:
    """
    Trading service with risk management for Binance Testnet Futures.

    Provides order validation, position size limits, and portfolio exposure checks.
    """

    def __init__(self, config: BinanceConfig | None = None):
        """
        Initialize Binance Futures trading service.

        Parameters
        ----------
        config : BinanceConfig | None
            Binance client configuration. If None, loads from settings.
        """
        binance_settings = get_binance_settings()

        if config is None:
            config = BinanceConfig(
                api_key=binance_settings.api_key,
                api_secret=binance_settings.api_secret,
                testnet=binance_settings.testnet,
                timeout=binance_settings.timeout,
            )

        self.client = BinanceClient(config)
        self.config = config

        # Risk limits from settings
        self.max_position_pct = binance_settings.max_position_pct
        self.max_gross_exposure = binance_settings.max_gross_exposure
        self.min_order_size = binance_settings.min_order_size
        self.max_order_size = binance_settings.max_order_size

        self.default_leverage = binance_settings.default_leverage
        self.symbol_filters_cache: dict[str, dict[str, Any]] = {}

    async def aget_account_balance(self) -> dict[str, float]:
        """
        Fetch current Binance Futures account balance.

        Returns
        -------
        dict[str, float]
            Account balance information with keys:
            - total_balance: Total account value
            - available_balance: Available for trading
            - used_balance: Currently in positions
            - unrealized_pnl: Unrealized profit/loss
        """
        try:
            account = await self.client.aget_account_info()
            usdt_asset = next((asset for asset in account.assets if asset.get("asset") == "USDT"), None)

            if usdt_asset:
                total_balance = float(usdt_asset.get("walletBalance", 0.0))
                available_balance = float(usdt_asset.get("availableBalance", 0.0))
                used_balance = total_balance - available_balance
            else:
                total_balance = account.total_balance
                available_balance = account.available_balance
                used_balance = account.used_balance

            return {
                "total_balance": total_balance,
                "available_balance": available_balance,
                "used_balance": used_balance,
                "unrealized_pnl": account.unrealized_pnl,
                "asset_breakdown": account.assets,
            }
        except Exception as e:
            logger.exception("Failed to get account balance", error=str(e))
            raise

    async def ainitialize_symbol(self, symbol: str, leverage: int | None = None) -> None:
        """
        Initialize symbol for trading (set leverage and margin type).

        Parameters
        ----------
        symbol : str
            Trading symbol
        leverage : int | None
            Leverage (1-125), uses default if None
        """
        if leverage is None:
            leverage = self.default_leverage

        try:
            # Set margin type to CROSSED (ignore error if already set)
            await self.client.aset_margin_type(symbol, "CROSSED")

            # Set leverage
            await self.client.aset_leverage(symbol, leverage)

            logger.info("Symbol initialized", symbol=symbol, leverage=leverage)
        except Exception as e:
            logger.exception("Failed to initialize symbol", symbol=symbol, error=str(e))
            raise

    async def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float | None,
        order_type: str,
        portfolio_value: float,
        current_exposure: float = 0.0,
        leverage: int = 1,
    ) -> dict[str, str | float | bool]:
        """
        Validate order against risk limits.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")
        side : str
            Order side ("BUY" or "SELL")
        quantity : float
            Order quantity
        price : float | None
            Order price (for LIMIT orders)
        order_type : str
            Order type ("MARKET", "LIMIT")
        portfolio_value : float
            Current portfolio total value
        current_exposure : float
            Current gross exposure as fraction (0.0-1.0)
        leverage : int
            Leverage multiplier

        Returns
        -------
        dict[str, str | float | bool]
            Validation result with:
            - valid: bool
            - reason: str (if not valid)
            - adjusted_quantity: float (if size adjusted)

        Raises
        ------
        OrderValidationError
            If order fails validation
        """
        validation_result: dict[str, str | float | bool] = {"valid": True, "reason": ""}

        # Estimate order value first (needed for min/max checks)
        if order_type == "MARKET":
            # For market orders, fetch current price
            ticker = await self.client.aget_ticker(symbol)
            estimated_price = ticker.price
        else:
            if price is None:
                raise OrderValidationError("LIMIT order requires price")
            estimated_price = price

        # Calculate notional value (WITHOUT leverage for min/max checks)
        order_value = quantity * estimated_price

        # Check minimum order size (in USD notional value)
        if order_value < self.min_order_size:
            raise OrderValidationError(
                f"Order notional value ${order_value:.2f} below minimum ${self.min_order_size:.2f} "
                f"(quantity={quantity:.6f} * price=${estimated_price:.2f})"
            )

        # Check maximum order size (in USD notional value)
        if order_value > self.max_order_size:
            raise OrderValidationError(
                f"Order notional value ${order_value:.2f} exceeds maximum ${self.max_order_size:.2f} "
                f"(quantity={quantity:.6f} * price=${estimated_price:.2f})"
            )
        notional_value = order_value * leverage

        # Check position size limit (% of portfolio)
        position_pct = notional_value / portfolio_value if portfolio_value > 0 else 0
        if position_pct > self.max_position_pct:
            # Adjust quantity to max allowed
            max_notional = self.max_position_pct * portfolio_value
            max_quantity = max_notional / (estimated_price * leverage)
            logger.warning(
                "Position size exceeds limit, adjusting",
                original_quantity=quantity,
                adjusted_quantity=max_quantity,
                position_pct=position_pct,
                max_pct=self.max_position_pct,
            )
            quantity = max_quantity
            validation_result["adjusted_quantity"] = max_quantity
            validation_result["reason"] = "Quantity adjusted to meet position size limit"

        # Check account balance (for margin required)
        try:
            balance = await self.aget_account_balance()
            margin_required = order_value / leverage
            if margin_required > balance["available_balance"]:
                raise InsufficientBalanceError(
                    f"Insufficient balance for order. "
                    f"Required margin: {margin_required:.2f}, "
                    f"Available: {balance['available_balance']:.2f}"
                )
        except InsufficientBalanceError:
            raise
        except Exception as e:
            logger.warning("Could not verify balance", error=str(e))
            # Continue without balance check if API unavailable

        return validation_result

    async def aplace_order_with_limits(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        position_side: str = "BOTH",
        time_in_force: str = "GTC",
        portfolio_value: float = 100000.0,
        current_exposure: float = 0.0,
        leverage: int | None = None,
    ) -> BinanceFuturesOrder:
        """
        Place order with risk validation.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Order side ("BUY" or "SELL")
        order_type : str
            Order type ("MARKET", "LIMIT")
        quantity : float
            Order quantity
        price : float | None
            Order price (for LIMIT orders)
        position_side : str
            Position side ("BOTH", "LONG", "SHORT")
        time_in_force : str
            Time in force ("GTC", "IOC", "FOK")
        portfolio_value : float
            Current portfolio value for risk checks
        current_exposure : float
            Current gross exposure (0.0-1.0)
        leverage : int | None
            Leverage (1-125), uses default if None

        Returns
        -------
        BinanceFuturesOrder
            Order information from Binance

        Raises
        ------
        OrderValidationError
            If order validation fails
        """
        if leverage is None:
            leverage = self.default_leverage

        # Initialize symbol (set leverage)
        await self.ainitialize_symbol(symbol, leverage)

        # Validate order
        validation = await self.validate_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            portfolio_value=portfolio_value,
            current_exposure=current_exposure,
            leverage=leverage,
        )

        # Use adjusted quantity if provided
        final_quantity = float(validation.get("adjusted_quantity", quantity))

        symbol_filters = await self.aget_symbol_filters(symbol)
        final_quantity = self.apply_quantity_precision(final_quantity, symbol_filters)

        logger.info(
            "Placing order with risk limits",
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=final_quantity,
            price=price,
            leverage=leverage,
            validation=validation,
        )

        # Place order via Binance client
        try:
            order = await self.client.aplace_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=final_quantity,
                price=price,
                position_side=position_side,
                time_in_force=time_in_force,
            )

            logger.info(
                "Order placed successfully",
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                status=order.status,
            )

            return order

        except Exception as e:
            logger.exception(
                "Failed to place order",
                symbol=symbol,
                side=side,
                quantity=final_quantity,
                error=str(e),
            )
            raise

    async def aget_symbol_filters(self, symbol: str) -> dict[str, Any]:
        """
        Retrieve Binance symbol filters for precision enforcement.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")

        Returns
        -------
        dict[str, Any]
            Mapping of filter type to configuration payload from exchangeInfo
        """
        if symbol not in self.symbol_filters_cache:
            symbol_info = await self.client.aget_symbol_info(symbol)
            filters = {item.get("filterType"): item for item in symbol_info.get("filters", [])}
            self.symbol_filters_cache[symbol] = filters
        return self.symbol_filters_cache[symbol]

    def apply_quantity_precision(self, quantity: float, filters: dict[str, Any]) -> float:
        """
        Apply quantity precision constraints defined by Binance filters.

        Parameters
        ----------
        quantity : float
            Raw order quantity before precision handling
        filters : dict[str, Any]
            Symbol filters returned by :meth:`aget_symbol_filters`

        Returns
        -------
        float
            Exchange-compliant quantity rounded down to valid step size

        Raises
        ------
        OrderValidationError
            If the resulting quantity violates exchange constraints
        """
        lot_filter = filters.get("LOT_SIZE", {})
        step_size = lot_filter.get("stepSize")
        min_qty = float(lot_filter.get("minQty", 0.0))
        max_qty = float(lot_filter.get("maxQty", float("inf")))

        if step_size is None:
            return round(quantity, 3)

        try:
            decimal_quantity = Decimal(str(quantity))
            decimal_step = Decimal(step_size)
            adjusted = decimal_quantity.quantize(decimal_step, rounding=ROUND_DOWN)
        except (InvalidOperation, ValueError) as exc:
            raise OrderValidationError(f"Invalid quantity precision for step size {step_size}: {quantity}") from exc

        adjusted_quantity = float(adjusted)

        if adjusted_quantity < min_qty:
            raise OrderValidationError(
                f"Quantity {adjusted_quantity} below minimum {min_qty} after precision adjustment"
            )

        if adjusted_quantity > max_qty:
            raise OrderValidationError(
                f"Quantity {adjusted_quantity} exceeds maximum {max_qty} after precision adjustment"
            )

        return adjusted_quantity

    async def acancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel an order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        order_id : int
            Order ID to cancel

        Returns
        -------
        bool
            True if successfully canceled
        """
        try:
            result = await self.client.acancel_order(symbol, order_id)
            logger.info("Order canceled", symbol=symbol, order_id=order_id)
            return result
        except Exception as e:
            logger.exception(
                "Failed to cancel order",
                symbol=symbol,
                order_id=order_id,
                error=str(e),
            )
            raise

    async def aget_open_orders(self, symbol: str | None = None) -> list[BinanceFuturesOrder]:
        """
        Get open orders.

        Parameters
        ----------
        symbol : str | None
            Trading symbol (optional, all symbols if None)

        Returns
        -------
        list[BinanceFuturesOrder]
            List of open orders
        """
        try:
            return await self.client.aget_open_orders(symbol)
        except Exception as e:
            logger.exception("Failed to get open orders", symbol=symbol, error=str(e))
            raise

    async def aget_positions(self, symbol: str | None = None) -> list[dict[str, float | str]]:
        """
        Get current positions.

        Parameters
        ----------
        symbol : str | None
            Trading symbol (optional, all symbols if None)

        Returns
        -------
        list[dict[str, float | str]]
            List of positions with symbol, side, amount, PnL
        """
        try:
            positions = await self.client.aget_positions(symbol)
            return [
                {
                    "symbol": pos.symbol,
                    "position_side": pos.position_side,
                    "amount": pos.position_amount,
                    "entry_price": pos.entry_price,
                    "mark_price": pos.mark_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "leverage": pos.leverage,
                }
                for pos in positions
            ]
        except Exception as e:
            logger.exception("Failed to get positions", symbol=symbol, error=str(e))
            raise

    async def aclose_position(self, symbol: str, position_side: str = "BOTH") -> BinanceFuturesOrder:
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
        BinanceFuturesOrder
            Closing order information
        """
        try:
            return await self.client.aclose_position(symbol, position_side)
        except Exception as e:
            logger.exception(
                "Failed to close position",
                symbol=symbol,
                position_side=position_side,
                error=str(e),
            )
            raise

    async def aget_current_price(self, symbol: str) -> float:
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
            ticker = await self.client.aget_ticker(symbol)
            return ticker.price
        except Exception as e:
            logger.exception("Failed to get current price", symbol=symbol, error=str(e))
            raise
