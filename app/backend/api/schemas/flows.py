from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FlowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    viewport: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    is_template: bool = False
    tags: list[str] | None = None


class FlowUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    viewport: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    is_template: bool | None = None
    tags: list[str] | None = None


class FlowResponse(BaseModel):
    id: int
    name: str
    description: str | None
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    viewport: dict[str, Any] | None
    data: dict[str, Any] | None
    is_template: bool
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FlowSummaryResponse(BaseModel):
    """Lightweight flow response without nodes/edges for listing."""

    id: int
    name: str
    description: str | None
    is_template: bool
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None
