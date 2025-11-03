"""Profiling middleware."""

from typing import Any

from app.backend.config import get_api_settings
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

try:
    from pyinstrument import Profiler
except ImportError:
    Profiler: Any = None  # type: ignore[misc,no-redef]


class ProfilingMiddleware(BaseHTTPMiddleware):
    """ProfilingMiddleware class."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Get request and response information before and after processing the request.

        Parameters
        ----------
        request: Request
            Request instance
        call_next: RequestResponseEndpoint
            an awaitable Response object

        Returns
        -------
        Response
            Http Response object

        """
        settings = get_api_settings()
        profiling = request.query_params.get("profile", False)

        # Only enable profiling if explicitly requested and enabled in settings
        if getattr(settings, "profiling_enabled", False) and profiling and Profiler is not None:
            profiler = Profiler(
                interval=getattr(settings, "profiling_interval", 0.001),
                async_mode="enabled",
            )
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())

        return await call_next(request)
