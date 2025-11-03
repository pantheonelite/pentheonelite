from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    """Request to create or update an API key."""

    provider: str = Field(..., min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)
    description: str | None = None
    is_active: bool = True


class ApiKeyUpdateRequest(BaseModel):
    """Request to update an existing API key."""

    key_value: str | None = Field(None, min_length=1)
    description: str | None = None
    is_active: bool | None = None


class ApiKeyResponse(BaseModel):
    """Complete API key response."""

    id: int
    provider: str
    key_value: str
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    last_used: datetime | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ApiKeySummaryResponse(BaseModel):
    """API key response without the actual key value."""

    id: int
    provider: str
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    last_used: datetime | None
    has_key: bool = True


class ApiKeyBulkUpdateRequest(BaseModel):
    """Request to update multiple API keys at once."""

    api_keys: list[ApiKeyCreateRequest]
