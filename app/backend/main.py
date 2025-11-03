"""Main application entry point."""

import structlog
from app.backend.api import router as api_router
from app.backend.config import get_api_settings
from app.backend.db.session_manager import session_manager
from app.backend.utils.middlewares.profiling_middleware import ProfilingMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api_settings = get_api_settings()
logger = structlog.stdlib.get_logger(__name__)


async def lifespan(_: FastAPI):
    """Application lifespan events."""
    yield

    await session_manager.close()


app = FastAPI(
    title=api_settings.title,
    description=api_settings.description,
    version=api_settings.version,
    docs_url=None,  # Disable Swagger UI
    redoc_url=None,  # Disable ReDoc
    openapi_url=None,  # Disable OpenAPI schema endpoint
    lifespan=lifespan,
)

# Configure CORS - MUST be added first before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add custom middlewares
app.add_middleware(ProfilingMiddleware)

# Include all routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("FastAPI application starting up")
    logger.info(f"CORS origins configured: {api_settings.cors_origins}")
    logger.info("To load mock data, run: uv run python app/backend/src/cli/load_mock_data.py")
