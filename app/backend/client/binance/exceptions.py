"""Binance API exception classes."""

from typing import Any


class BinanceAPIException(Exception):
    """Base exception for Binance API errors."""

    def __init__(self, message: str, code: int | None = None, response: dict[str, Any] | None = None):
        """
        Initialize Binance API exception.

        Parameters
        ----------
        message : str
            Error message
        code : int | None
            Binance error code
        response : dict[str, Any] | None
            Full API response
        """
        super().__init__(message)
        self.code = code
        self.response = response


class BinanceRequestException(BinanceAPIException):
    """Exception for request-related errors."""


class BinanceAuthenticationError(BinanceAPIException):
    """Exception for authentication failures."""


class BinanceRateLimitError(BinanceAPIException):
    """Exception for rate limit violations."""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs: Any):
        """
        Initialize rate limit exception.

        Parameters
        ----------
        message : str
            Error message
        retry_after : int | None
            Seconds to wait before retry
        **kwargs : Any
            Additional parameters for base exception
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after or 60


class BinanceOrderError(BinanceAPIException):
    """Exception for order-related errors."""


class BinanceInsufficientBalanceError(BinanceOrderError):
    """Exception for insufficient balance errors."""


class BinanceInvalidSymbolError(BinanceAPIException):
    """Exception for invalid symbol errors."""


class BinanceServerError(BinanceAPIException):
    """Exception for server-side errors."""


class BinanceTimeoutError(BinanceAPIException):
    """Exception for request timeout errors."""


def parse_binance_error(status_code: int, response: dict[str, Any]) -> BinanceAPIException:
    """
    Parse Binance API error response and return appropriate exception.

    Parameters
    ----------
    status_code : int
        HTTP status code
    response : dict[str, Any]
        Error response from API

    Returns
    -------
    BinanceAPIException
        Appropriate exception for the error
    """
    code = response.get("code", 0)
    msg = response.get("msg", "Unknown error")

    # Rate limiting errors (-1003, -1015, 429)
    if code in (-1003, -1015) or status_code == 429:
        retry_after = 60 if code == -1003 else 120
        return BinanceRateLimitError(
            f"Rate limit exceeded: {msg}",
            code=code,
            response=response,
            retry_after=retry_after,
        )

    # Authentication errors (-1022, -2014, -2015)
    if code in (-1022, -2014, -2015):
        return BinanceAuthenticationError(
            f"Authentication failed: {msg}",
            code=code,
            response=response,
        )

    # Order errors (-1111, -2010, -2011, -4164)
    if code in (-1111, -2010, -2011, -4164):
        return BinanceOrderError(
            f"Order error: {msg}",
            code=code,
            response=response,
        )

    # Insufficient balance (-2019)
    if code == -2019:
        return BinanceInsufficientBalanceError(
            f"Insufficient balance: {msg}",
            code=code,
            response=response,
        )

    # Invalid symbol (-1121)
    if code == -1121:
        return BinanceInvalidSymbolError(
            f"Invalid symbol: {msg}",
            code=code,
            response=response,
        )

    # Server errors (5xx)
    if 500 <= status_code < 600:
        return BinanceServerError(
            f"Server error: {msg}",
            code=code,
            response=response,
        )

    # Timeout errors
    if status_code == 408 or code == -1007:
        return BinanceTimeoutError(
            f"Request timeout: {msg}",
            code=code,
            response=response,
        )

    # Generic request error
    return BinanceRequestException(
        f"Request failed: {msg}",
        code=code,
        response=response,
    )
