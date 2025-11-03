"""Streaming and real-time workflow utilities for agents (combined module)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AgentConfig:
    """Lightweight agent configuration container."""

    name: str
    description: str = ""
    persona: str = ""


class WorkflowEngine:
    """Workflow engine for managing real-time trading workflows."""

    def __init__(self):
        self.running: bool = False
        self.agents: dict[str, dict[str, Any]] = {}
        self.symbols: list[str] = []
        self.exchanges: list[str] = []

    async def start_workflow(self, symbols: list[str], agent_configs: list[dict], exchanges: list[str]) -> None:
        """Start workflow with provided agents and symbols."""
        self.running = True
        self.symbols = symbols
        self.exchanges = exchanges
        for cfg in agent_configs:
            name = cfg.get("name") or cfg.get("agent_id") or "agent"
            self.agents[name] = cfg

    async def stop_workflow(self) -> None:
        """Stop current workflow and clear runtime state."""
        self.running = False
        self.agents.clear()
        self.symbols = []
        self.exchanges = []

    async def get_workflow_status(self) -> dict:
        """Return current workflow status."""
        return {
            "running": self.running,
            "agents": list(self.agents.keys()),
            "symbols": self.symbols,
            "exchanges": self.exchanges,
        }

    def subscribe_agent_to_websocket(self, _agent_id: str, _websocket) -> None:
        """No-op subscription placeholder for WS integration hooks."""
        return

    async def add_agent(self, config: dict, symbols: list[str], exchanges: list[str]) -> None:
        """Add an agent to the running workflow."""
        name = config.get("name") or config.get("agent_id") or "agent"
        self.agents[name] = config
        if symbols:
            self.symbols = symbols
        if exchanges:
            self.exchanges = exchanges

    async def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the running workflow."""
        self.agents.pop(agent_id, None)


class AsterStreamingAnalystAgent:
    """Real-time streaming agent for Aster DEX data analysis (minimal integration)."""

    def __init__(self, config: AgentConfig, **kwargs: Any):
        self.config = config
        self.kwargs = kwargs
        self.name = config.name
        self.running = False

    async def start_streaming(self, symbols: list[str]) -> None:
        """Start streaming for provided symbols."""
        self.running = True
        logger.info("Aster agent started", agent=self.name, symbols=symbols)

    async def stop_streaming(self, _symbols: list[str] | None = None) -> None:
        """Stop streaming (symbols optional)."""
        self.running = False
        logger.info("Aster agent stopped", agent=self.name)

    async def stream_signals_to_websocket(self, websocket) -> None:
        """Stream a minimal heartbeat signal to the websocket."""
        await websocket.send_json(
            {
                "type": "aster_agent_heartbeat",
                "agent": self.name,
                "running": self.running,
            }
        )

    async def get_aster_streaming_status(self) -> dict:
        """Return current streaming status."""
        return {"name": self.name, "running": self.running}
