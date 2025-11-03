"""Rate limiter for Binance API requests."""

import asyncio
import time
from collections import deque
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API requests.

    Implements rate limiting with support for multiple time windows.
    """

    def __init__(self, requests_per_minute: int = 1200, burst_limit: int | None = None):
        """
        Initialize rate limiter.

        Parameters
        ----------
        requests_per_minute : int
            Maximum requests per minute (default: 1200 for Binance)
        burst_limit : int | None
            Maximum burst size (default: requests_per_minute / 10)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or max(requests_per_minute // 10, 10)

        # Request timestamps for sliding window
        self.request_times: deque[float] = deque(maxlen=requests_per_minute)

        # Token bucket for burst control
        self.tokens = float(self.burst_limit)
        self.last_refill = time.time()
        self.refill_rate = requests_per_minute / 60.0  # tokens per second

        self._lock = asyncio.Lock()

        logger.info(
            "Rate limiter initialized",
            requests_per_minute=requests_per_minute,
            burst_limit=self.burst_limit,
        )

    async def acquire(self, weight: int = 1) -> None:
        """
        Acquire permission to make a request.

        Parameters
        ----------
        weight : int
            Request weight (default: 1)
        """
        async with self._lock:
            # Refill tokens
            now = time.time()
            time_passed = now - self.last_refill
            self.tokens = min(
                self.burst_limit,
                self.tokens + time_passed * self.refill_rate,
            )
            self.last_refill = now

            # Check if we need to wait
            if self.tokens < weight:
                wait_time = (weight - self.tokens) / self.refill_rate
                logger.debug(
                    "Rate limit approached, waiting",
                    wait_time=wait_time,
                    tokens=self.tokens,
                    weight=weight,
                )
                await asyncio.sleep(wait_time)

                # Refill after waiting
                now = time.time()
                time_passed = now - self.last_refill
                self.tokens = min(
                    self.burst_limit,
                    self.tokens + time_passed * self.refill_rate,
                )
                self.last_refill = now

            # Consume tokens
            self.tokens -= weight

            # Add to request history
            self.request_times.append(now)

    def get_current_rate(self) -> dict[str, Any]:
        """
        Get current rate limiting statistics.

        Returns
        -------
        dict[str, Any]
            Statistics including tokens, request count
        """
        now = time.time()
        minute_ago = now - 60

        # Count requests in last minute
        recent_requests = sum(1 for t in self.request_times if t > minute_ago)

        return {
            "tokens_available": self.tokens,
            "max_tokens": self.burst_limit,
            "requests_last_minute": recent_requests,
            "max_requests_per_minute": self.requests_per_minute,
            "utilization": recent_requests / self.requests_per_minute,
        }

    async def wait_if_needed(self) -> None:
        """Wait if rate limit is close to being exceeded."""
        stats = self.get_current_rate()
        if stats["utilization"] > 0.9:  # 90% utilization
            wait_time = 1.0  # Wait 1 second
            logger.warning(
                "High rate limit utilization, throttling",
                utilization=stats["utilization"],
                wait_time=wait_time,
            )
            await asyncio.sleep(wait_time)


class OrderRateLimiter:
    """
    Specialized rate limiter for order operations.

    Binance has separate rate limits for orders.
    """

    def __init__(self, orders_per_10_seconds: int = 100, orders_per_day: int = 200000):
        """
        Initialize order rate limiter.

        Parameters
        ----------
        orders_per_10_seconds : int
            Maximum orders per 10 seconds
        orders_per_day : int
            Maximum orders per day
        """
        self.orders_per_10_seconds = orders_per_10_seconds
        self.orders_per_day = orders_per_day

        # Track orders in different time windows
        self.orders_10s: deque[float] = deque(maxlen=orders_per_10_seconds)
        self.orders_1d: deque[float] = deque(maxlen=orders_per_day)

        self._lock = asyncio.Lock()

    async def acquire_order(self) -> None:
        """Acquire permission to place an order."""
        async with self._lock:
            now = time.time()

            # Check 10-second window
            ten_seconds_ago = now - 10
            recent_orders_10s = sum(1 for t in self.orders_10s if t > ten_seconds_ago)

            if recent_orders_10s >= self.orders_per_10_seconds:
                wait_time = 10.0 - (now - self.orders_10s[0])
                logger.warning(
                    "Order rate limit (10s) reached, waiting",
                    wait_time=wait_time,
                    recent_orders=recent_orders_10s,
                )
                await asyncio.sleep(wait_time)
                now = time.time()

            # Check daily window
            one_day_ago = now - 86400
            recent_orders_1d = sum(1 for t in self.orders_1d if t > one_day_ago)

            if recent_orders_1d >= self.orders_per_day:
                raise RuntimeError(f"Daily order limit reached ({self.orders_per_day}). Please wait until tomorrow.")

            # Record order
            self.orders_10s.append(now)
            self.orders_1d.append(now)

    def get_order_stats(self) -> dict[str, Any]:
        """
        Get order rate limiting statistics.

        Returns
        -------
        dict[str, Any]
            Order statistics
        """
        now = time.time()
        ten_seconds_ago = now - 10
        one_day_ago = now - 86400

        return {
            "orders_last_10s": sum(1 for t in self.orders_10s if t > ten_seconds_ago),
            "max_orders_per_10s": self.orders_per_10_seconds,
            "orders_last_day": sum(1 for t in self.orders_1d if t > one_day_ago),
            "max_orders_per_day": self.orders_per_day,
        }
