"""API key management endpoints."""

from app.backend.api.dependencies import UnitOfWorkDep
from app.backend.api.schemas import (
    ApiKeyBulkUpdateRequest,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeySummaryResponse,
    ApiKeyUpdateRequest,
    ErrorResponse,
)
from app.backend.api.utils.error_handling import handle_repository_errors
from app.backend.db.models import ApiKey
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@handle_repository_errors
@router.post(
    "/",
    response_model=ApiKeyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_or_update_api_key(request: ApiKeyCreateRequest, uow: UnitOfWorkDep):
    """Create a new API key or update existing one."""
    repo = uow.get_repository(ApiKey)
    api_key = await repo.create_or_update_api_key(
        provider=request.provider,
        key_value=request.key_value,
        description=request.description,
        is_active=request.is_active,
    )
    return ApiKeyResponse.model_validate(api_key)


@handle_repository_errors
@router.get(
    "/",
    response_model=list[ApiKeySummaryResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_api_keys(uow: UnitOfWorkDep, *, include_inactive: bool = False):
    """Get all API keys (without actual key values for security)."""
    repo = uow.get_repository(ApiKey)
    api_keys = await repo.get_all_api_keys(include_inactive=include_inactive)
    return [ApiKeySummaryResponse.model_validate(key) for key in api_keys]


@handle_repository_errors
@router.get(
    "/{provider}",
    response_model=ApiKeyResponse,
    responses={
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_api_key(provider: str, uow: UnitOfWorkDep):
    """Get a specific API key by provider."""
    repo = uow.get_repository(ApiKey)
    api_key = await repo.get_api_key_by_provider(provider)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyResponse.model_validate(api_key)


@handle_repository_errors
@router.put(
    "/{provider}",
    response_model=ApiKeyResponse,
    responses={
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_api_key(provider: str, request: ApiKeyUpdateRequest, uow: UnitOfWorkDep):
    """Update an existing API key."""
    repo = uow.get_repository(ApiKey)
    api_key = await repo.update_api_key(
        provider=provider,
        key_value=request.key_value,
        description=request.description,
        is_active=request.is_active,
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyResponse.model_validate(api_key)


@handle_repository_errors
@router.delete(
    "/{provider}",
    responses={
        204: {"description": "API key deleted successfully"},
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_api_key(provider: str, uow: UnitOfWorkDep):
    """Delete an API key."""
    repo = uow.get_repository(ApiKey)
    success = await repo.delete_api_key(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deleted successfully"}


@handle_repository_errors
@router.patch(
    "/{provider}/deactivate",
    response_model=ApiKeySummaryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def deactivate_api_key(provider: str, uow: UnitOfWorkDep):
    """Deactivate an API key without deleting it."""
    repo = uow.get_repository(ApiKey)
    success = await repo.deactivate_api_key(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key = await repo.get_api_key_by_provider(provider)
    return ApiKeySummaryResponse.model_validate(api_key)


@handle_repository_errors
@router.post(
    "/bulk",
    response_model=list[ApiKeyResponse],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def bulk_update_api_keys(request: ApiKeyBulkUpdateRequest, uow: UnitOfWorkDep):
    """Bulk create or update multiple API keys."""
    repo = uow.get_repository(ApiKey)
    api_keys_data = [
        {
            "provider": key.provider,
            "key_value": key.key_value,
            "description": key.description,
            "is_active": key.is_active,
        }
        for key in request.api_keys
    ]
    api_keys = await repo.bulk_create_or_update(api_keys_data)
    return [ApiKeyResponse.model_validate(key) for key in api_keys]


@handle_repository_errors
@router.patch(
    "/{provider}/last-used",
    responses={
        200: {"description": "Last used timestamp updated"},
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_last_used(provider: str, uow: UnitOfWorkDep):
    """Update the last used timestamp for an API key."""
    repo = uow.get_repository(ApiKey)
    success = await repo.update_last_used(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "Last used timestamp updated"}
