"""Aster Futures API client based on official API documentation.

Reference: https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation
Base URL: https://fapi.asterdex.com
"""

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import aiohttp
import structlog
from app.backend.config.aster import get_aster_settings
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)
aster_settings = get_aster_settings()


class AsterFuturesError(Exception):
    """Base exception for Aster Futures API errors."""

    def __init__(self, code: int, msg: str, *args: object) -> None:
        super().__init__(*args)
        self.code = code
        self.msg = msg


class RateLimitError(AsterFuturesError):
    """Raised when API rate limit is exceeded."""


class AuthenticationError(AsterFuturesError):
    """Raised when API authentication fails."""


class PositionMode(BaseModel):
    """Position mode information."""

    dual_side_position: bool = Field(description="True for hedge mode, False for one-way mode")


class MultiAssetsMode(BaseModel):
    """Multi-assets mode information."""

    multi_assets_margin: bool = Field(description="True for multi-asset mode, False for single-asset mode")


class FuturesAccountBalance(BaseModel):
    """Futures account balance."""

    account_alias: str
    asset: str
    balance: float
    cross_wallet_balance: float
    cross_un_pnl: float
    available_balance: float
    max_withdraw_amount: float
    margin_available: bool
    update_time: int


class AccountInformation(BaseModel):
    """Account information V4."""

    asset: str
    wallet_balance: float
    unrealized_profit: float
    margin_balance: float
    maint_margin: float
    initial_margin: float
    position_initial_margin: float
    open_order_initial_margin: float
    max_withdraw_amount: float
    cross_wallet_balance: float
    cross_un_pnl: float
    available_balance: float
    margin_available: bool
    update_time: int


class Position(BaseModel):
    """Position information V2."""

    symbol: str
    initial_margin: float
    maint_margin: float
    unrealized_profit: float
    position_initial_margin: float
    open_order_initial_margin: float
    leverage: int
    isolated_margin: float
    entry_price: float
    max_notional: float
    bid_notional: float
    ask_notional: float
    position_side: str = Field(description="BOTH, LONG, or SHORT")
    position_amt: float
    update_time: int


class Order(BaseModel):
    """Order information."""

    order_id: int
    symbol: str
    status: str
    client_order_id: str
    price: float
    avg_price: float = Field(default=0.0)
    orig_qty: float
    executed_qty: float
    cum_qty: float = Field(default=0.0)
    cum_quote: float = Field(default=0.0)
    time_in_force: str
    type: str
    reduce_only: bool = Field(default=False)
    close_position: bool = Field(default=False)
    side: str
    position_side: str = Field(default="BOTH")
    stop_price: float | None = None
    working_type: str | None = None
    price_protect: bool = Field(default=False)
    orig_type: str
    time: int
    update_time: int


class Trade(BaseModel):
    """Trade information."""

    buyer: bool
    commission: float
    commission_asset: str
    id: int
    maker: bool
    order_id: int
    price: float
    qty: float
    quote_qty: float
    realized_pnl: float
    side: str
    position_side: str
    symbol: str
    time: int


class Income(BaseModel):
    """Income history entry."""

    symbol: str | None = None
    income_type: str
    income: float
    asset: str
    info: str
    time: int
    tran_id: int
    trade_id: str | None = None


class AsterFuturesClient:
    """Aster Futures API client implementing the official API specification.

    Reference: https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation
    Base URL: https://fapi.asterdex.com

    Can be used as an async context manager to ensure proper resource cleanup:

    Examples
    --------
    >>> async with AsterFuturesClient() as client:
    ...     ticker = await client.get_24hr_ticker("BTCUSDT")
    >>> # Session is automatically closed on exit
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = "https://fapi.asterdex.com",
        timeout: int = 30,
    ):
        """
        Initialize Aster Futures API client.

        Parameters
        ----------
        api_key : str | None
            API key (optional, will use settings if not provided)
        api_secret : str | None
            API secret (optional, will use settings if not provided)
        base_url : str
            Base URL for API requests
        timeout : int
            Request timeout in seconds
        """
        self.api_key = api_key or aster_settings.api_key
        self.api_secret = api_secret or aster_settings.api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> "AsterFuturesClient":
        """Async context manager entry - initializes the HTTP session."""
        await self._get_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit - ensures session is closed."""
        await self.close()

    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for signed endpoints."""
        if not self.api_secret:
            raise AuthenticationError(-1015, "API secret is required for signed endpoints")
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _build_params(self, **kwargs: Any) -> dict[str, Any]:
        """Build params dict, excluding None values."""
        return {k: v for k, v in kwargs.items() if v is not None}

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        signed: bool = False,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Aster Futures API.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE)
        endpoint : str
            API endpoint path
        params : dict[str, Any] | None
            Request parameters
        signed : bool
            Whether this is a signed endpoint requiring authentication

        Returns
        -------
        dict[str, Any]
            API response data

        Raises
        ------
        RateLimitError
            When rate limit is exceeded (HTTP 429)
        AuthenticationError
            When authentication fails
        AsterFuturesError
            When API returns an error
        """
        if params is None:
            params = {}

        # Add timestamp and signature for signed endpoints
        if signed:
            if not self.api_key:
                raise AuthenticationError(-1015, "API key is required for signed endpoints")
            params["timestamp"] = int(time.time() * 1000)
            query_string = urlencode(sorted(params.items()))
            params["signature"] = self._generate_signature(query_string)

        url = f"{self.base_url}{endpoint}"
        headers: dict[str, str] = {}

        if signed and self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key

        session = await self._get_session()
        method_map = {
            "GET": session.get,
            "POST": session.post,
            "PUT": session.put,
            "DELETE": session.delete,
        }

        try:
            if method not in method_map:
                raise ValueError(f"Unsupported HTTP method: {method}")
            http_method = method_map[method]
            request_kwargs = {"headers": headers}
            if method in {"GET", "DELETE"}:
                request_kwargs["params"] = params
            else:
                request_kwargs["data"] = params

            async with http_method(url, **request_kwargs) as response:
                return await self._handle_response(response)

        except aiohttp.ClientError as e:
            logger.exception("HTTP client error")
            raise AsterFuturesError(-1, f"HTTP client error: {e}") from e

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response and check for errors."""
        # Check rate limit headers
        if response.status == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(-1023, f"Rate limit exceeded. Retry after {retry_after} seconds")

        if response.status == 403:
            raise AuthenticationError(-1022, "WAF limit violated")

        if response.status == 418:
            raise RateLimitError(-1023, "IP auto-banned for continuing to send requests after receiving 429 codes")

        data = await response.json()

        # Check for API error response
        if "code" in data and data["code"] != 200:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            if code == -1022:
                raise AuthenticationError(code, msg)
            if code == -1023:
                raise RateLimitError(code, msg)
            raise AsterFuturesError(code, msg)

        if response.status >= 500:
            raise AsterFuturesError(-1, f"Server error: HTTP {response.status}")

        return data

    # Market Data Endpoints (Public)

    async def test_connectivity(self) -> dict[str, Any]:
        """
        Test connectivity to the Rest API.

        Returns
        -------
        dict[str, Any]
            Empty dict if successful
        """
        return await self._request("GET", "/fapi/v1/ping")

    async def get_server_time(self) -> dict[str, Any]:
        """
        Check Server Time.

        Returns
        -------
        dict[str, Any]
            Server time in milliseconds
        """
        return await self._request("GET", "/fapi/v1/time")

    async def get_exchange_info(self, symbol: str | None = None) -> dict[str, Any]:
        """Exchange information."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/exchangeInfo", params)

    async def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        """
        Get order book.

        Parameters
        ----------
        symbol : str
            Trading symbol
        limit : int
            Limit of results (default: 100, max: 5000)

        Returns
        -------
        dict[str, Any]
            Order book data with bids and asks
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._request("GET", "/fapi/v1/depth", params)

    async def get_recent_trades(self, symbol: str, limit: int = 500) -> list[dict[str, Any]]:
        """
        Get recent trades list.

        Parameters
        ----------
        symbol : str
            Trading symbol
        limit : int
            Limit of results (default: 500, max: 1000)

        Returns
        -------
        list[dict[str, Any]]
            List of recent trades
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._request("GET", "/fapi/v1/trades", params)

    async def get_historical_trades(
        self, symbol: str, limit: int = 500, from_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Get older trades."""
        params = self._build_params(symbol=symbol, limit=limit, fromId=from_id)
        return await self._request("GET", "/fapi/v1/historicalTrades", params)

    async def get_aggregate_trades(
        self,
        symbol: str,
        from_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Get compressed/aggregate trades list."""
        params = self._build_params(symbol=symbol, fromId=from_id, startTime=start_time, endTime=end_time, limit=limit)
        return await self._request("GET", "/fapi/v1/aggTrades", params)

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[list[Any]]:
        """Kline/candlestick data."""
        params = self._build_params(
            symbol=symbol, interval=interval, startTime=start_time, endTime=end_time, limit=limit
        )
        return await self._request("GET", "/fapi/v1/klines", params)

    async def get_index_price_klines(
        self,
        pair: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[list[Any]]:
        """Index price kline/candlestick data."""
        params = self._build_params(pair=pair, interval=interval, startTime=start_time, endTime=end_time, limit=limit)
        return await self._request("GET", "/fapi/v1/indexPriceKlines", params)

    async def get_mark_price_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[list[Any]]:
        """Mark Price kline/candlestick data."""
        params = self._build_params(
            symbol=symbol, interval=interval, startTime=start_time, endTime=end_time, limit=limit
        )
        return await self._request("GET", "/fapi/v1/markPriceKlines", params)

    async def get_mark_price(self, symbol: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Mark Price."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/premiumIndex", params)

    async def get_funding_rate_history(
        self,
        symbol: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get funding rate history."""
        params = self._build_params(symbol=symbol, startTime=start_time, endTime=end_time, limit=limit)
        return await self._request("GET", "/fapi/v1/fundingRate", params)

    async def get_24hr_ticker(self, symbol: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """24hr ticker price change statistics."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/ticker/24hr", params)

    async def get_price_ticker(self, symbol: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Symbol price ticker."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/ticker/price", params)

    async def get_book_ticker(self, symbol: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Symbol order book ticker."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/ticker/bookTicker", params)

    # Account/Trades Endpoints (Signed - TRADE and USER_DATA)

    async def change_position_mode(self, *, dual_side_position: bool) -> dict[str, Any]:
        """
        Change position mode (TRADE).

        Parameters
        ----------
        dual_side_position : bool
            True for hedge mode, False for one-way mode

        Returns
        -------
        dict[str, Any]
            Response confirming position mode change
        """
        params = {"dualSidePosition": str(dual_side_position).lower()}
        return await self._request("POST", "/fapi/v1/positionSide/dual", params, signed=True)

    async def get_current_position_mode(self) -> PositionMode:
        """
        Get current position mode (USER_DATA).

        Returns
        -------
        PositionMode
            Current position mode setting
        """
        result = await self._request("GET", "/fapi/v1/positionSide/dual", signed=True)
        return PositionMode(**result)

    async def change_multi_assets_mode(self, *, multi_assets_margin: bool) -> dict[str, Any]:
        """
        Change Multi-Assets Mode (TRADE).

        Parameters
        ----------
        multi_assets_margin : bool
            True for multi-asset mode, False for single-asset mode

        Returns
        -------
        dict[str, Any]
            Response confirming mode change
        """
        params = {"multiAssetsMargin": str(multi_assets_margin).lower()}
        return await self._request("POST", "/fapi/v1/multiAssetsMargin", params, signed=True)

    async def get_current_multi_assets_mode(self) -> MultiAssetsMode:
        """
        Get Current Multi-Assets Mode (USER_DATA).

        Returns
        -------
        MultiAssetsMode
            Current multi-assets mode setting
        """
        result = await self._request("GET", "/fapi/v1/multiAssetsMargin", signed=True)
        return MultiAssetsMode(**result)

    async def new_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float | None = None,
        price: float | None = None,
        time_in_force: str = "GTC",
        *,
        reduce_only: bool = False,
        close_position: bool = False,
        stop_price: float | None = None,
        working_type: str | None = None,
        price_protect: bool = False,
        new_client_order_id: str | None = None,
        position_side: str = "BOTH",
    ) -> Order:
        """
        New order (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Order side (BUY or SELL)
        order_type : str
            Order type (MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET)
        quantity : float | None
            Order quantity (required for most order types)
        price : float | None
            Order price (required for LIMIT orders)
        time_in_force : str
            Time in force (GTC, IOC, FOK) - default: GTC
        reduce_only : bool
            Reduce only order (default: False)
        close_position : bool
            Close all positions (default: False)
        stop_price : float | None
            Stop price (required for STOP orders)
        working_type : str | None
            Working type (MARK_PRICE or CONTRACT_PRICE)
        price_protect : bool
            Price protect (default: False)
        new_client_order_id : str | None
            Client order ID (optional, max 32 chars)
        position_side : str
            Position side (BOTH, LONG, SHORT) - default: BOTH

        Returns
        -------
        Order
            Created order information
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "positionSide": position_side,
        }

        if quantity is not None:
            params["quantity"] = quantity
        if price is not None:
            params["price"] = price
        if time_in_force:
            params["timeInForce"] = time_in_force
        if reduce_only:
            params["reduceOnly"] = "true"
        if close_position:
            params["closePosition"] = "true"
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if working_type:
            params["workingType"] = working_type
        if price_protect:
            params["priceProtect"] = "true"
        if new_client_order_id:
            params["newClientOrderId"] = new_client_order_id

        result = await self._request("POST", "/fapi/v1/order", params, signed=True)
        return Order(**result)

    async def place_multiple_orders(self, batch_orders: list[dict[str, Any]]) -> list[Order]:
        """
        Place Multiple Orders (TRADE).

        Parameters
        ----------
        batch_orders : list[dict[str, Any]]
            List of order dictionaries (max 5 orders)

        Returns
        -------
        list[Order]
            List of created orders
        """
        if len(batch_orders) > 5:
            raise ValueError("Maximum 5 orders allowed in batch")
        params = {"batchOrders": json.dumps(batch_orders)}
        result = await self._request("POST", "/fapi/v1/batchOrders", params, signed=True)
        return [Order(**order) for order in result]

    async def query_order(
        self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None
    ) -> Order:
        """Query Order (USER_DATA)."""
        params = self._build_params(symbol=symbol, orderId=order_id, origClientOrderId=orig_client_order_id)
        result = await self._request("GET", "/fapi/v1/order", params, signed=True)
        return Order(**result)

    async def cancel_order(
        self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None
    ) -> Order:
        """Cancel Order (TRADE)."""
        params = self._build_params(symbol=symbol, orderId=order_id, origClientOrderId=orig_client_order_id)
        result = await self._request("DELETE", "/fapi/v1/order", params, signed=True)
        return Order(**result)

    async def cancel_all_open_orders(self, symbol: str) -> dict[str, Any]:
        """
        Cancel All Open Orders (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol

        Returns
        -------
        dict[str, Any]
            Response confirming cancellation
        """
        params = {"symbol": symbol}
        return await self._request("DELETE", "/fapi/v1/allOpenOrders", params, signed=True)

    async def cancel_multiple_orders(
        self, symbol: str, order_id_list: list[int] | None = None, orig_client_order_id_list: list[str] | None = None
    ) -> list[Order]:
        """
        Cancel Multiple Orders (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        order_id_list : list[int] | None
            List of order IDs (optional)
        orig_client_order_id_list : list[str] | None
            List of client order IDs (optional)

        Returns
        -------
        list[Order]
            List of cancelled orders
        """
        params: dict[str, Any] = {"symbol": symbol}
        if order_id_list:
            params["orderIdList"] = json.dumps(order_id_list)
        if orig_client_order_id_list:
            params["origClientOrderIdList"] = json.dumps(orig_client_order_id_list)
        result = await self._request("DELETE", "/fapi/v1/batchOrders", params, signed=True)
        return [Order(**order) for order in result]

    async def auto_cancel_all_open_orders(self, symbol: str, countdown_time: int) -> dict[str, Any]:
        """
        Auto-Cancel All Open Orders (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        countdown_time : int
            Countdown time in seconds (10 to 600)

        Returns
        -------
        dict[str, Any]
            Response with countdown timer information
        """
        params = {"symbol": symbol, "countdownTime": countdown_time}
        return await self._request("POST", "/fapi/v1/countdownCancelAll", params, signed=True)

    async def get_current_open_order(
        self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None
    ) -> Order:
        """Query Current Open Order (USER_DATA)."""
        params = self._build_params(symbol=symbol, orderId=order_id, origClientOrderId=orig_client_order_id)
        result = await self._request("GET", "/fapi/v1/openOrder", params, signed=True)
        return Order(**result)

    async def get_all_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Current All Open Orders (USER_DATA)."""
        params = self._build_params(symbol=symbol)
        result = await self._request("GET", "/fapi/v1/openOrders", params, signed=True)
        return [Order(**order) for order in result]

    async def get_all_orders(
        self,
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[Order]:
        """All Orders (USER_DATA)."""
        params = self._build_params(
            symbol=symbol, orderId=order_id, startTime=start_time, endTime=end_time, limit=limit
        )
        result = await self._request("GET", "/fapi/v1/allOrders", params, signed=True)
        return [Order(**order) for order in result]

    async def get_futures_account_balance_v2(self) -> list[FuturesAccountBalance]:
        """
        Futures Account Balance V2 (USER_DATA).

        Returns
        -------
        list[FuturesAccountBalance]
            List of account balances
        """
        result = await self._request("GET", "/fapi/v2/balance", signed=True)
        return [FuturesAccountBalance(**balance) for balance in result]

    async def get_account_information_v4(self) -> AccountInformation:
        """
        Account Information V4 (USER_DATA).

        Returns
        -------
        AccountInformation
            Account information
        """
        result = await self._request("GET", "/fapi/v4/account", signed=True)
        return AccountInformation(**result)

    async def change_initial_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        """
        Change Initial Leverage (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        leverage : int
            Leverage (1-125)

        Returns
        -------
        dict[str, Any]
            Response confirming leverage change
        """
        params = {"symbol": symbol, "leverage": leverage}
        return await self._request("POST", "/fapi/v1/leverage", params, signed=True)

    async def change_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        """
        Change Margin Type (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        margin_type : str
            Margin type (ISOLATED or CROSSED)

        Returns
        -------
        dict[str, Any]
            Response confirming margin type change
        """
        params = {"symbol": symbol, "marginType": margin_type}
        return await self._request("POST", "/fapi/v1/marginType", params, signed=True)

    async def modify_isolated_position_margin(self, symbol: str, amount: float, type: int) -> dict[str, Any]:
        """
        Modify Isolated Position Margin (TRADE).

        Parameters
        ----------
        symbol : str
            Trading symbol
        amount : float
            Amount to add or reduce
        type : int
            Type (1: add, 2: reduce)

        Returns
        -------
        dict[str, Any]
            Response confirming margin modification
        """
        params = {"symbol": symbol, "amount": amount, "type": type}
        return await self._request("POST", "/fapi/v1/positionMargin", params, signed=True)

    async def get_position_information_v2(self, symbol: str | None = None) -> list[Position]:
        """Position Information V2 (USER_DATA)."""
        params = self._build_params(symbol=symbol)
        result = await self._request("GET", "/fapi/v2/positionRisk", params, signed=True)
        return [Position(**position) for position in result]

    async def get_account_trade_list(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        from_id: int | None = None,
        limit: int = 500,
    ) -> list[Trade]:
        """Account Trade List (USER_DATA)."""
        params = self._build_params(symbol=symbol, startTime=start_time, endTime=end_time, fromId=from_id, limit=limit)
        result = await self._request("GET", "/fapi/v1/userTrades", params, signed=True)
        return [Trade(**trade) for trade in result]

    async def get_income_history(
        self,
        symbol: str | None = None,
        income_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[Income]:
        """Get Income History (USER_DATA)."""
        params = self._build_params(
            symbol=symbol, incomeType=income_type, startTime=start_time, endTime=end_time, limit=limit
        )
        result = await self._request("GET", "/fapi/v1/income", params, signed=True)
        return [Income(**income) for income in result]

    async def get_notional_and_leverage_brackets(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Notional and Leverage Brackets (USER_DATA)."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/leverageBracket", params, signed=True)

    async def get_position_adl_quantile_estimation(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Position ADL Quantile Estimation (USER_DATA)."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/adlQuantile", params, signed=True)

    async def get_users_force_orders(
        self,
        symbol: str | None = None,
        auto_close_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """User's Force Orders (USER_DATA)."""
        params = self._build_params(
            symbol=symbol, autoCloseType=auto_close_type, startTime=start_time, endTime=end_time, limit=limit
        )
        return await self._request("GET", "/fapi/v1/forceOrders", params, signed=True)

    async def get_user_commission_rate(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """User Commission Rate (USER_DATA)."""
        params = self._build_params(symbol=symbol)
        return await self._request("GET", "/fapi/v1/commissionRate", params, signed=True)
