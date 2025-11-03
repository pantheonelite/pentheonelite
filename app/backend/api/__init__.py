"""Public API for backend routes."""

from app.backend.api.routers import api_v1_router
from fastapi import APIRouter, status

router = APIRouter()
router.include_router(api_v1_router)


@router.get("/healthz", status_code=status.HTTP_200_OK)
def perform_healthcheck() -> dict[str, str]:
    """Lightweight readiness probe."""
    return {"healthz": "OK"}


__all__ = ["router"]
