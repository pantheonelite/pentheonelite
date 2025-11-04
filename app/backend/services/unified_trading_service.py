"""Unified trading service - routes to appropriate platform."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import structlog
from app.backend.client.aster import AsterClient
from app.backend.client.binance import BinanceClient
from app.backend.db.models.council import Council
from app.backend.db.models.order import Order
from app.backend.db.repositories.wallet_repository import WalletRepository
from app.backend.services.futures_position_service import FuturesPositionService
from app.backend.services.spot_holding_service import SpotHoldingService
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Type aliases for strict typing
OrderSide = Literal["BUY", "SELL"]
PositionSide = Literal["LONG", "SHORT", "BOTH"]
Platform = Literal["binance", "aster"]


class UnifiedTradingService:
    """
    Routes to appropriate platform based on council configuration.

    Council determines:
    - trading_mode: "paper" (Binance Testnet) | "real" (Aster)
    - trading_type: "futures" | "spot"
    """

    def __init__(self, session: AsyncSession, council: Council):
        """
        Initialize unified trading service.

        Parameters
        ----------
        session : AsyncSession
            Database session
        council : Council
            Council configuration
        """
        self.session = session
        self.council = council
        self.futures_service = FuturesPositionService(session)
        self.spot_service = SpotHoldingService(session)
        self.client: BinanceClient | AsterClient | None = None
        self.platform: Platform | None = None
        self._client_initialized = False

    async def _initialize_client(self) -> None:
        """
        Initialize client with wallet credentials if available.

        This method should be called before using the client.
        It will check if council has a wallet and use those credentials.
        Otherwise, it will fall back to environment variables.
        """
        if self._client_initialized:
            return

        # Try to get wallet from council
        wallet = None
        if self.council.wallet_id:
            wallet_repo = WalletRepository(self.session)
            wallet = await wallet_repo.get_by_id(self.council.wallet_id)
            if wallet and not wallet.is_active:
                logger.warning(
                    "Wallet found but is inactive, falling back to environment variables",
                    council_id=self.council.id,
                    wallet_id=wallet.id,
                )
                wallet = None

        # Initialize appropriate client based on trading mode
        if self.council.trading_mode == "paper":
            from app.backend.config.binance import BinanceConfig

            if wallet and wallet.exchange.lower() == "binance":
                # Use wallet credentials
                config = BinanceConfig(
                    api_key=wallet.api_key,
                    api_secret=wallet.secret_key,
                    testnet=True,
                )
                logger.info(
                    "Initializing Binance client with wallet credentials",
                    council_id=self.council.id,
                    wallet_id=wallet.id,
                )
            else:
                # Fall back to environment variables
                config = BinanceConfig(testnet=True)
                if wallet:
                    logger.warning(
                        "Wallet exchange does not match platform, using environment variables",
                        council_id=self.council.id,
                        wallet_exchange=wallet.exchange,
                        platform="binance",
                    )
                else:
                    logger.info(
                        "No wallet found, using environment variables for Binance",
                        council_id=self.council.id,
                    )

            self.client = BinanceClient(config)
            self.platform = "binance"
        else:  # real
            if wallet and wallet.exchange.lower() == "aster":
                # Use wallet credentials
                self.client = AsterClient(api_key=wallet.api_key, api_secret=wallet.secret_key)
                logger.info(
                    "Initializing Aster client with wallet credentials",
                    council_id=self.council.id,
                    wallet_id=wallet.id,
                )
            else:
                # Fall back to environment variables
                self.client = AsterClient()
                if wallet:
                    logger.warning(
                        "Wallet exchange does not match platform, using environment variables",
                        council_id=self.council.id,
                        wallet_exchange=wallet.exchange,
                        platform="aster",
                    )
                else:
                    logger.info(
                        "No wallet found, using environment variables for Aster",
                        council_id=self.council.id,
                    )

            self.platform = "aster"

        self._client_initialized = True
        logger.info(
            "Unified trading service initialized",
            council_id=self.council.id,
            trading_mode=self.council.trading_mode,
            trading_type=self.council.trading_type,
            platform=self.platform,
            has_wallet=wallet is not None,
        )

    async def aexecute_trade(
        self,
        symbol: str,
        side: OrderSide,
        position_size_usd: Decimal,
        confidence: Decimal,
        agent_reasoning: str | None = None,
        leverage: int | None = None,
        stop_loss: float | None = None,
        take_profit_short: float | None = None,
        take_profit_mid: float | None = None,
        take_profit_long: float | None = None,
    ) -> dict[str, bool | int | str]:
        """
        Execute trade - enforces open/close only policy.

        ⚠️ CRITICAL: This method will reject trades that attempt to update existing positions.
        Agents must close positions first before opening new ones.

        NOTE: position_size_usd is the DESIRED size in USD.
        Actual trade size will be adjusted based on available wallet balance.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : OrderSide
            Order side ("BUY" | "SELL")
        position_size_usd : Decimal
            Desired position size in USD (will be adjusted to wallet balance)
        confidence : Decimal
            Agent confidence (0.0-1.0)
        agent_reasoning : str | None
            Agent's reasoning
        leverage : int | None
            Leverage for futures (1-125)
        stop_loss : float | None
            Stop loss price from agent decision
        take_profit_short : float | None
            Short-term take profit price
        take_profit_mid : float | None
            Mid-term take profit price
        take_profit_long : float | None
            Long-term take profit price

        Returns
        -------
        dict[str, bool | int | str]
            Trade result with success/error information
        """
        await self._initialize_client()
        if self.council.trading_type == "futures":
            return await self._execute_futures_trade(
                symbol,
                side,
                position_size_usd,
                confidence,
                agent_reasoning,
                leverage,
                stop_loss,
                take_profit_short,
                take_profit_mid,
                take_profit_long,
            )
        return await self._execute_spot_trade(symbol, side, position_size_usd)

    async def _execute_futures_trade(
        self,
        symbol: str,
        side: OrderSide,
        position_size_usd: Decimal,
        confidence: Decimal,
        agent_reasoning: str | None,
        leverage: int | None,
        stop_loss: float | None,
        take_profit_short: float | None,
        take_profit_mid: float | None,
        take_profit_long: float | None,
    ) -> dict[str, bool | int | str]:
        """
        Execute futures trade with proper wallet balance checking.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : OrderSide
            Order side
        position_size_usd : Decimal
            Desired position size in USD
        confidence : Decimal
            Confidence
        agent_reasoning : str | None
            Reasoning
        leverage : int | None
            Leverage

        Returns
        -------
        dict
            Trade result
        """
        try:
            # Calculate leverage
            if leverage is None:
                leverage = self._calculate_leverage(confidence)

            # Get actual wallet balance
            account = await self.client.aget_account_info()
            available_balance = Decimal(str(account.available_balance))

            # Get current market price
            ticker = await self.client.aget_ticker(symbol)
            current_price = Decimal(str(ticker.price))

            # Calculate margin required for desired position
            # For futures: margin = (quantity * price) / leverage
            # We want: margin from position_size_usd
            desired_margin = position_size_usd / Decimal(leverage)

            # Adjust if wallet doesn't have enough
            if desired_margin > available_balance:
                logger.warning(
                    "Insufficient wallet balance, adjusting position",
                    desired_margin=float(desired_margin),
                    available=float(available_balance),
                    symbol=symbol,
                )
                # Use 95% of available (keep buffer)
                actual_margin = available_balance * Decimal("0.95")
            else:
                actual_margin = desired_margin

            # Calculate quantity in base asset
            # notional = quantity * price
            # margin = notional / leverage
            # => quantity = (margin * leverage) / price
            quantity_in_asset = (actual_margin * Decimal(leverage)) / current_price

            # Apply Binance precision (round down to step size)
            if self.platform == "binance":
                # For Binance, round to 3 decimal places (common for most pairs)
                # TODO: Fetch actual symbol filters for precise step size
                quantity_in_asset = quantity_in_asset.quantize(Decimal("0.001"))

            # Validate quantity before placing order
            # Check if quantity is zero or negative after quantization
            if quantity_in_asset <= 0:
                error_msg = (
                    f"Insufficient wallet balance to place order. "
                    f"Available: ${float(available_balance):.2f}, "
                    f"Required margin: ${float(desired_margin):.2f}, "
                    f"Calculated quantity: {float(quantity_in_asset):.6f}"
                )
                logger.warning(
                    "Cannot execute trade: quantity too small after quantization",
                    council_id=self.council.id,
                    symbol=symbol,
                    side=side,
                    available_balance=float(available_balance),
                    desired_margin=float(desired_margin),
                    quantity=float(quantity_in_asset),
                )
                raise ValueError(error_msg)

            # Check minimum order size (notional value = quantity * price)
            notional_value = quantity_in_asset * current_price
            min_order_size = Decimal("10.0")  # Binance minimum order size in USD
            if notional_value < min_order_size:
                error_msg = (
                    f"Order size too small. Notional value ${float(notional_value):.2f} "
                    f"below minimum ${float(min_order_size):.2f}. "
                    f"Available balance: ${float(available_balance):.2f}"
                )
                logger.warning(
                    "Cannot execute trade: notional value below minimum",
                    council_id=self.council.id,
                    symbol=symbol,
                    side=side,
                    notional_value=float(notional_value),
                    min_order_size=float(min_order_size),
                    available_balance=float(available_balance),
                )
                raise ValueError(error_msg)

            # Determine position sides
            if self.platform == "binance":
                api_position_side: PositionSide = "BOTH"
            else:
                api_position_side: PositionSide = "LONG" if side == "BUY" else "SHORT"

            normalized_side: PositionSide = "LONG" if side == "BUY" else "SHORT"

            logger.info(
                "Executing futures trade",
                symbol=symbol,
                side=side,
                desired_usd=float(position_size_usd),
                available_balance=float(available_balance),
                actual_margin=float(actual_margin),
                current_price=float(current_price),
                quantity_asset=float(quantity_in_asset),
                notional_value=float(notional_value),
                leverage=leverage,
                platform=self.platform,
            )

            # Place order with rounded quantity
            order = await self.client.aplace_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=float(quantity_in_asset),
                position_side=api_position_side,
            )

            # Get position from exchange
            positions = await self.client.aget_positions(symbol)
            exchange_position = next((p for p in positions if p.position_side == api_position_side), None)

            liquidation_price = None
            isolated_margin = None
            if exchange_position:
                if exchange_position.liquidation_price:
                    liquidation_price = Decimal(str(exchange_position.liquidation_price))
                if exchange_position.margin_type == "isolated":
                    filled_qty = Decimal(str(order.filled_quantity or order.quantity))
                    avg_px = Decimal(str(order.average_price or current_price))
                    isolated_margin = (filled_qty * avg_px) / Decimal(leverage)

            # Create position in database (updates are not allowed by policy)
            avg_price = (
                order.average_price
                if order.average_price
                else (exchange_position.entry_price if exchange_position else current_price)
            )

            # Enforce policy: reject if an open position already exists for this council/symbol/side
            existing = await self.futures_service.repo.find_by_symbol_and_side(
                council_id=self.council.id,
                symbol=symbol,
                position_side=api_position_side,
                status="OPEN",
            )
            if existing:
                raise ValueError(
                    "Position updates are not allowed per trading policy. Agents must close existing positions before opening new ones in the same direction. "
                    f"Council {self.council.id}, Symbol: {symbol}, Side: {api_position_side}"
                )

            position = await self.futures_service.aopen_position(
                council_id=self.council.id,
                symbol=symbol,
                position_side=api_position_side,
                position_amt=Decimal(str(order.filled_quantity or order.quantity)),
                entry_price=Decimal(str(avg_price)),
                leverage=leverage,
                margin_type="CROSSED",
                platform=self.platform,
                trading_mode=self.council.trading_mode,
                liquidation_price=liquidation_price,
                isolated_margin=isolated_margin,
                confidence=confidence,
                agent_reasoning=agent_reasoning,
                external_position_id=str(order.order_id),
            )
            was_created = True

            # Log order
            await self._log_order(order, position.id, None)

            # Place exit plan orders (SL/TP) if position was just created
            # Skip if updating existing position (exit plan already exists)
            if was_created:
                await self._execute_exit_plan(
                    symbol=symbol,
                    side=side,
                    quantity=float(quantity_in_asset),
                    position_id=position.id,
                    stop_loss=stop_loss,
                    take_profit_short=take_profit_short,
                    take_profit_mid=take_profit_mid,
                    take_profit_long=take_profit_long,
                )

            logger.info(
                "Futures trade executed successfully",
                position_id=position.id,
                order_id=order.order_id,
                symbol=symbol,
                side=normalized_side,
                was_created=was_created,
            )

            return {"success": True, "position_id": position.id, "order_id": order.order_id, "platform": self.platform}
        except Exception as e:
            logger.exception("Failed to execute futures trade", symbol=symbol, side=side, error=str(e))
            return {"success": False, "error": str(e)}

    async def _execute_spot_trade(
        self,
        symbol: str,
        side: OrderSide,
        position_size_usd: Decimal,
    ) -> dict[str, bool | int | str]:
        """
        Execute spot trade with wallet balance checking.

        Parameters
        ----------
        symbol : str
            Symbol
        side : OrderSide
            Side
        position_size_usd : Decimal
            Desired size in USD

        Returns
        -------
        dict
            Result
        """
        try:
            # Get wallet balance
            account = await self.client.aget_account_info()
            available_balance = Decimal(str(account.available_balance))

            # Get current price
            ticker = await self.client.aget_ticker(symbol)
            current_price = Decimal(str(ticker.price))

            # Adjust to available balance
            max_position_usd = min(position_size_usd, available_balance * Decimal("0.95"))

            # Convert to quantity
            quantity_in_asset = max_position_usd / current_price

            # Apply precision for Binance
            if self.platform == "binance":
                quantity_in_asset = quantity_in_asset.quantize(Decimal("0.001"))

            logger.info(
                "Executing spot trade",
                symbol=symbol,
                side=side,
                desired_usd=float(position_size_usd),
                available=float(available_balance),
                quantity=float(quantity_in_asset),
                platform=self.platform,
            )

            order = await self.client.aplace_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=float(quantity_in_asset),
            )

            # Parse symbol
            base_asset, quote_asset = self._parse_symbol(symbol)

            # Update holding
            quantity_delta = Decimal(str(order.filled_quantity or order.quantity))
            if side == "SELL":
                quantity_delta = -quantity_delta

            holding = await self.spot_service.aupdate_holding(
                council_id=self.council.id,
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                quantity_delta=quantity_delta,
                price=Decimal(str(order.average_price or current_price)),
                platform=self.platform,
                trading_mode=self.council.trading_mode,
            )

            await self._log_order(order, None, holding.id)

            logger.info(
                "Spot trade executed successfully",
                holding_id=holding.id,
                order_id=order.order_id,
                symbol=symbol,
                side=side,
            )

            return {"success": True, "holding_id": holding.id, "order_id": order.order_id, "platform": self.platform}
        except Exception as e:
            logger.exception("Failed to execute spot trade", symbol=symbol, side=side, error=str(e))
            return {"success": False, "error": str(e)}

    async def _execute_exit_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        position_id: int,
        stop_loss: float | None,
        take_profit_short: float | None,
        take_profit_mid: float | None,
        take_profit_long: float | None,
    ) -> None:
        """
        Execute exit plan by placing SL and TP orders.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : OrderSide
            Original order side
        quantity : float
            Position quantity
        position_id : int
            Database position ID
        stop_loss : float | None
            Stop loss price
        take_profit_short : float | None
            Short-term TP price
        take_profit_mid : float | None
            Mid-term TP price
        take_profit_long : float | None
            Long-term TP price
        """
        # Place stop loss order
        sl_order_id = None
        if stop_loss:
            sl_order_id = await self._place_stop_loss_order(symbol, side, quantity, stop_loss)

        # Place take profit orders
        tp_order_ids = await self._place_take_profit_orders(
            symbol,
            side,
            quantity,
            take_profit_short,
            take_profit_mid,
            take_profit_long,
        )

        # Update position with exit plan
        if sl_order_id or tp_order_ids:
            await self.futures_service.aupdate_exit_plan(
                position_id=position_id,
                stop_loss_price=Decimal(str(stop_loss)) if stop_loss else None,
                stop_loss_order_id=sl_order_id,
                take_profit_short=Decimal(str(take_profit_short)) if take_profit_short else None,
                take_profit_short_order_id=tp_order_ids.get("short"),
                take_profit_mid=Decimal(str(take_profit_mid)) if take_profit_mid else None,
                take_profit_mid_order_id=tp_order_ids.get("mid"),
                take_profit_long=Decimal(str(take_profit_long)) if take_profit_long else None,
                take_profit_long_order_id=tp_order_ids.get("long"),
            )

    async def _place_stop_loss_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_loss_price: float,
    ) -> str | None:
        """
        Place STOP_MARKET order for stop loss.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : OrderSide
            Original order side
        quantity : float
            Position quantity
        stop_loss_price : float
            Stop loss trigger price

        Returns
        -------
        str | None
            Order ID if successful, None otherwise
        """
        try:
            stop_order = await self.client.aplace_order(
                symbol=symbol,
                side="SELL" if side == "BUY" else "BUY",  # Opposite side to close
                order_type="STOP_MARKET",
                quantity=quantity,
                stop_price=stop_loss_price,
                reduce_only=True,
            )
            logger.info(
                "Stop-loss order placed",
                symbol=symbol,
                order_id=stop_order.order_id,
                price=stop_loss_price,
            )
            return str(stop_order.order_id)
        except Exception as e:
            logger.warning("Failed to place stop-loss order", symbol=symbol, error=str(e))
            return None

    async def _place_take_profit_orders(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        tp_short: float | None,
        tp_mid: float | None,
        tp_long: float | None,
    ) -> dict[str, str]:
        """
        Place TAKE_PROFIT_MARKET orders at multiple levels.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : OrderSide
            Original order side
        quantity : float
            Position quantity
        tp_short : float | None
            Short-term TP price
        tp_mid : float | None
            Mid-term TP price
        tp_long : float | None
            Long-term TP price

        Returns
        -------
        dict[str, str]
            Dictionary of TP level to order ID
        """
        tp_order_ids = {}
        tp_levels = [
            (tp_short, "short"),
            (tp_mid, "mid"),
            (tp_long, "long"),
        ]
        valid_levels = [(price, name) for price, name in tp_levels if price is not None]

        if not valid_levels:
            return {}

        # Split quantity across TP levels
        quantity_per_tp = quantity / len(valid_levels)

        for tp_price, tp_name in valid_levels:
            try:
                tp_order = await self.client.aplace_order(
                    symbol=symbol,
                    side="SELL" if side == "BUY" else "BUY",  # Opposite side to close
                    order_type="TAKE_PROFIT_MARKET",
                    quantity=quantity_per_tp,
                    stop_price=tp_price,
                    reduce_only=True,
                )
                tp_order_ids[tp_name] = str(tp_order.order_id)
                logger.info(
                    "Take-profit order placed",
                    symbol=symbol,
                    level=tp_name,
                    order_id=tp_order.order_id,
                    price=tp_price,
                    quantity=quantity_per_tp,
                )
            except Exception as e:
                logger.warning("Failed to place TP", symbol=symbol, level=tp_name, error=str(e))

        return tp_order_ids

    async def _log_order(
        self, exchange_order: object, futures_position_id: int | None, spot_holding_id: int | None
    ) -> None:
        """Log order in database."""
        order = Order(
            council_id=self.council.id,
            futures_position_id=futures_position_id,
            spot_holding_id=spot_holding_id,
            symbol=exchange_order.symbol,
            order_id=exchange_order.order_id,
            side=exchange_order.side,
            type=exchange_order.type,
            position_side=getattr(exchange_order, "position_side", None),
            orig_qty=Decimal(str(exchange_order.quantity)),
            executed_qty=Decimal(str(exchange_order.filled_quantity or exchange_order.quantity)),
            avg_price=Decimal(str(exchange_order.average_price)) if exchange_order.average_price else None,
            status=exchange_order.status,
            platform=self.platform,
            trading_mode=self.council.trading_mode,
            trading_type=self.council.trading_type,
            transaction_time=datetime.now(UTC),
            update_time=datetime.now(UTC),
        )

        self.session.add(order)
        await self.session.commit()

    def _calculate_leverage(self, confidence: Decimal) -> int:
        """Calculate leverage based on confidence."""
        if confidence < Decimal("0.6"):
            return max(1, int(confidence * 10))
        if confidence < Decimal("0.7"):
            return max(5, int(confidence * 15))
        if confidence < Decimal("0.8"):
            return max(10, int(confidence * 20))
        return min(20, max(15, int(confidence * 25)))

    async def aclose_existing_position(
        self,
        symbol: str,
        position_side: str | None = None,
    ) -> dict[str, bool | int | str]:
        """
        Close existing position for symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol
        position_side : str | None
            Position side ("BOTH", "LONG", "SHORT"). If None, uses default for platform.

        Returns
        -------
        dict[str, bool | int | str]
            Result with success, position_id, order_id
        """
        try:
            # Determine position side based on platform
            if position_side is None:
                position_side = "BOTH" if self.platform == "binance" else None

            # Find existing open position
            if position_side:
                existing = await self.futures_service.repo.find_by_symbol_and_side(
                    council_id=self.council.id,
                    symbol=symbol,
                    position_side=position_side,
                    status="OPEN",
                )
            else:
                # For Aster or when position_side not specified, find any open position
                positions = await self.futures_service.repo.find_open_positions(
                    council_id=self.council.id,
                    symbol=symbol,
                )
                existing = positions[0] if positions else None

            if not existing:
                logger.warning("No open position found to close", symbol=symbol)
                return {"success": False, "error": "No open position found"}

            # Place closing order on exchange
            close_order = await self.client.aclose_position(symbol, existing.position_side)

            # Get current price for PnL calculation
            ticker = await self.client.aget_ticker(symbol)
            exit_price = Decimal(str(ticker.price))

            # Close position in database
            closed_position = await self.futures_service.aclose_position(
                position_id=existing.id,
                exit_price=exit_price,
                fees=Decimal(0),  # TODO: Extract from order if available
                funding_fees=Decimal(0),  # TODO: Calculate funding fees
            )

            logger.info(
                "Position closed successfully",
                position_id=closed_position.id,
                symbol=symbol,
                realized_pnl=float(closed_position.realized_pnl or 0),
            )

            return {
                "success": True,
                "position_id": closed_position.id,
                "order_id": close_order.order_id,
            }
        except Exception as e:
            logger.exception("Failed to close position", symbol=symbol, error=str(e))
            return {"success": False, "error": str(e)}

    def _parse_symbol(self, symbol: str) -> tuple[str, str]:
        """Parse symbol into base and quote assets."""
        quote_assets = ["USDT", "BUSD", "USD", "BTC", "ETH"]
        for quote in quote_assets:
            if symbol.endswith(quote):
                base = symbol[: -len(quote)]
                return (base, quote)
        return (symbol[:-4], symbol[-4:])
