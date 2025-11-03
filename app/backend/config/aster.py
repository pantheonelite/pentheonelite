"""Aster trading platform configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AsterConfig(BaseSettings):
    """Configuration for Aster client."""

    model_config = SettingsConfigDict(env_prefix="ASTER_", case_sensitive=False)

    # API Connection Settings
    api_key: str | None = Field(default=None, description="Aster API key")
    api_secret: str | None = Field(default=None, description="Aster API secret")
    base_url: str = Field(default="https://fapi.asterdex.com", description="Aster API base URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    show_limit_usage: bool = Field(default=False, description="Show API limit usage")
    show_header: bool = Field(default=False, description="Show response headers")

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


@lru_cache
def get_aster_settings() -> AsterConfig:
    """Get cached Aster settings."""
    return AsterConfig()
