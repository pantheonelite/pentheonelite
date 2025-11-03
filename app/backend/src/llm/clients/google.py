"""Google client implementation."""

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_google_genai import ChatGoogleGenerativeAI


class GoogleClient(BaseLLMClient):
    """Google client implementation."""

    def call(self, prompt: str, model: str) -> str:
        """Make a call to Google."""
        if not self.config.google_api_key:
            raise ValueError("Google API key not configured")

        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.config.google_api_key,
        )
        return self._invoke_with_prompt(llm, prompt)
