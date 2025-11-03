"""
Aster-based cryptocurrency data tools following LangChain @tool decorator pattern.

Migrated from BaseTool class-based approach to @tool decorator as per:
https://docs.langchain.com/oss/python/langchain/agents#tools

All tools follow the pattern:
- Use @tool decorator with args_schema
- Provide comprehensive docstrings (used by LLM for understanding)
- Return JSON strings for structured data
- Handle errors gracefully with error JSON responses
"""

import json

from app.backend.client import AsterClient
from langchain.tools import tool
from pydantic import BaseModel, Field


# Input Schemas
class AsterPriceInput(BaseModel):
    """Input schema for Aster price tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    exchange: str = Field(default="aster", description="Exchange name (always aster)")


class AsterHistoryInput(BaseModel):
    """Input schema for Aster history tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    limit: int = Field(default=100, description="Number of data points (max 1000)")
    exchange: str = Field(default="aster", description="Exchange name (always aster)")


class AsterOrderBookInput(BaseModel):
    """Input schema for Aster order book tool."""

    symbol: str = Field(description="Cryptocurrency symbol (e.g., BTCUSDT)")
    exchange: str = Field(default="aster", description="Exchange name (always aster)")


class AsterAccountInput(BaseModel):
    """Input schema for Aster account tool."""

    exchange: str = Field(default="aster", description="Exchange name (always aster)")


class AsterMultiPriceInput(BaseModel):
    """Input schema for fetching multiple cryptocurrency prices."""

    symbols: str = Field(description="Comma-separated trading symbols (e.g., 'BTCUSDT,ETHUSDT,SOLUSDT')")
    exchange: str = Field(default="aster", description="Exchange name (always aster)")


# Tool Implementations using @tool decorator


@tool(args_schema=AsterPriceInput)
def aster_get_price(symbol: str, exchange: str = "aster") -> str:
    """
    Get real-time cryptocurrency price data from Aster exchange.

    This tool fetches current market data including price, volume, 24h changes,
    and high/low values for a specified cryptocurrency symbol. Use this when you
    need current market prices for analysis or decision making.

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (always "aster")

    Returns
    -------
        JSON string containing:
        - symbol: Trading pair symbol
        - price: Current market price
        - volume: 24h trading volume
        - change_24h: Absolute price change in 24h
        - change_percent_24h: Percentage price change in 24h
        - high_24h: Highest price in 24h
        - low_24h: Lowest price in 24h
        - timestamp: Data timestamp
        - exchange: Exchange identifier
    """
    try:
        with AsterClient() as client:
            ticker = client.get_ticker(symbol)
            result = {
                "symbol": ticker.symbol,
                "price": ticker.price,
                "volume": ticker.volume,
                "change_24h": ticker.change_24h,
                "change_percent_24h": ticker.change_percent_24h,
                "high_24h": ticker.high_24h,
                "low_24h": ticker.low_24h,
                "timestamp": ticker.timestamp.isoformat(),
                "exchange": ticker.exchange,
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": str(e), "symbol": symbol, "exchange": exchange}
        return json.dumps(error_result, indent=2)


@tool(args_schema=AsterHistoryInput)
def aster_get_history(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    exchange: str = "aster",
) -> str:
    """
    Get historical OHLCV (Open, High, Low, Close, Volume) data for technical analysis.

    This tool retrieves historical price data that can be used for technical analysis,
    pattern recognition, and trend analysis. Each data point includes OHLCV values.

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        timeframe: Candle timeframe - valid options are:
                   1m (1 minute), 5m, 15m, 30m, 1h (1 hour), 4h, 1d (1 day)
        limit: Number of historical data points to retrieve (max 1000)
        exchange: Exchange name (always "aster")

    Returns
    -------
        JSON string containing:
        - symbol: Trading pair symbol
        - timeframe: The requested timeframe
        - exchange: Exchange identifier
        - data: Array of OHLCV objects with timestamp, open, high, low, close, volume
        - count: Number of data points returned
    """
    try:
        with AsterClient() as client:
            klines = client.get_klines(symbol, timeframe, limit)
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "exchange": "aster",
                "data": [
                    {
                        "timestamp": kline.timestamp.isoformat(),
                        "open": kline.open,
                        "high": kline.high,
                        "low": kline.low,
                        "close": kline.close,
                        "volume": kline.volume,
                    }
                    for kline in klines
                ],
                "count": len(klines),
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {
            "error": str(e),
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
        }
        return json.dumps(error_result, indent=2)


@tool(args_schema=AsterOrderBookInput)
def aster_get_order_book(symbol: str, exchange: str = "aster") -> str:
    """
    Get order book data for market depth analysis from Aster exchange.

    The order book shows current buy (bid) and sell (ask) orders, which helps
    understand market liquidity, support/resistance levels, and potential price
    movements. This is crucial for assessing market depth before large trades.

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        exchange: Exchange name (always "aster")

    Returns
    -------
        JSON string containing:
        - symbol: Trading pair symbol
        - bids: Array of [price, quantity] bid orders (buy orders)
        - asks: Array of [price, quantity] ask orders (sell orders)
        - timestamp: Data timestamp
        - exchange: Exchange identifier
        - spread: Difference between best ask and best bid (market spread)
    """
    try:
        with AsterClient() as client:
            order_book = client.get_order_book(symbol)
            result = {
                "symbol": order_book.symbol,
                "bids": order_book.bids,
                "asks": order_book.asks,
                "timestamp": order_book.timestamp.isoformat(),
                "exchange": order_book.exchange,
                "spread": order_book.asks[0][0] - order_book.bids[0][0]
                if order_book.bids and order_book.asks
                else None,
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": str(e), "symbol": symbol, "exchange": exchange}
        return json.dumps(error_result, indent=2)


@tool(args_schema=AsterAccountInput)
def aster_get_account(exchange: str = "aster") -> str:
    """
    Get account information and balance from Aster exchange.

    This tool retrieves current account status including total balance, available
    funds for trading, used balance in open positions, and active positions. Use
    this to check available capital before making trading decisions.

    Args:
        exchange: Exchange name (always "aster")

    Returns
    -------
        JSON string containing:
        - total_balance: Total account balance (USDT)
        - available_balance: Available funds for trading (USDT)
        - used_balance: Funds locked in open positions (USDT)
        - positions: List of active trading positions
        - timestamp: Data timestamp
        - exchange: Exchange identifier
    """
    try:
        with AsterClient() as client:
            account = client.get_account_info()
            result = {
                "total_balance": account.total_balance,
                "available_balance": account.available_balance,
                "used_balance": account.used_balance,
                "positions": account.positions,
                "timestamp": account.timestamp.isoformat(),
                "exchange": "aster",
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": str(e), "exchange": exchange}
        return json.dumps(error_result, indent=2)


@tool(args_schema=AsterMultiPriceInput)
def aster_get_multi_price(symbols: str, exchange: str = "aster") -> str:
    """
    Get real-time prices for multiple cryptocurrencies in a single call.

    This tool efficiently fetches price data for multiple symbols at once, which
    is useful for portfolio analysis, correlation analysis, or getting a market
    overview. More efficient than calling aster_get_price multiple times.

    Args:
        symbols: Comma-separated trading symbols (e.g., "BTCUSDT,ETHUSDT,SOLUSDT")
        exchange: Exchange name (always "aster")

    Returns
    -------
        JSON string containing a dictionary where keys are symbols and values are
        price objects with the same fields as aster_get_price (price, volume,
        change_24h, etc.). Failed symbols will have an "error" field.
    """
    try:
        # Parse symbols from comma-separated string
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

        with AsterClient() as client:
            result = {}
            for sym in symbol_list:
                try:
                    ticker = client.get_ticker(sym)
                    result[sym] = {
                        "symbol": ticker.symbol,
                        "price": ticker.price,
                        "volume": ticker.volume,
                        "change_24h": ticker.change_24h,
                        "change_percent_24h": ticker.change_percent_24h,
                        "high_24h": ticker.high_24h,
                        "low_24h": ticker.low_24h,
                        "timestamp": ticker.timestamp.isoformat(),
                        "exchange": ticker.exchange,
                    }
                except Exception as sym_error:
                    result[sym] = {
                        "error": str(sym_error),
                        "symbol": sym,
                        "exchange": "aster",
                    }

            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {"error": str(e), "symbols": symbols, "exchange": exchange}
        return json.dumps(error_result, indent=2)
