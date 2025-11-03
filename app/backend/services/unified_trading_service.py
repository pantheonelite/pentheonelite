"""Unified trading service - routes to appropriate platform."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import structlog
from app.backend.client.aster import AsterClient
from app.backend.client.binance import BinanceClient
from app.backend.config.binance import BinanceConfig
from app.backend.db.models.council import Council
from app.backend.db.models.order import Order
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

        # Initialize appropriate client based on trading mode
        if council.trading_mode == "paper":
            config = BinanceConfig(testnet=True)
            self.client = BinanceClient(config)
            self.platform = "binance"
        else:  # real
            self.client = AsterClient()
            self.platform = "aster"

        logger.info(
            "Unified trading service initialized",
            council_id=council.id,
            trading_mode=council.trading_mode,
            trading_type=council.trading_type,
            platform=self.platform,
        )

    async def aexecute_trade(
        self,
        symbol: str,
        side: OrderSide,
        position_size_usd: Decimal,
        confidence: Decimal,
        agent_reasoning: str | None = None,
        leverage: int | None = None,
    ) -> dict[str, bool | int | str]:
        """
        Execute trade based on council type.

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

        Returns
        -------
        dict[str, bool | int | str]
            Trade result
        """
        if self.council.trading_type == "futures":
            return await self._execute_futures_trade(
                symbol, side, position_size_usd, confidence, agent_reasoning, leverage
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

            # Create position in database
            avg_price = (
                order.average_price
                if order.average_price
                else (exchange_position.entry_price if exchange_position else current_price)
            )

            position = await self.futures_service.aopen_position(
                council_id=self.council.id,
                symbol=symbol,
                position_side=normalized_side,
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

            # Log order
            await self._log_order(order, position.id, None)

            logger.info(
                "Futures trade executed successfully",
                position_id=position.id,
                order_id=order.order_id,
                symbol=symbol,
                side=normalized_side,
            )
        except Exception as e:
            logger.exception("Failed to execute futures trade", symbol=symbol, side=side, error=str(e))
            return {"success": False, "error": str(e)}
        else:
            return {"success": True, "position_id": position.id, "order_id": order.order_id, "platform": self.platform}

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
        except Exception as e:
            logger.exception("Failed to execute spot trade", symbol=symbol, side=side, error=str(e))
            return {"success": False, "error": str(e)}
        else:
            return {"success": True, "holding_id": holding.id, "order_id": order.order_id, "platform": self.platform}

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

    def _parse_symbol(self, symbol: str) -> tuple[str, str]:
        """Parse symbol into base and quote assets."""
        quote_assets = ["USDT", "BUSD", "USD", "BTC", "ETH"]
        for quote in quote_assets:
            if symbol.endswith(quote):
                base = symbol[: -len(quote)]
                return (base, quote)
        return (symbol[:-4], symbol[-4:])
