"""Binance Testnet configuration for futures trading."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BinanceConfig(BaseSettings):
    """Configuration for Binance Testnet Futures client."""

    model_config = SettingsConfigDict(env_prefix="BINANCE_", case_sensitive=False)

    # API Connection Settings
    api_key: str | None = Field(default=None, description="Binance API key")
    api_secret: str | None = Field(default=None, description="Binance API secret")
    testnet: bool = Field(default=True, description="Use testnet or production")
    base_url: str = Field(
        default="https://testnet.binancefuture.com",
        description="Binance Futures API base URL",
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    recv_window: int = Field(default=5000, description="Request valid time window in ms")

    # Risk Management Settings
    max_position_pct: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Maximum position size as percentage of portfolio (0.0-1.0)",
    )
    min_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for executing trades (0.0-1.0)",
    )
    max_gross_exposure: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Maximum total gross exposure across all positions (0.0-2.0)",
    )
    min_order_size: float = Field(
        default=10.0,
        ge=0.0,
        description="Minimum order size in USD",
    )
    max_order_size: float = Field(
        default=100000.0,
        ge=0.0,
        description="Maximum order size in USD",
    )
    default_leverage: int = Field(
        default=1,
        ge=1,
        le=125,
        description="Default leverage for futures positions (1-125)",
    )

    def get_base_url(self) -> str:
        """Get appropriate base URL based on testnet setting."""
        if self.testnet:
            return "https://testnet.binancefuture.com"
        return "https://fapi.binance.com"


@lru_cache
def get_binance_settings() -> BinanceConfig:
    """Get cached Binance settings."""
    return BinanceConfig()
