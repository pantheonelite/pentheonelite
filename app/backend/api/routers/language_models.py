"""Language model endpoints for listing available models and providers."""

from app.backend.api.schemas import ErrorResponse
from app.backend.api.utils.error_handling import handle_http_exceptions
from app.backend.src.llm.manager import list_available_models
from fastapi import APIRouter

router = APIRouter(prefix="/language-models", tags=["language-models"])


@router.get(
    "/",
    responses={
        200: {"description": "List of available language models"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_http_exceptions
async def get_language_models():
    """Get the list of available cloud-based language models."""
    models = list_available_models()
    return {"models": models}


@router.get(
    "/providers",
    responses={
        200: {"description": "List of available model providers"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_http_exceptions
async def get_language_model_providers():
    """Get the list of available model providers with their models grouped."""
    models = list_available_models()

    # Group models by provider
    providers = {}
    for model in models:
        provider_name = model["provider"]
        if provider_name not in providers:
            providers[provider_name] = {"name": provider_name, "models": []}
        providers[provider_name]["models"].append(
            {"display_name": model["display_name"], "model_name": model["model_name"]}
        )

    return {"providers": list(providers.values())}
