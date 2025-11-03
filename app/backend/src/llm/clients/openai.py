"""OpenAI client implementation."""

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_openai import ChatOpenAI


class OpenAIClient(BaseLLMClient):
    """OpenAI client implementation."""

    def call(self, prompt: str, model: str) -> str:
        """Make a call to OpenAI."""
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        llm = ChatOpenAI(
            model=model,
            openai_api_key=self.config.openai_api_key,
            openai_api_base=self.config.openai_api_base or "https://api.openai.com/v1",
        )
        return self._invoke_with_prompt(llm, prompt)
