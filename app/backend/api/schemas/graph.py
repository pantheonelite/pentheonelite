from typing import Any

from pydantic import BaseModel


class GraphNode(BaseModel):
    """Represents a node in the agent graph."""

    id: str
    type: str | None = None
    data: dict[str, Any] | None = None
    position: dict[str, Any] | None = None


class GraphEdge(BaseModel):
    """Represents an edge in the agent graph."""

    id: str
    source: str
    target: str
    type: str | None = None
    data: dict[str, Any] | None = None
