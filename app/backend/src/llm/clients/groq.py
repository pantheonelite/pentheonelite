"""Groq client implementation."""

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_groq import ChatGroq


class GroqClient(BaseLLMClient):
    """Groq client implementation."""

    def call(self, prompt: str, model: str) -> str:
        """Make a call to Groq."""
        if not self.config.groq_api_key:
            raise ValueError("Groq API key not configured")

        llm = ChatGroq(model=model, groq_api_key=self.config.groq_api_key)
        return self._invoke_with_prompt(llm, prompt)
