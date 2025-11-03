"""Twitter/X API configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class TwitterSettings(BaseSettings):
    """Twitter API configuration settings."""

    x_consumer_key: str = Field(default="", description="Twitter API consumer key")
    x_consumer_secret: str = Field(default="", description="Twitter API consumer secret")
    x_access_token: str = Field(default="", description="Twitter API access token")
    x_access_token_secret: str = Field(default="", description="Twitter API access token secret")
    x_bearer_token: str = Field(default="", description="Twitter API bearer token")
    wait_on_rate_limit: bool = Field(default=False, description="Wait when rate limits are reached")
    include_post_metrics: bool = Field(default=True, description="Include post metrics in results")


def get_twitter_settings() -> TwitterSettings | None:
    """
    Get Twitter API settings.

    Returns
    -------
    TwitterSettings | None
        Twitter API configuration or None if not configured
    """
    return TwitterSettings()
