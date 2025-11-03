"""LLM provider configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM provider settings."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore", env_file=".env", env_file_encoding="utf-8")

    # OpenAI settings
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    openai_model: str = "gpt-4-mini"

    # Anthropic settings
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Groq settings
    groq_api_key: str | None = None
    groq_model: str = "llama3-8b-8192"

    # DeepSeek settings
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"

    # Google settings
    google_api_key: str | None = None
    google_model: str = "gemini-pro"

    # OpenRouter settings
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"

    # LiteLLM settings
    litellm_api_key: str | None = None
    litellm_model: str = "gpt-4o-mini"
    litellm_base_url: str | None = None
    litellm_timeout: int = 30
    litellm_max_tokens: int = 4000
    litellm_temperature: float = 0.7

    def get_api_keys(self) -> dict[str, str]:
        """
        Get all available API keys as a dictionary.

        Returns
        -------
        dict[str, str]
            Dictionary mapping provider names to API keys
        """
        keys = {}
        if self.openai_api_key:
            keys["OPENAI_API_KEY"] = self.openai_api_key
        if self.anthropic_api_key:
            keys["ANTHROPIC_API_KEY"] = self.anthropic_api_key
        if self.groq_api_key:
            keys["GROQ_API_KEY"] = self.groq_api_key
        if self.deepseek_api_key:
            keys["DEEPSEEK_API_KEY"] = self.deepseek_api_key
        if self.google_api_key:
            keys["GOOGLE_API_KEY"] = self.google_api_key
        if self.openrouter_api_key:
            keys["OPENROUTER_API_KEY"] = self.openrouter_api_key
        if self.litellm_api_key:
            keys["LITELLM_API_KEY"] = self.litellm_api_key
        return keys


@lru_cache
def get_llm_settings() -> LLMSettings:
    """Get cached LLM settings."""
    return LLMSettings()
