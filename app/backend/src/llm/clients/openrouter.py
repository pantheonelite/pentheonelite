"""OpenRouter client implementation using LangChain structured output patterns."""

from typing import Any

from app.backend.src.llm.base_client import BaseLLMClient
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


class OpenRouterClient(BaseLLMClient):
    """
    OpenRouter client implementation.

    Follows LangChain best practices for structured output:
    https://docs.langchain.com/oss/python/langchain/structured-output
    """

    def call(self, prompt: str, model: str) -> str:
        """Make a call to OpenRouter."""
        if not self.config.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        llm = ChatOpenAI(
            model=model, openai_api_key=self.config.openrouter_api_key, openai_api_base="https://openrouter.ai/api/v1"
        )
        return self._invoke_with_prompt(llm, prompt)

    def call_with_structured_output(self, prompt: str, model: str, pydantic_model: Any) -> Any:
        """
        Make a call with structured output using LangChain's with_structured_output().

        This follows the LangChain pattern for guaranteed JSON format responses:
        https://docs.langchain.com/oss/python/langchain/structured-output

        The method uses:
        - ProviderStrategy for models with native structured output support (OpenAI)
        - ToolStrategy fallback for other models via artificial tool calling

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
            Instance of the Pydantic model with guaranteed JSON format
        """
        if not self.config.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        # Create base LLM
        llm = ChatOpenAI(
            model=model, openai_api_key=self.config.openrouter_api_key, openai_api_base="https://openrouter.ai/api/v1"
        )

        # Use with_structured_output for guaranteed JSON format
        # LangChain automatically selects ProviderStrategy or ToolStrategy
        structured_llm = llm.with_structured_output(pydantic_model)

        # Invoke with the prompt
        if hasattr(prompt, "messages"):
            # It's a ChatPromptValue, use it directly
            response = structured_llm.invoke(prompt)
        else:
            # It's a string, wrap in HumanMessage
            response = structured_llm.invoke([HumanMessage(content=str(prompt))])

        return response
