"""Simplified LLM helper functions."""

import typing
from typing import Any, cast

import structlog
from app.backend.config.llm import get_llm_settings
from app.backend.src.graph.state import CryptoAgentState
from app.backend.src.llm import LLMManager, ModelProvider
from dotenv import load_dotenv
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


def call_llm_with_retry(
    prompt: str,
    pydantic_model: type[BaseModel],
    agent_name: str | None = None,
    state: CryptoAgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
    use_structured_output: bool = False,
    **kwargs: Any,
) -> BaseModel:
    """
    Makes an LLM call with retry logic and structured output support.

    Follows LangChain structured output patterns:
    https://docs.langchain.com/oss/python/langchain/structured-output

    When use_structured_output=True, this uses LangChain's with_structured_output()
    which automatically selects:
    - ProviderStrategy: For models with native structured output (OpenAI, Grok)
    - ToolStrategy: For other models via artificial tool calling

    Parameters
    ----------
    prompt : str
        The prompt to send to the LLM
    pydantic_model : type[BaseModel]
        The Pydantic model class to structure the output.
        Supports: Pydantic models, dataclasses, TypedDict, JSON Schema
    agent_name : str | None
        Optional name of the agent for progress updates and model config extraction
    state : CryptoAgentState | None
        Optional state object to extract agent-specific model configuration
    max_retries : int
        Maximum number of retries (default: 3)
    default_factory : callable | None
        Optional factory function to create default response on failure
    use_structured_output : bool
        If True, use LangChain's with_structured_output() for guaranteed JSON format.
        This provides:
        - Automatic schema validation
        - Error handling with retry logic
        - Native provider support when available
        Default: False (uses manual JSON parsing)
    **kwargs : Any
        Additional parameters for the LLM call

    Returns
    -------
    BaseModel
        An instance of the specified Pydantic model with validated fields
    """
    # Extract model configuration from state
    model_name, model_provider_str = (
        get_agent_model_config(state, agent_name) if state else ("openai/gpt-4o-mini", "OPENROUTER")
    )

    try:
        # Try to match the provider string to enum
        model_provider = ModelProvider[model_provider_str.upper()]
    except KeyError:
        model_provider = ModelProvider.OPENROUTER

    # Create LLM manager with API keys
    manager = create_llm_manager()

    try:
        logger.info(f"Calling LLM for agent {agent_name}", model_name=model_name, model_provider=model_provider)
        result = manager.call_llm(
            prompt=prompt,
            model=model_name,
            provider=model_provider,
            pydantic_model=pydantic_model,
            max_retries=max_retries,
            use_structured_output=use_structured_output,
            **kwargs,
        )
        # Cast to BaseModel as documented return type
        return cast("BaseModel", result)
    except Exception:
        logger.exception("LLM call failed")
        if default_factory:
            return default_factory()
        return create_default_response(pydantic_model)


def create_default_response(model_class: type[BaseModel]) -> BaseModel:
    """
    Creates a safe default response based on the model's fields.

    Parameters
    ----------
    model_class : type[BaseModel]
        The Pydantic model class

    Returns
    -------
    BaseModel
        Default response instance
    """
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        annotation = field.annotation

        # Handle Annotated types (extract the inner type)
        if hasattr(annotation, "__origin__") and annotation.__origin__ is typing.Annotated:
            inner_type = annotation.__args__[0]
            annotation = inner_type

        # Handle Union types (Optional[X] is Union[X, None])
        origin = typing.get_origin(annotation)
        if origin is typing.Union:
            # Get the first non-None type
            args = typing.get_args(annotation)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                annotation = non_none_types[0]
                # Re-get origin/args after extraction
                origin = typing.get_origin(annotation)
            else:
                default_values[field_name] = None
                continue

        # Handle Literal types first (before basic types)
        if origin is typing.Literal:
            first_value = typing.get_args(annotation)[0]
            # Normalize signal values to lowercase for models expecting lowercase
            if field_name in ["signal", "action"] and isinstance(first_value, str):
                default_values[field_name] = first_value.lower()
            elif field_name in ["recommendation", "sentiment"] and isinstance(first_value, str):
                default_values[field_name] = first_value.upper()
            else:
                default_values[field_name] = first_value
            continue

        # Handle basic types
        if isinstance(annotation, type):
            if annotation is str:
                if "signal" in field_name or "action" in field_name:
                    default_values[field_name] = "hold"
                elif "reasoning" in field_name:
                    default_values[field_name] = "Error in analysis, using default"
                elif "risk_level" in field_name or "risk" in field_name:
                    default_values[field_name] = "medium"
                else:
                    default_values[field_name] = "Unknown"
            elif annotation is float:
                default_values[field_name] = 0.0
            elif annotation is int:
                default_values[field_name] = 0
            elif annotation is bool:
                default_values[field_name] = False
            else:
                default_values[field_name] = None
            continue

        # Handle generic types (list, dict, etc.)
        if origin is list:
            default_values[field_name] = []
        elif origin is dict:
            default_values[field_name] = {}
        elif origin is tuple:
            default_values[field_name] = ()
        elif origin is set:
            default_values[field_name] = set()
        else:
            # Final fallback - use None for optional fields
            default_values[field_name] = None

    return model_class(**default_values)


def create_llm_manager() -> LLMManager:
    """Create an LLM manager with API keys from settings."""
    load_dotenv()
    llm_config = get_llm_settings()
    return LLMManager(llm_config.get_api_keys())


def get_agent_model_config(state: CryptoAgentState, agent_name: str) -> tuple[str, str]:
    """Get model configuration for a specific agent from the state."""
    # Note: agent_name parameter is kept for future extensibility
    _ = agent_name  # Suppress unused parameter warning
    model_name = state.get("model_name")
    model_provider = state.get("model_provider")
    if not model_name or not model_provider:
        raise ValueError("Model name and provider must be specified in the agent state.")

    # Convert enum to string if necessary
    if hasattr(model_provider, "value"):
        model_provider = model_provider.value
    elif isinstance(model_provider, str) and model_provider.upper() == "OPENAI":
        model_provider = "OpenAI"

    return model_name, model_provider
