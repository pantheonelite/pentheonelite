"""Refactored base agent configuration - STUB IMPLEMENTATION.

TODO: This is a stub implementation to fix import errors.
      Proper implementation needed for production use.
"""

from typing import Any

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """
    Base configuration for agents.

    This is a stub implementation. Extend as needed.
    """

    agent_id: str
    agent_name: str
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    additional_params: dict[str, Any] | None = None

    class Config:
        """Pydantic configuration."""

        extra = "allow"
