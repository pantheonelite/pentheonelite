"""Anthropic client implementation."""

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_anthropic import ChatAnthropic


class AnthropicClient(BaseLLMClient):
    """Anthropic client implementation."""

    def call(self, prompt: str, model: str) -> str:
        """Make a call to Anthropic."""
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        llm = ChatAnthropic(model=model, anthropic_api_key=self.config.anthropic_api_key)
        return self._invoke_with_prompt(llm, prompt)
