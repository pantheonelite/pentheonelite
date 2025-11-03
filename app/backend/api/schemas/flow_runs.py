from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class FlowRunStatus(str, Enum):
    """Status of a flow run."""

    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class FlowRunCreateRequest(BaseModel):
    """Request to create a new flow run."""

    request_data: dict[str, Any] | None = None


class FlowRunUpdateRequest(BaseModel):
    """Request to update an existing flow run."""

    status: FlowRunStatus | None = None
    results: dict[str, Any] | None = None
    error_message: str | None = None


class FlowRunResponse(BaseModel):
    """Complete flow run response."""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    updated_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    request_data: dict[str, Any] | None
    results: dict[str, Any] | None
    error_message: str | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FlowRunSummaryResponse(BaseModel):
    """Lightweight flow run response for listing."""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
