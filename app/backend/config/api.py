"""API application settings."""

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    model_config = SettingsConfigDict(env_prefix="API_", case_sensitive=False)

    title: str = "AI Hedge Fund API"
    description: str = "Backend API for AI Hedge Fund"
    version: str = "0.1.0"
    debug: bool = False
    json_log_enabled: bool = False
    docs_url: str = "/docs"
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://pantheonelite.ai,https://www.pantheonelite.ai,http://pantheonelite.ai,http://www.pantheonelite.ai",
        alias="API_CORS_ORIGINS",
    )
    frontend_url: str | None = Field(default=None, alias="FRONTEND_URL")

    @computed_field
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        # If explicit FRONTEND_URL is provided, lock CORS to that single origin
        if self.frontend_url:
            return [self.frontend_url.strip()]
        if not self.cors_origins_str:
            return [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://pantheonelite.ai",
                "https://www.pantheonelite.ai",
                "http://pantheonelite.ai",
                "http://www.pantheonelite.ai",
            ]
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]


@lru_cache
def get_api_settings() -> ApiSettings:
    """Return cached API settings loaded from environment variables."""
    return ApiSettings()
