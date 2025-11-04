"""Aster REST API client for cryptocurrency trading."""

import asyncio
import contextlib
from datetime import UTC, datetime
from typing import Any

import structlog
from app.backend.config.aster import get_aster_settings
from aster.error import ClientError, ServerError
from aster.rest_api import Client as AsterRestClient
from pydantic import BaseModel, Field

aster_settings = get_aster_settings()

logger = structlog.get_logger(__name__)


class AsterTicker(BaseModel):
    """Aster ticker data model."""

    symbol: str
    price: float
    volume: float
    change_24h: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    exchange: str = "aster"


class AsterOHLCV(BaseModel):
    """Aster OHLCV data model."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str = "aster"


class AsterOrderBook(BaseModel):
    """Aster order book data model."""

    symbol: str
    bids: list[list[float]] = Field(description="List of [price, quantity] for bids")
    asks: list[list[float]] = Field(description="List of [price, quantity] for asks")
    timestamp: datetime
    exchange: str = "aster"


class AsterAccount(BaseModel):
    """Aster account information."""

    total_balance: float
    available_balance: float
    used_balance: float
    positions: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class AsterOrder(BaseModel):
    """Aster order model."""

    order_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    type: str  # "MARKET", "LIMIT", etc.
    quantity: float
    price: float | None = None
    status: str
    timestamp: datetime
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    average_price: float | None = None


class AsterClient:
    """Aster REST API client wrapper."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        """
        Initialize Aster client.

        The client is initialized immediately and can be used directly
        or as a context manager for automatic cleanup.

        Parameters
        ----------
        api_key : str | None
            Custom API key. If None, uses global aster_settings
        api_secret : str | None
            Custom API secret. If None, uses global aster_settings
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._client = None
        self._initialize_client()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._close_client()

    def __del__(self):
        """Cleanup client on garbage collection."""
        self._close_client()

    def _initialize_client(self) -> None:
        """Initialize the Aster REST client."""
        try:
            if self._client is None:
                # Use custom credentials if provided, otherwise fallback to global settings
                api_key = self._api_key if self._api_key is not None else aster_settings.api_key
                api_secret = self._api_secret if self._api_secret is not None else aster_settings.api_secret

                self._client = AsterRestClient(
                    key=api_key,
                    secret=api_secret,
                    base_url=aster_settings.base_url,
                    timeout=aster_settings.timeout,
                    show_limit_usage=aster_settings.show_limit_usage,
                    show_header=aster_settings.show_header,
                )
                if self._api_key is not None:
                    logger.info("Aster client initialized with custom credentials")
                else:
                    logger.info("Aster client initialized with global settings")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Aster client: {e}") from e

    def _close_client(self) -> None:
        """Close and cleanup the Aster REST client."""
        if self._client is not None:
            if hasattr(self._client, "close") and callable(self._client.close):
                with contextlib.suppress(Exception):
                    self._client.close()  # type: ignore[attr-defined]
            self._client = None
            logger.debug("Aster client closed")

    def get_ticker(self, symbol: str) -> AsterTicker:
        """
        Get ticker data for a symbol.

        Parameters
        ----------
        symbol : str
            Trading symbol (e.g., "BTCUSDT")

        Returns
        -------
        AsterTicker
            Ticker data
        """
        try:
            # Try different ticker methods to find the correct one
            result = None
            method_used = None

            # Try ticker_24hr_price_change first (most comprehensive data)
            if hasattr(self._client, "ticker_24hr_price_change"):
                result = self._client.ticker_24hr_price_change(symbol)
                method_used = "ticker_24hr_price_change"
            # Try ticker_price as fallback
            elif hasattr(self._client, "ticker_price"):
                result = self._client.ticker_price(symbol)
                method_used = "ticker_price"
            # Try book_ticker as last resort
            elif hasattr(self._client, "book_ticker"):
                result = self._client.book_ticker(symbol)
                method_used = "book_ticker"
            else:
                # List available methods for debugging
                available_methods = [method for method in dir(self._client) if not method.startswith("_")]
                logger.error("No ticker method found. Available methods: %s", available_methods)
                error_msg = f"No ticker method available on Aster client. Available methods: {available_methods}"
                raise RuntimeError(error_msg)

            logger.debug("Got ticker response for %s using method %s: %s", symbol, method_used, result)
            return self._parse_ticker_data(result, symbol)

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get ticker for {symbol}: {e}") from e

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[AsterOHLCV]:
        """
        Get historical kline/candlestick data.

        Parameters
        ----------
        symbol : str
            Trading symbol
        interval : str
            Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        limit : int
            Number of klines to retrieve

        Returns
        -------
        List[AsterOHLCV]
            List of OHLCV data
        """
        try:
            result = self._client.klines(symbol, interval, limit=limit)
            return self._parse_klines_data(result, symbol)

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get klines for {symbol}: {e}") from e

    def get_klines_by_date_range(
        self, symbol: str, interval: str = "1h", start_date: str | None = None, end_date: str | None = None
    ) -> list[AsterOHLCV]:
        """
        Get historical kline/candlestick data for a specific date range.

        Parameters
        ----------
        symbol : str
            Trading symbol
        interval : str
            Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        start_date : str | None
            Start date in YYYY-MM-DD format
        end_date : str | None
            End date in YYYY-MM-DD format

        Returns
        -------
        List[AsterOHLCV]
            List of OHLCV data within the date range
        """
        try:
            # Calculate appropriate limit based on date range
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=None)
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=None)
                days_diff = (end_dt - start_dt).days

                # Calculate limit based on interval and date range
                interval_hours = {
                    "1m": 1 / 60,
                    "5m": 5 / 60,
                    "15m": 15 / 60,
                    "30m": 30 / 60,
                    "1h": 1,
                    "4h": 4,
                    "1d": 24,
                }.get(interval, 1)

                # For historical data, we need to request enough data to cover the full date range
                # The Aster API returns the most recent klines, so we need to request enough
                # to go back to the start date. For simplicity, always request 1000
                # which gives us about 41 days of 1h data
                limit = 1000
            else:
                limit = 100  # Default limit if no dates provided

            result = self._client.klines(symbol, interval, limit=limit)

            if not result:
                return []

            # Parse the raw kline data first
            parsed_klines = self._parse_klines_data(result, symbol)

            # Filter by date range if provided
            if start_date and end_date:
                start_timestamp = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000
                end_timestamp = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000

                logger.debug(
                    "Filtering %d klines from %s to %s (timestamps: %s to %s)",
                    len(parsed_klines),
                    start_date,
                    end_date,
                    start_timestamp,
                    end_timestamp,
                )

                filtered_klines = []
                for kline in parsed_klines:
                    kline_ts = kline.timestamp.timestamp() * 1000
                    if start_timestamp <= kline_ts <= end_timestamp:
                        filtered_klines.append(kline)

                logger.debug("Filtered result: %d klines", len(filtered_klines))
                return filtered_klines

            return parsed_klines

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to get klines for {symbol} in date range {start_date} to {end_date}: {e}"
            ) from e

    def get_order_book(self, symbol: str, limit: int = 100) -> AsterOrderBook:
        """
        Get order book data.

        Parameters
        ----------
        symbol : str
            Trading symbol
        limit : int
            Number of orders to retrieve

        Returns
        -------
        AsterOrderBook
            Order book data
        """
        try:
            result = self._client.depth(symbol, limit=limit)
            return self._parse_order_book_data(result, symbol)

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get order book for {symbol}: {e}") from e

    def get_account_info(self) -> AsterAccount:
        """
        Get account information.

        Returns
        -------
        AsterAccount
            Account information
        """
        try:
            result = self._client.account()
            return self._parse_account_data(result)

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get account info: {e}") from e

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
    ) -> AsterOrder:
        """
        Place a new order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        side : str
            Order side ("BUY" or "SELL")
        order_type : str
            Order type ("MARKET", "LIMIT", etc.)
        quantity : float
            Order quantity
        price : float | None
            Order price (required for LIMIT orders)
        time_in_force : str
            Time in force ("GTC", "IOC", "FOK")

        Returns
        -------
        AsterOrder
            Order information
        """
        try:
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                # "timeInForce": time_in_force,
            }

            if price is not None:
                order_params["price"] = price

            result = self._client.new_order(**order_params)
            return self._parse_order_data(result, symbol)

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to place order: {e}") from e

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an order.

        Parameters
        ----------
        symbol : str
            Trading symbol
        order_id : str
            Order ID to cancel

        Returns
        -------
        bool
            True if successful
        """
        try:
            result = self._client.cancel_order(symbol=symbol, orderId=order_id)
            return result.get("status") == "CANCELED"

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to cancel order: {e}") from e

    def get_open_orders(self, symbol: str | None = None) -> list[AsterOrder]:
        """
        Get open orders.

        Parameters
        ----------
        symbol : str | None
            Trading symbol (optional)

        Returns
        -------
        list[AsterOrder]
            List of open orders
        """
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol

            result = self._client.open_orders(**params)  # type: ignore[attr-defined]
            return [self._parse_order_data(order, order.get("symbol", "")) for order in result]

        except ClientError as e:
            raise RuntimeError(f"Aster API client error: {e.error_message}") from e
        except ServerError as e:
            raise RuntimeError(f"Aster API server error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to get open orders: {e}") from e

    # Async wrapper methods
    async def aget_ticker(self, symbol: str) -> AsterTicker:
        """Async wrapper for get_ticker."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_ticker, symbol)

    async def aget_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[AsterOHLCV]:
        """Async wrapper for get_klines."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_klines, symbol, interval, limit)

    async def aget_order_book(self, symbol: str, limit: int = 100) -> AsterOrderBook:
        """Async wrapper for get_order_book."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_order_book, symbol, limit)

    async def aget_account_info(self) -> AsterAccount:
        """Async wrapper for get_account_info."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_account_info)

    async def aplace_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
    ) -> AsterOrder:
        """Async wrapper for place_order."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.place_order, symbol, side, order_type, quantity, price, time_in_force
        )

    async def acancel_order(self, symbol: str, order_id: str) -> bool:
        """Async wrapper for cancel_order."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cancel_order, symbol, order_id)

    async def aget_open_orders(self, symbol: str | None = None) -> list[AsterOrder]:
        """Async wrapper for get_open_orders."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_open_orders, symbol)

    def _parse_ticker_data(self, data: dict[str, Any], symbol: str) -> AsterTicker:
        """Parse ticker data from Aster API ticker24hr response."""
        # Try to get lastPrice first, then price, default to 0
        price = float(data.get("lastPrice", data.get("price", 0)))

        # Log warning if price is zero (missing data)
        if price == 0:
            logger.warning(
                "Price data missing for %s in API response. Available keys: %s. Data: %s",
                symbol,
                list(data.keys()),
                data,
            )

        return AsterTicker(
            symbol=symbol,
            price=price,
            volume=float(data.get("volume", 0)),  # 24h volume in base currency
            change_24h=float(data.get("priceChange", 0)),
            change_percent_24h=float(data.get("priceChangePercent", 0)),
            high_24h=float(data.get("highPrice", 0)),
            low_24h=float(data.get("lowPrice", 0)),
            timestamp=datetime.now(),
            exchange="aster",
        )

    def _parse_klines_data(self, data: list[list[Any]], symbol: str) -> list[AsterOHLCV]:
        """Parse klines data from Aster API response."""
        return [
            AsterOHLCV(
                timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=UTC),
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[5]),
                symbol=symbol,
                exchange="aster",
            )
            for kline in data
        ]

    def _parse_order_book_data(self, data: dict[str, Any], symbol: str) -> AsterOrderBook:
        """Parse order book data from Aster API response."""
        return AsterOrderBook(
            symbol=symbol,
            bids=[[float(price), float(qty)] for price, qty in data.get("bids", [])],
            asks=[[float(price), float(qty)] for price, qty in data.get("asks", [])],
            timestamp=datetime.now(),
            exchange="aster",
        )

    def _parse_account_data(self, data: dict[str, Any]) -> AsterAccount:
        """Parse account data from Aster API response."""
        return AsterAccount(
            total_balance=float(data.get("totalWalletBalance", 0)),
            available_balance=float(data.get("availableBalance", 0)),
            used_balance=float(data.get("totalWalletBalance", 0)) - float(data.get("availableBalance", 0)),
            positions=data.get("positions", {}),
            timestamp=datetime.now(),
        )

    def _parse_order_data(self, data: dict[str, Any], symbol: str) -> AsterOrder:
        """Parse order data from Aster API response."""
        return AsterOrder(
            order_id=str(data.get("orderId", "")),
            symbol=symbol,
            side=data.get("side", ""),
            type=data.get("type", ""),
            quantity=float(data.get("origQty", 0)),
            price=float(data.get("price", 0)) if data.get("price") else None,
            status=data.get("status", ""),
            timestamp=datetime.now(),
            filled_quantity=float(data.get("executedQty", 0)),
            remaining_quantity=float(data.get("origQty", 0)) - float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0)) if data.get("avgPrice") else None,
        )
