"""DeepSeek client implementation."""

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_openai import ChatOpenAI


class DeepSeekClient(BaseLLMClient):
    """DeepSeek client implementation."""

    def call(self, prompt: str, model: str) -> str:
        """Make a call to DeepSeek."""
        if not self.config.deepseek_api_key:
            raise ValueError("DeepSeek API key not configured")

        llm = ChatOpenAI(
            model=model, openai_api_key=self.config.deepseek_api_key, openai_api_base="https://api.deepseek.com"
        )
        return self._invoke_with_prompt(llm, prompt)
