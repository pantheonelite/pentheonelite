from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response model."""

    message: str
    error: str | None = None
