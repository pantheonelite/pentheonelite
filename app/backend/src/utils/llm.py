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
    *,
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
        logger.info("Calling LLM", agent_name=agent_name, model_name=model_name, model_provider=model_provider)
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


def _unwrap_annotated(annotation: Any) -> Any:
    """Unwrap typing.Annotated to its inner type if present."""
    if hasattr(annotation, "__origin__") and annotation.__origin__ is typing.Annotated:
        return annotation.__args__[0]
    return annotation


def _resolve_union(annotation: Any) -> tuple[Any, Any | None]:
    """Resolve Union/Optional and return (resolved_type, default_if_none)."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = typing.get_args(annotation)
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            return non_none_types[0], None
        return annotation, None
    return annotation, None


def _default_for_literal(field_name: str, annotation: Any) -> Any:
    """Return default value for Literal types based on the first literal value."""
    first_value = typing.get_args(annotation)[0]
    if field_name in ["signal", "action"] and isinstance(first_value, str):
        return first_value.lower()
    if field_name in ["recommendation", "sentiment"] and isinstance(first_value, str):
        return first_value.upper()
    return first_value


def _default_for_basic_type(field_name: str, type_obj: type) -> Any:
    """Return default value for simple builtin types."""
    value: Any = None
    if type_obj is str:
        if "signal" in field_name or "action" in field_name:
            value = "hold"
        elif "reasoning" in field_name:
            value = "Error in analysis, using default"
        elif "risk_level" in field_name or "risk" in field_name:
            value = "medium"
        else:
            value = "Unknown"
    elif type_obj is float:
        value = 0.0
    elif type_obj is int:
        value = 0
    elif type_obj is bool:
        value = False
    return value


def _default_for_origin(origin: Any) -> Any:
    """Return default value for generic container origins."""
    if origin is list:
        return []
    if origin is dict:
        return {}
    if origin is tuple:
        return ()
    if origin is set:
        return set()
    return None


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
    default_values: dict[str, Any] = {}
    for field_name, field in model_class.model_fields.items():
        annotation = _unwrap_annotated(field.annotation)

        # Resolve Optional/Union
        annotation, _ = _resolve_union(annotation)
        origin = typing.get_origin(annotation)

        # Literal
        if origin is typing.Literal:
            default_values[field_name] = _default_for_literal(field_name, annotation)
            continue

        # Basic builtin types
        if isinstance(annotation, type):
            default_values[field_name] = _default_for_basic_type(field_name, annotation)
            continue

        # Generic containers
        container_default = _default_for_origin(origin)
        default_values[field_name] = container_default

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
