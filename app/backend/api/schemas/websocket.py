from typing import Any

from pydantic import BaseModel


class StartStreamingRequest(BaseModel):
    """Request model for starting streaming."""

    symbols: list[str]
    exchanges: list[str] | None = None
    agents: list[dict[str, Any]]


class StopStreamingRequest(BaseModel):
    """Request model for stopping streaming."""

    symbols: list[str] | None = None


class StartAsterStreamingRequest(BaseModel):
    """Request model for starting Aster streaming."""

    symbols: list[str]
    agents: list[dict[str, Any]]
    api_key: str | None = None
    api_secret: str | None = None


class StopAsterStreamingRequest(BaseModel):
    """Request model for stopping Aster streaming."""

    symbols: list[str] | None = None
