"""Binance Testnet Futures REST API client."""

import asyncio
import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp
import structlog
from app.backend.client.binance.exceptions import (
    BinanceAPIException,
    BinanceRateLimitError,
    parse_binance_error,
)
from app.backend.client.binance.rate_limiter import OrderRateLimiter, RateLimiter
from app.backend.config.binance import BinanceConfig, get_binance_settings
from pydantic import BaseModel, Field

binance_settings = get_binance_settings()

logger = structlog.get_logger(__name__)


class BinanceTicker(BaseModel):
    """Binance ticker data model."""

    symbol: str
    price: float
    volume: float
    change_24h: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    exchange: str = "binance_testnet"


class BinanceOHLCV(BaseModel):
    """Binance OHLCV data model."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str = "binance_testnet"


class BinanceFuturesAccount(BaseModel):
    """Binance Futures account information."""

    total_balance: float
    available_balance: float
    used_balance: float
    unrealized_pnl: float
    assets: list[dict[str, Any]] = Field(default_factory=list)
    positions: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime


class BinanceFuturesOrder(BaseModel):
    """Binance Futures order model."""

    order_id: int
    symbol: str
    side: str  # "BUY" or "SELL"
    position_side: str  # "BOTH", "LONG", "SHORT"
    type: str  # "MARKET", "LIMIT", "STOP_MARKET", etc.
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    status: str
    timestamp: datetime
    filled_quantity: float = 0.0
    average_price: float | None = None
    reduce_only: bool = False


class BinanceFuturesPosition(BaseModel):
    """Binance Futures position model."""

    symbol: str
    position_side: str  # "BOTH", "LONG", "SHORT"
    position_amount: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: int
    margin_type: str  # "cross" or "isolated"
    liquidation_price: float | None = None
    timestamp: datetime


class BinanceClient:
    """Binance Testnet Futures REST API client."""

    def __init__(
        self,
        config: BinanceConfig | None = None,
        *,
        enable_rate_limiting: bool = True,
    ):
        """
        Initialize Binance Futures client.

        Parameters
        ----------
        config : BinanceConfig | None
            Binance client configuration. If None, loads from settings.
        enable_rate_limiting : bool
            Enable client-side rate limiting (default: True)
        """
        if config is None:
            config = binance_settings

        self.config = config
        self.base_url = config.get_base_url()
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        self.timeout = config.timeout
        self.recv_window = config.recv_window

        # Rate limiting
        self.enable_rate_limiting = enable_rate_limiting
        if enable_rate_limiting:
            self.rate_limiter = RateLimiter(requests_per_minute=1200)
            self.order_rate_limiter = OrderRateLimiter()
        else:
            self.rate_limiter = None
            self.order_rate_limiter = None

        self._symbol_info_cache: dict[str, dict[str, Any]] = {}

        logger.info(
            "Binance Futures client initialized",
            base_url=self.base_url,
            testnet=config.testnet,
            rate_limiting=enable_rate_limiting,
        )

    def _generate_signature(self, params: dict[str, Any]) -> str:
        """
        Generate HMAC SHA256 signature for authenticated requests.

        Parameters
        ----------
        params : dict[str, Any]
            Request parameters

        Returns
        -------
        str
            HMAC signature
        """
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with API key."""
        return {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        signed: bool = False,
        weight: int = 1,
        max_retries: int = 3,
    ) -> dict[str, Any] | list[Any]:
        """
        Make HTTP request to Binance API with retry logic.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, DELETE, PUT)
        endpoint : str
            API endpoint
        params : dict[str, Any] | None
            Request parameters
        signed : bool
            Whether request requires signature
        weight : int
            Request weight for rate limiting
        max_retries : int
            Maximum retry attempts for failed requests

        Returns
        -------
        dict[str, Any] | list[Any]
            Response data

        Raises
        ------
        BinanceAPIException
            On API errors
        """
        if params is None:
            params = {}

        url = f"{self.base_url}{endpoint}"

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window
            signature = self._generate_signature(params)
            params["signature"] = signature

        headers = self._get_headers() if signed else {}

        # Apply rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire(weight)

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    request_kwargs = {
                        "url": url,
                        "params": params,
                        "headers": headers,
                        "timeout": aiohttp.ClientTimeout(total=self.timeout),
                    }

                    if method == "GET":
                        async with session.get(**request_kwargs) as response:
                            return await self._handle_response(response)
                    if method == "POST":
                        async with session.post(**request_kwargs) as response:
                            return await self._handle_response(response)
                    if method == "DELETE":
                        async with session.delete(**request_kwargs) as response:
                            return await self._handle_response(response)
                    if method == "PUT":
                        async with session.put(**request_kwargs) as response:
                            return await self._handle_response(response)
                    raise ValueError(f"Unsupported HTTP method: {method}")

            except BinanceRateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = e.retry_after * (2**attempt)
                    logger.warning(
                        "Rate limit hit, retrying",
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        endpoint=endpoint,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise

            except (TimeoutError, aiohttp.ClientError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "Request failed, retrying",
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        error=str(e),
                        endpoint=endpoint,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                logger.exception(
                    "Binance API request failed after retries",
                    method=method,
                    endpoint=endpoint,
                    error=str(e),
                )
                raise BinanceAPIException(f"Request failed: {e}") from e

        return None

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any] | list[Any]:
        """
        Handle API response and errors.

        Parameters
        ----------
        response : aiohttp.ClientResponse
            HTTP response

        Returns
        -------
        dict[str, Any] | list[Any]
            Parsed response data

        Raises
        ------
        BinanceAPIException
            On API errors
        """
        try:
            data = await response.json()
        except Exception:
            data = {}

        if response.status >= 400:
            # Parse error
            error = parse_binance_error(response.status, data)
            logger.error(
                "Binance API error",
                status=response.status,
                code=error.code,
                message=str(error),
            )
            raise error

        return data

    async def aget_ticker(self, symbol: str) -> BinanceTicker:
        """
        Get ticker data for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")

        Returns
        -------
        BinanceTicker
            Ticker data
        """
        try:
            data = await self._request("GET", "/fapi/v1/ticker/24hr", {"symbol": symbol})
            return self._parse_ticker_data(data, symbol)
        except Exception as e:
            logger.exception("Failed to get ticker", symbol=symbol, error=str(e))
            raise

    async def aget_symbol_info(self, symbol: str) -> dict[str, Any]:
        """
        Get exchange metadata for a specific symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")

        Returns
        -------
        dict[str, Any]
            Exchange information for the symbol including filters

        Raises
        ------
        BinanceAPIException
            If the exchange info request fails or the symbol is not found
        """
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]

        try:
            data = await self._request("GET", "/fapi/v1/exchangeInfo", {"symbol": symbol})
        except Exception as e:
            logger.exception("Failed to get symbol info", symbol=symbol, error=str(e))
            raise

        symbols = data.get("symbols", []) if isinstance(data, dict) else []
        symbol_info = next((item for item in symbols if item.get("symbol") == symbol), None)

        if symbol_info is None:
            raise BinanceAPIException(f"Symbol info not found for {symbol}")

        self._symbol_info_cache[symbol] = symbol_info
        return symbol_info

    async def aget_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[BinanceOHLCV]:
        """
        Get historical kline/candlestick data.

        Parameters
        ----------
        symbol : str
            Trading symbol
        interval : str
            Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        limit : int
            Number of klines to retrieve (max 1500)

        Returns
        -------
        list[BinanceOHLCV]
            List of OHLCV data
        """
        try:
            data = await self._request(
                "GET", "/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit}
            )
            return self._parse_klines_data(data, symbol)
        except Exception as e:
            logger.exception("Failed to get klines", symbol=symbol, error=str(e))
            raise

    async def aget_account_info(self) -> BinanceFuturesAccount:
        """
        Get Futures account information.

        Returns
        -------
        BinanceFuturesAccount
            Account information including balance and positions
        """
        try:
            data = await self._request("GET", "/fapi/v2/account", signed=True)
            return self._parse_account_data(data)
        except Exception as e:
            logger.exception("Failed to get account info", error=str(e))
            raise

    async def aget_positions(self, symbol: str | None = None) -> list[BinanceFuturesPosition]:
        """
        Get current Futures positions.

        Parameters
        ----------
        symbol : str | None
            Trading symbol (optional, all symbols if None)

        Returns
        -------
        list[BinanceFuturesPosition]
            List of positions
        """
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol

            data = await self._request("GET", "/fapi/v2/positionRisk", params, signed=True)
            return [self._parse_position_data(pos) for pos in data if float(pos.get("positionAmt", 0)) != 0]
        except Exception as e:
            logger.exception("Failed to get positions", symbol=symbol, error=str(e))
            raise

    async def aset_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        """
        Set leverage for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol
        leverage : int
            Leverage (1-125)

        Returns
        -------
        dict[str, Any]
            Response data
        """
        try:
            data = await self._request(
                "POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage}, signed=True
            )
            logger.info("Leverage set", symbol=symbol, leverage=leverage)
            return data
        except Exception as e:
            logger.exception("Failed to set leverage", symbol=symbol, leverage=leverage, error=str(e))
            raise

    async def aset_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        """
        Set margin type for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol
        margin_type : str
            Margin type ("ISOLATED" or "CROSSED")

        Returns
        -------
        dict[str, Any]
            Response data
        """
        try:
            data = await self._request(
                "POST",
                "/fapi/v1/marginType",
                {"symbol": symbol, "marginType": margin_type},
                signed=True,
            )
            logger.info("Margin type set", symbol=symbol, margin_type=margin_type)
            return data
        except Exception as e:
            # Margin type might already be set, log but don't fail
            logger.warning(
                "Failed to set margin type (may already be set)",
                symbol=symbol,
                margin_type=margin_type,
                error=str(e),
            )
            return {}

    async def aplace_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        position_side: str = "BOTH",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        stop_price: float | None = None,
        self_trade_prevention_mode: str | None = None,
        price_match: str | None = None,
    ) -> BinanceFuturesOrder:
        """
        Place a Futures order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Order side ("BUY" or "SELL")
        order_type : str
            Order type ("MARKET", "LIMIT", "STOP_MARKET", etc.)
        quantity : float
            Order quantity
        price : float | None
            Order price (required for LIMIT orders)
        position_side : str
            Position side ("BOTH", "LONG", "SHORT")
        time_in_force : str
            Time in force ("GTC", "IOC", "FOK")
        reduce_only : bool
            Reduce only flag
        stop_price : float | None
            Stop price (for STOP orders)
        self_trade_prevention_mode : str | None
            Self-trade prevention mode: NONE, EXPIRE_TAKER, EXPIRE_MAKER, EXPIRE_BOTH
        price_match : str | None
            Price match mode: NONE, OPPONENT, OPPONENT_5, OPPONENT_10, OPPONENT_20, QUEUE, QUEUE_5, QUEUE_10, QUEUE_20

        Returns
        -------
        BinanceFuturesOrder
            Order information
        """
        # Apply order rate limiting
        if self.order_rate_limiter:
            await self.order_rate_limiter.acquire_order()

        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "positionSide": position_side,
            }

            if order_type == "LIMIT":
                if price is None:
                    raise ValueError("Price required for LIMIT orders")
                params["price"] = price
                params["timeInForce"] = time_in_force

            if reduce_only:
                params["reduceOnly"] = "true"

            if stop_price is not None:
                params["stopPrice"] = stop_price

            # Self-Trade Prevention (STP)
            if self_trade_prevention_mode is not None:
                params["selfTradePreventionMode"] = self_trade_prevention_mode

            # Price Match for better execution
            if price_match is not None:
                params["priceMatch"] = price_match

            data = await self._request("POST", "/fapi/v1/order", params, signed=True, weight=1)
            logger.info(
                "Order placed",
                order_id=data.get("orderId"),
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
            )
            return self._parse_order_data(data)

        except Exception as e:
            logger.exception("Failed to place order", symbol=symbol, side=side, error=str(e))
            raise

    async def amodify_order(
        self,
        symbol: str,
        order_id: int,
        quantity: float | None = None,
        price: float | None = None,
    ) -> BinanceFuturesOrder:
        """
        Modify an existing Futures order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        order_id : int
            Order ID to modify
        quantity : float | None
            New order quantity (optional)
        price : float | None
            New order price (optional)

        Returns
        -------
        BinanceFuturesOrder
            Modified order information
        """
        try:
            params: dict[str, Any] = {
                "symbol": symbol,
                "orderId": order_id,
            }

            if quantity is not None:
                params["quantity"] = quantity

            if price is not None:
                params["price"] = price

            data = await self._request("PUT", "/fapi/v1/order", params, signed=True, weight=1)
            logger.info(
                "Order modified",
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                price=price,
            )
            return self._parse_order_data(data)
        except Exception as e:
            logger.exception("Failed to modify order", symbol=symbol, order_id=order_id, error=str(e))
            raise

    async def acancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel a Futures order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        order_id : int
            Order ID to cancel

        Returns
        -------
        bool
            True if successful
        """
        try:
            await self._request(
                "DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True, weight=1
            )
            logger.info("Order canceled", symbol=symbol, order_id=order_id)
            return True
        except Exception as e:
            logger.exception("Failed to cancel order", symbol=symbol, order_id=order_id, error=str(e))
            raise

    async def acancel_all_orders(self, symbol: str) -> int:
        """
        Cancel all open orders for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        int
            Number of orders canceled
        """
        try:
            data = await self._request("DELETE", "/fapi/v1/allOpenOrders", {"symbol": symbol}, signed=True, weight=1)
            count = data.get("code", 0) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0
            logger.info("All orders canceled", symbol=symbol, count=count)
            return count
        except Exception as e:
            logger.exception("Failed to cancel all orders", symbol=symbol, error=str(e))
            raise

    async def aplace_batch_orders(
        self,
        orders: list[dict[str, Any]],
    ) -> list[BinanceFuturesOrder]:
        """
        Place multiple orders in a single request.

        Parameters
        ----------
        orders : list[dict[str, Any]]
            List of order parameters (max 5 orders per request)

        Returns
        -------
        list[BinanceFuturesOrder]
            List of placed orders

        Examples
        --------
        >>> orders = [
        ...     {
        ...         "symbol": "BTCUSDT",
        ...         "side": "BUY",
        ...         "type": "LIMIT",
        ...         "quantity": 0.001,
        ...         "price": 50000.0,
        ...         "timeInForce": "GTC"
        ...     },
        ...     {
        ...         "symbol": "ETHUSDT",
        ...         "side": "BUY",
        ...         "type": "MARKET",
        ...         "quantity": 0.01,
        ...     }
        ... ]
        >>> placed_orders = await client.aplace_batch_orders(orders)
        """
        # Apply order rate limiting for batch
        if self.order_rate_limiter:
            for _ in orders:
                await self.order_rate_limiter.acquire_order()

        try:
            # Format batch orders payload
            params = {
                "batchOrders": str(orders),  # JSON string of order list
            }

            data = await self._request("POST", "/fapi/v1/batchOrders", params, signed=True, weight=5)
            logger.info("Batch orders placed", count=len(orders))

            # Parse results
            results = []
            if isinstance(data, list):
                for order_data in data:
                    if isinstance(order_data, dict) and "orderId" in order_data:
                        results.append(self._parse_order_data(order_data))

            return results
        except Exception as e:
            logger.exception("Failed to place batch orders", count=len(orders), error=str(e))
            raise

    async def aget_open_orders(self, symbol: str | None = None) -> list[BinanceFuturesOrder]:
        """
        Get open Futures orders.

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
            params = {}
            if symbol:
                params["symbol"] = symbol

            data = await self._request("GET", "/fapi/v1/openOrders", params, signed=True)
            return [self._parse_order_data(order) for order in data]
        except Exception as e:
            logger.exception("Failed to get open orders", symbol=symbol, error=str(e))
            raise

    async def aget_all_orders(
        self,
        symbol: str | None = None,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[BinanceFuturesOrder]:
        """
        Get all Futures orders (including closed orders).

        Parameters
        ----------
        symbol : str | None
            Trading symbol (required for allOrders endpoint)
        order_id : int | None
            Order ID (optional)
        start_time : int | None
            Start time in milliseconds (optional)
        end_time : int | None
            End time in milliseconds (optional)
        limit : int
            Maximum number of orders to return (default 500, max 1000)

        Returns
        -------
        list[BinanceFuturesOrder]
            List of all orders (open and closed)
        """
        try:
            if not symbol:
                # If no symbol, get orders for all symbols by making multiple requests
                # For now, return empty list if symbol not provided
                logger.warning("Symbol is required for aget_all_orders, returning empty list")
                return []

            params: dict[str, Any] = {"symbol": symbol, "limit": min(limit, 1000)}
            if order_id:
                params["orderId"] = order_id
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time

            data = await self._request("GET", "/fapi/v1/allOrders", params, signed=True)
            return [self._parse_order_data(order) for order in data]
        except Exception as e:
            logger.exception("Failed to get all orders", symbol=symbol, error=str(e))
            raise

    async def aclose_position(self, symbol: str, position_side: str = "BOTH") -> BinanceFuturesOrder | None:
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
        BinanceFuturesOrder | None
            Closing order information, or None if no open position found
        """
        try:
            positions = await self.aget_positions(symbol)

            if position_side == "BOTH":
                # Close both LONG and SHORT positions
                # Binance positions can have position_side="BOTH" (one-way mode) or explicit "LONG"/"SHORT"
                # For "BOTH" positions, direction is determined by sign of position_amount
                long_positions: list[BinanceFuturesPosition] = []
                short_positions: list[BinanceFuturesPosition] = []

                for pos in positions:
                    if pos.position_side == "LONG":
                        long_positions.append(pos)
                    elif pos.position_side == "SHORT":
                        short_positions.append(pos)
                    elif pos.position_side == "BOTH":
                        # One-way mode: determine direction from position_amount sign
                        if pos.position_amount > 0:
                            long_positions.append(pos)
                        elif pos.position_amount < 0:
                            short_positions.append(pos)

                if not long_positions and not short_positions:
                    return None

                order_result: BinanceFuturesOrder | None = None

                # Close all LONG positions
                for long_pos in long_positions:
                    close_side_long = "SELL" if long_pos.position_amount > 0 else "BUY"
                    quantity_long = abs(long_pos.position_amount)
                    order_result = await self.aplace_order(
                        symbol=symbol,
                        side=close_side_long,
                        order_type="MARKET",
                        quantity=quantity_long,
                        position_side=long_pos.position_side,  # Use original position_side
                        reduce_only=True,
                    )

                # Close all SHORT positions
                for short_pos in short_positions:
                    close_side_short = "SELL" if short_pos.position_amount > 0 else "BUY"
                    quantity_short = abs(short_pos.position_amount)
                    order_result = await self.aplace_order(
                        symbol=symbol,
                        side=close_side_short,
                        order_type="MARKET",
                        quantity=quantity_short,
                        position_side=short_pos.position_side,  # Use original position_side
                        reduce_only=True,
                    )

                # Return the last order executed
                return order_result
            else:
                # Close specific position side (LONG or SHORT)
                # Also handle positions with position_side="BOTH" where direction is determined by sign
                position = None
                for pos in positions:
                    if pos.position_side == position_side:
                        position = pos
                        break
                    elif pos.position_side == "BOTH":
                        # One-way mode: check if position direction matches requested side
                        if position_side == "LONG" and pos.position_amount > 0:
                            position = pos
                            break
                        elif position_side == "SHORT" and pos.position_amount < 0:
                            position = pos
                            break

                if not position:
                    return None

                # Determine closing side (opposite of position)
                close_side = "SELL" if position.position_amount > 0 else "BUY"
                quantity = abs(position.position_amount)

                return await self.aplace_order(
                    symbol=symbol,
                    side=close_side,
                    order_type="MARKET",
                    quantity=quantity,
                    position_side=position.position_side,  # Use original position_side
                    reduce_only=True,
                )
        except Exception as e:
            logger.exception("Failed to close position", symbol=symbol, error=str(e))
            raise

    def _parse_ticker_data(self, data: dict[str, Any], symbol: str) -> BinanceTicker:
        """Parse ticker data from Binance API response."""
        return BinanceTicker(
            symbol=symbol,
            price=float(data.get("lastPrice", 0)),
            volume=float(data.get("volume", 0)),
            change_24h=float(data.get("priceChange", 0)),
            change_percent_24h=float(data.get("priceChangePercent", 0)),
            high_24h=float(data.get("highPrice", 0)),
            low_24h=float(data.get("lowPrice", 0)),
            timestamp=datetime.now(UTC),
            exchange="binance_testnet",
        )

    def _parse_klines_data(self, data: list[list[Any]], symbol: str) -> list[BinanceOHLCV]:
        """Parse klines data from Binance API response."""
        return [
            BinanceOHLCV(
                timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=UTC),
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[5]),
                symbol=symbol,
                exchange="binance_testnet",
            )
            for kline in data
        ]

    def _parse_account_data(self, data: dict[str, Any]) -> BinanceFuturesAccount:
        """Parse account data from Binance API response."""
        assets = data.get("assets", [])
        total_balance = sum(float(asset.get("walletBalance", 0)) for asset in assets)
        available_balance = sum(float(asset.get("availableBalance", 0)) for asset in assets)

        return BinanceFuturesAccount(
            total_balance=total_balance,
            available_balance=available_balance,
            used_balance=total_balance - available_balance,
            unrealized_pnl=float(data.get("totalUnrealizedProfit", 0)),
            assets=assets,
            positions=data.get("positions", []),
            timestamp=datetime.now(UTC),
        )

    def _parse_position_data(self, data: dict[str, Any]) -> BinanceFuturesPosition:
        """Parse position data from Binance API response."""
        return BinanceFuturesPosition(
            symbol=data.get("symbol", ""),
            position_side=data.get("positionSide", "BOTH"),
            position_amount=float(data.get("positionAmt", 0)),
            entry_price=float(data.get("entryPrice", 0)),
            mark_price=float(data.get("markPrice", 0)),
            unrealized_pnl=float(data.get("unRealizedProfit", 0)),
            leverage=int(data.get("leverage", 1)),
            margin_type=data.get("marginType", "cross").lower(),
            liquidation_price=float(data.get("liquidationPrice", 0)) if data.get("liquidationPrice") else None,
            timestamp=datetime.now(UTC),
        )

    def _parse_order_data(self, data: dict[str, Any]) -> BinanceFuturesOrder:
        """Parse order data from Binance API response."""
        return BinanceFuturesOrder(
            order_id=int(data.get("orderId", 0)),
            symbol=data.get("symbol", ""),
            side=data.get("side", ""),
            position_side=data.get("positionSide", "BOTH"),
            type=data.get("type", ""),
            quantity=float(data.get("origQty", 0)),
            price=float(data.get("price", 0)) if data.get("price") else None,
            stop_price=float(data.get("stopPrice", 0)) if data.get("stopPrice") else None,
            status=data.get("status", ""),
            timestamp=datetime.fromtimestamp(int(data.get("updateTime", 0)) / 1000, tz=UTC),
            filled_quantity=float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0)) if data.get("avgPrice") else None,
            reduce_only=data.get("reduceOnly", False),
        )
