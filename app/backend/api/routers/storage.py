"""Storage endpoints for file operations."""

import json
from pathlib import Path

from app.backend.api.schemas import ErrorResponse, SaveJsonRequest
from app.backend.api.utils.error_handling import handle_http_exceptions
from fastapi import APIRouter

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post(
    "/save-json",
    responses={
        200: {"description": "File saved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_http_exceptions
async def save_json_file(request: SaveJsonRequest):
    """Save JSON data to the project's /outputs directory."""
    # Create outputs directory if it doesn't exist
    project_root = Path(__file__).parent.parent.parent.parent
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Construct file path
    file_path = outputs_dir / request.filename

    # Save JSON data to file
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(request.data, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "message": f"File saved successfully to {file_path}",
        "filename": request.filename,
    }
