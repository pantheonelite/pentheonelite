"""LLM manager using classvar dict for client management."""

import json
from typing import Any, ClassVar

import structlog
from app.backend.config.llm import get_llm_settings
from pydantic import BaseModel

from .base_client import BaseLLMClient, ModelProvider
from .clients import (
    AnthropicClient,
    DeepSeekClient,
    GoogleClient,
    GroqClient,
    LiteLLMClient,
    OpenAIClient,
    OpenRouterClient,
)

logger = structlog.get_logger(__name__)


# Model catalog for API responses
AVAILABLE_MODELS = [
    {"provider": "OpenAI", "model_name": "gpt-4", "display_name": "GPT-4"},
    {"provider": "OpenAI", "model_name": "gpt-4-turbo", "display_name": "GPT-4 Turbo"},
    {"provider": "OpenAI", "model_name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo"},
    {"provider": "Anthropic", "model_name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
    {"provider": "Anthropic", "model_name": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet"},
    {"provider": "Anthropic", "model_name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku"},
    {"provider": "Groq", "model_name": "llama-3.1-70b-versatile", "display_name": "Llama 3.1 70B"},
    {"provider": "Groq", "model_name": "mixtral-8x7b-32768", "display_name": "Mixtral 8x7B"},
    {"provider": "DeepSeek", "model_name": "deepseek-chat", "display_name": "DeepSeek Chat"},
    {"provider": "Google", "model_name": "gemini-pro", "display_name": "Gemini Pro"},
    {"provider": "OpenRouter", "model_name": "openai/gpt-4", "display_name": "GPT-4 (OpenRouter)"},
    {
        "provider": "OpenRouter",
        "model_name": "deepseek/deepseek-chat-v3.1:free",
        "display_name": "DeepSeek Chat v3.1 (OpenRouter)",
    },
    {
        "provider": "OpenRouter",
        "model_name": "deepseek/deepseek-chat-v3.1",
        "display_name": "DeepSeek Chat v3.1 (OpenRouter)",
    },
]


def list_available_models() -> list[dict[str, str]]:
    """
    Get list of available language models.

    Returns
    -------
    list[dict[str, str]]
        List of model information dictionaries
    """
    return AVAILABLE_MODELS


class LLMManager:
    """LLM manager using classvar dict for client management."""

    # Classvar dict mapping providers to client classes
    _client_classes: ClassVar[dict[ModelProvider, type[BaseLLMClient]]] = {
        ModelProvider.OPENAI: OpenAIClient,
        ModelProvider.OPENROUTER: OpenRouterClient,
        ModelProvider.ANTHROPIC: AnthropicClient,
        ModelProvider.GROQ: GroqClient,
        ModelProvider.DEEPSEEK: DeepSeekClient,
        ModelProvider.GOOGLE: GoogleClient,
        ModelProvider.LITELLM: LiteLLMClient,
    }

    def __init__(self, api_keys: dict[str, str] | None = None):
        """Initialize with API keys."""
        self.api_keys = api_keys or {}
        self.llm_config = get_llm_settings()
        self._clients: dict[ModelProvider, BaseLLMClient] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize available clients by passing settings config to each client."""
        for provider, client_class in self._client_classes.items():
            # Pass the entire settings config to each client
            # Let each client extract what it needs from the config
            self._clients[provider] = client_class(self.llm_config)

    def call_llm(
        self,
        prompt: str,
        model: str,
        provider: ModelProvider,
        pydantic_model: type[BaseModel] | None = None,
        max_retries: int = 3,
        use_structured_output: bool = False,
        **_kwargs: Any,
    ) -> BaseModel | str:
        """
        Make an LLM call with optional Pydantic model parsing.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM
        model : str
            Model name to use
        provider : ModelProvider
            LLM provider
        pydantic_model : type[BaseModel] | None
            Pydantic model for structured output
        max_retries : int
            Maximum retry attempts
        use_structured_output : bool
            If True, use LangChain's with_structured_output() for guaranteed JSON

        Returns
        -------
        BaseModel | str
            Parsed response or string
        """
        client = self._clients.get(provider)
        if not client:
            raise ValueError(f"Provider {provider.value} not available. Available: {list(self._clients.keys())}")

        for attempt in range(max_retries):
            try:
                if use_structured_output and pydantic_model:
                    # Use structured output for guaranteed JSON format
                    response = client.call_with_structured_output(prompt, model, pydantic_model)
                else:
                    # Regular call with JSON parsing
                    response = client.call(prompt, model)
                    response = self._parse_response(response, pydantic_model)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %d failed: %s. Retrying...", attempt + 1, e)
                else:
                    logger.exception(
                        "All %d attempts failed - Model name: %s, model provider: %s",
                        max_retries,
                        model,
                        provider.value,
                    )
                    return self._create_default_response(pydantic_model)

        return self._create_default_response(pydantic_model)

    def _parse_response(self, response: str, model_class: type[BaseModel] | None) -> BaseModel | str:
        """Parse LLM response into Pydantic model or return string."""
        if not model_class:
            return response

        try:
            json_text = self._extract_json(response)
            data = json.loads(json_text) if json_text else json.loads(response)

            # Normalize signal/recommendation fields to uppercase for Literal validation
            if "signal" in data and isinstance(data["signal"], str):
                data["signal"] = data["signal"].upper()
            if "recommendation" in data and isinstance(data["recommendation"], str):
                data["recommendation"] = data["recommendation"].upper()
            if "sentiment" in data and isinstance(data["sentiment"], str):
                data["sentiment"] = data["sentiment"].upper()
            if "action" in data and isinstance(data["action"], str):
                data["action"] = data["action"].lower()  # action is lowercase

            return model_class(**data)
        except Exception as e:
            logger.warning("Failed to parse response as %s: %s", model_class.__name__, e)
            return self._create_default_response(model_class)

    def _extract_json(self, text: str) -> str | None:
        """
        Extract FIRST complete JSON object from text, ignoring trailing content.

        Handles:
        - Markdown code blocks with ```json
        - Raw JSON objects
        - JSON with extra text after it
        """
        # Try markdown code blocks first
        patterns = ["```json", "```"]
        for pattern in patterns:
            start = text.find(pattern)
            if start != -1:
                start += len(pattern)
                end = text.find("```", start)
                if end != -1:
                    return text[start:end].strip()

        # Find first { and matching } by counting braces
        start = text.find("{")
        if start == -1:
            return None

        # Track brace depth to find matching closing brace
        brace_count = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    # Found matching close brace - return just the JSON object
                    return text[start : i + 1]

        # No matching closing brace found
        return None

    def _create_default_response(self, model_class: type[BaseModel] | None) -> BaseModel | str:
        """Create a default response for failed parsing."""
        if not model_class:
            return "Error in analysis"

        default_values = {}
        for field_name, field in model_class.model_fields.items():
            field_type = field.annotation

            # Handle Union types
            if hasattr(field_type, "__origin__") and field_type.__origin__ is type(None).__class__:
                args = getattr(field_type, "__args__", ())
                non_none_types = [arg for arg in args if arg is not type(None)]
                field_type = non_none_types[0] if non_none_types else str

            # Set defaults based on type
            default_values[field_name] = self._get_default_value(field_name, field_type)

        return model_class(**default_values)

    def _get_default_value(self, field_name: str, field_type: Any) -> Any:
        """
        Get type-appropriate default value for a field.

        Handles Optional, Union, Literal types and returns correct type defaults.
        """
        from typing import Literal, Union, get_args, get_origin

        # Get origin type (handles Optional, Union, etc.)
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional/Union types - extract the actual type
        if origin is Union:
            # Get first non-None type
            non_none_types = [t for t in args if t is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]
                origin = get_origin(field_type)
                args = get_args(field_type)

        # Handle Literal types - return first literal value (UPPERCASE for signals)
        if origin is Literal:
            first_value = args[0] if args else "HOLD"
            # If it's a signal/recommendation, ensure uppercase
            if field_name in ["signal", "recommendation", "sentiment"] and isinstance(first_value, str):
                return first_value.upper()
            return first_value

        # Type-based defaults (check by identity, not equality)
        if field_type is float or origin is float:
            return 0.0
        if field_type is int or origin is int:
            return 0
        if field_type is bool or origin is bool:
            return False
        if field_type is list or origin is list:
            return []
        if field_type is dict or origin is dict:
            return {}

        # String fields - use semantic defaults
        if field_type is str or origin is str:
            if "signal" in field_name:
                return "hold"  # Lowercase for underscored signals
            if "recommendation" in field_name:
                return "HOLD"  # Uppercase for recommendations
            if "reasoning" in field_name:
                return "Error in analysis"
            if "sentiment" in field_name:
                return "NEUTRAL"
            if "action" in field_name:
                return "hold"
            return "Unknown"

        # Final fallback
        return 0.0  # Safe numeric default instead of string

    def get_available_providers(self) -> list[ModelProvider]:
        """Get list of available providers."""
        return list(self._clients.keys())

    def is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a provider is available."""
        return provider in self._clients
