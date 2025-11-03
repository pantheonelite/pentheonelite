from pydantic import BaseModel


class SaveJsonRequest(BaseModel):
    """Request model for saving JSON data."""

    filename: str
    data: dict
