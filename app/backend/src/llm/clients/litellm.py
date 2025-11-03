"""LiteLLM client implementation."""

from typing import Any

import litellm
import structlog
from app.backend.src.llm.base_client import BaseLLMClient
from litellm import completion

logger = structlog.get_logger(__name__)


class LiteLLMClient(BaseLLMClient):
    """LiteLLM client for unified LLM access."""

    def __init__(self, config: Any):
        """
        Initialize LiteLLM client.

        Parameters
        ----------
        config : Any
            LLM settings configuration containing API keys and settings
        """
        super().__init__(config)

    def call(self, prompt: str, model: str) -> str:
        """
        Make a call to the LLM using LiteLLM.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM
        model : str
            The model identifier (e.g., "gpt-4", "claude-3-sonnet", "gemini-pro")

        Returns
        -------
        str
            The LLM response
        """
        if not self.config.litellm_api_key:
            raise ValueError("LiteLLM API key not configured")

        try:
            # Handle different prompt formats
            messages = self._format_messages(prompt)

            litellm.drop_params = True

            # Prepare completion parameters
            completion_params = {
                "model": model,
                "messages": messages,
                "api_key": self.config.litellm_api_key,
                "temperature": self.config.litellm_temperature,
                "max_tokens": self.config.litellm_max_tokens,
                "timeout": self.config.litellm_timeout,
            }

            # Add base URL if provided
            if self.config.litellm_base_url:
                completion_params["api_base"] = self.config.litellm_base_url

            # Make the completion call
            response = completion(**completion_params)

            # Extract the content from the response
            if hasattr(response, "choices") and response.choices:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                logger.warning("Empty response from LiteLLM")
                return "No response generated"
            logger.warning("No choices in LiteLLM response")
            return "No response generated"

        except Exception:
            logger.exception("LiteLLM call failed")
            raise

    def _format_messages(self, prompt: str) -> list[dict[str, str]]:
        """
        Format prompt into messages for LiteLLM.

        Parameters
        ----------
        prompt : str
            The input prompt

        Returns
        -------
        list[dict[str, str]]
            Formatted messages for LiteLLM
        """
        # Handle different prompt formats
        if isinstance(prompt, str):
            # Simple string prompt
            return [{"role": "user", "content": prompt}]
        if hasattr(prompt, "messages"):
            # ChatPromptTemplate format
            messages = []
            for message in prompt.messages:
                if hasattr(message, "content"):
                    role = "assistant" if message.__class__.__name__ == "AIMessage" else "user"
                    messages.append({"role": role, "content": message.content})
            return messages
        if isinstance(prompt, list):
            # Already formatted messages
            return prompt
        # Fallback to string conversion
        return [{"role": "user", "content": str(prompt)}]

    def get_available_models(self) -> list[str]:
        """
        Get list of available models through LiteLLM.

        Returns
        -------
        list[str]
            List of available model identifiers
        """
        # Common models supported by LiteLLM
        return [
            # OpenAI models
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            # Anthropic models
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            # Google models
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            # Groq models
            "llama3-8b-8192",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            # DeepSeek models
            "deepseek-chat",
            "deepseek-coder",
            # Other models via LiteLLM
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "meta-llama/Llama-2-70b-chat-hf",
        ]

    def supports_model(self, model: str) -> bool:
        """
        Check if a model is supported by LiteLLM.

        Parameters
        ----------
        model : str
            Model identifier to check

        Returns
        -------
        bool
            True if model is supported
        """
        try:
            # Try to get model info from LiteLLM
            model_info = litellm.get_model_info(model)
            return model_info is not None
        except Exception:
            # If we can't get model info, assume it's supported
            # LiteLLM will handle the error if it's not
            return True

    def get_model_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Get the cost for a model call.

        Parameters
        ----------
        model : str
            Model identifier
        input_tokens : int
            Number of input tokens
        output_tokens : int
            Number of output tokens

        Returns
        -------
        float
            Estimated cost in USD
        """
        try:
            return litellm.completion_cost(model=model, prompt_tokens=input_tokens, completion_tokens=output_tokens)
        except Exception as e:
            logger.warning("Could not calculate cost for model %s: %s", model, str(e))
            return 0.0
