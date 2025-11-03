"""Base LLM client class."""

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GROQ = "Groq"
    DEEPSEEK = "DeepSeek"
    GOOGLE = "Google"
    OPENROUTER = "OpenRouter"
    LITELLM = "LiteLLM"


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: Any):
        """Initialize with settings config."""
        self.config = config

    @abstractmethod
    def call(self, prompt: str, model: str) -> str:
        """Make a call to the LLM."""

    def call_with_structured_output(self, prompt: str, model: str, pydantic_model: Any) -> Any:
        """
        Make a call to the LLM with structured output (guaranteed JSON format).

        Uses LangChain's with_structured_output() to ensure the response is properly formatted.
        This method should be overridden by specific clients that support structured output.

        Parameters
        ----------
        prompt : str
            The prompt to send
        model : str
            Model name
        pydantic_model : Any
            Pydantic model class for structured output

        Returns
        -------
        Any
            Instance of the Pydantic model
        """
        # Default implementation: call regular method and try to parse
        response = self.call(prompt, model)
        try:
            data = json.loads(response)
            return pydantic_model(**data)
        except Exception:
            # If parsing fails, return a default instance
            return pydantic_model()

    def _invoke_with_prompt(self, llm, prompt: Any) -> str:
        """Helper method to invoke LLM with proper prompt handling."""
        if hasattr(prompt, "messages"):
            # It's a ChatPromptValue, use it directly
            response = llm.invoke(prompt)
        else:
            # It's a string, wrap in HumanMessage
            response = llm.invoke([HumanMessage(content=str(prompt))])
        return response.content
