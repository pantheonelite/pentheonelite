"""Registered API routers."""

from fastapi import APIRouter

from .api_keys import router as api_keys_router
from .aster_websocket import router as aster_websocket_router
from .councils import router as councils_router  # Unified councils API
from .flow_runs import router as flow_runs_router
from .flows import router as flows_router
from .health import router as health_router
from .hedge_fund import router as hedge_fund_router
from .language_models import router as language_models_router
from .storage import router as storage_router
from .websocket import router as websocket_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(hedge_fund_router, tags=["hedge-fund"])
api_v1_router.include_router(storage_router, tags=["storage"])
api_v1_router.include_router(flows_router, tags=["flows"])
api_v1_router.include_router(flow_runs_router, tags=["flow-runs"])
api_v1_router.include_router(language_models_router, tags=["language-models"])
api_v1_router.include_router(api_keys_router, tags=["api-keys"])
api_v1_router.include_router(councils_router, tags=["councils"])  # Unified councils API
api_v1_router.include_router(websocket_router, tags=["websocket"])
api_v1_router.include_router(aster_websocket_router, tags=["aster-websocket"])

__all__ = ["api_v1_router"]
