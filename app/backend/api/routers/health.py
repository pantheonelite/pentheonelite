"""Health check and system status endpoints."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def root():
    """Root endpoint returning API welcome message."""
    return {"message": "Welcome to AI Hedge Fund API"}


@router.get("/ping")
async def ping():
    """Server-Sent Events ping endpoint for connection testing."""

    async def event_generator():
        """Generate SSE ping events."""
        for i in range(5):
            data = {"ping": f"ping {i + 1}/5", "timestamp": i + 1}
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
