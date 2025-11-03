"""WebSocket endpoints for real-time cryptocurrency trading."""

import json
from datetime import datetime

import structlog
from app.backend.api.schemas import StartStreamingRequest, StopStreamingRequest
from app.backend.src.agents.streaming_agent import WorkflowEngine
from app.backend.src.tools.crypto.websocket_client import MockWebSocketClient
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.stdlib.get_logger(__name__)
router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """
        Add WebSocket connection to channel.

        Parameters
        ----------
        websocket : WebSocket
            WebSocket connection
        channel : str
            Channel name
        """
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str):
        """
        Remove WebSocket connection from channel.

        Parameters
        ----------
        websocket : WebSocket
            WebSocket connection
        channel : str
            Channel name
        """
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)

    async def broadcast(self, channel: str, data: dict):
        """
        Broadcast data to all connections in channel.

        Parameters
        ----------
        channel : str
            Channel name
        data : dict
            Data to broadcast
        """
        if channel in self.active_connections:
            dead_connections = []

            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.exception("Error broadcasting to WebSocket", error=str(e))
                    dead_connections.append(connection)

            # Remove dead connections
            for connection in dead_connections:
                self.active_connections[channel].remove(connection)

    async def send_to_connection(self, websocket: WebSocket, data: dict):
        """
        Send data to a specific WebSocket connection.

        Parameters
        ----------
        websocket : WebSocket
            WebSocket connection
        data : dict
            Data to send
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.exception("Error sending to WebSocket", error=str(e))


# Instantiate WebSocket manager at module level
websocket_manager = WebSocketManager()


@router.websocket("/ws/crypto-data/{symbol}")
async def crypto_data_stream(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time crypto data.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    symbol : str
        Trading pair symbol
    """
    channel = f"crypto_data_{symbol}"
    await websocket_manager.connect(websocket, channel)

    try:
        # Subscribe to WebSocket data streams
        websocket_client = MockWebSocketClient()

        async def data_callback(data):
            await websocket_manager.send_to_connection(
                websocket,
                {
                    "type": "crypto_data",
                    "symbol": symbol,
                    "data": data.dict() if hasattr(data, "dict") else data,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Subscribe to ticker data
        await websocket_client.subscribe_ticker(symbol, "binance", data_callback)

        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                # Echo back for connection testing
                await websocket.send_json({"type": "echo", "message": message})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in crypto data stream", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, channel)


@router.websocket("/ws/agent-signals")
async def agent_signals_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent signals.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    channel = "agent_signals"
    await websocket_manager.connect(websocket, channel)

    try:
        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "subscribe_agent":
                    # Subscribe to specific agent signals
                    agent_id = data.get("agent_id")
                    if agent_id:
                        workflow_engine = WorkflowEngine()
                        workflow_engine.subscribe_agent_to_websocket(agent_id, websocket)

                elif data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in agent signals stream", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, channel)


@router.websocket("/ws/portfolio-updates")
async def portfolio_updates_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time portfolio updates.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    channel = "portfolio_updates"
    await websocket_manager.connect(websocket, channel)

    try:
        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                # Echo back for connection testing
                await websocket.send_json({"type": "echo", "message": message})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in portfolio updates stream", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, channel)


@router.websocket("/ws/workflow-control")
async def workflow_control_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time workflow control.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    channel = "workflow_control"
    await websocket_manager.connect(websocket, channel)

    try:
        workflow_engine = WorkflowEngine()

        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "start_workflow":
                    # Start a new workflow
                    request_data = data.get("data", {})
                    symbols = request_data.get("symbols", [])
                    exchanges = request_data.get("exchanges", ["binance", "coinbase"])
                    agents = request_data.get("agents", [])

                    await workflow_engine.start_workflow(symbols, agents, exchanges)

                    await websocket.send_json(
                        {
                            "type": "workflow_started",
                            "symbols": symbols,
                            "agents": [agent["name"] for agent in agents],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "stop_workflow":
                    # Stop the workflow
                    await workflow_engine.stop_workflow()

                    await websocket.send_json({"type": "workflow_stopped", "timestamp": datetime.now().isoformat()})

                elif data.get("type") == "get_status":
                    # Get workflow status
                    status = await workflow_engine.get_workflow_status()

                    await websocket.send_json(
                        {"type": "workflow_status", "status": status, "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "add_agent":
                    # Add a new agent
                    agent_data = data.get("data", {})
                    config = {
                        "name": agent_data.get("name"),
                        "description": agent_data.get("description", ""),
                        "persona": agent_data.get("persona", ""),
                    }
                    symbols = agent_data.get("symbols", [])
                    exchanges = agent_data.get("exchanges", ["binance", "coinbase"])

                    await workflow_engine.add_agent(config, symbols, exchanges)

                    await websocket.send_json(
                        {
                            "type": "agent_added",
                            "agent_id": config["name"],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "remove_agent":
                    # Remove an agent
                    agent_id = data.get("agent_id")
                    await workflow_engine.remove_agent(agent_id)

                    await websocket.send_json(
                        {"type": "agent_removed", "agent_id": agent_id, "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.exception("Error in workflow control", error=str(e))
                await websocket.send_json(
                    {"type": "error", "message": str(e), "timestamp": datetime.now().isoformat()}
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in workflow control stream", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, channel)


@router.post("/streaming/start")
async def start_streaming(request: StartStreamingRequest):
    """
    Start real-time streaming for specified symbols and agents.

    Parameters
    ----------
    request : StartStreamingRequest
        Streaming configuration request

    Returns
    -------
    dict
        Response with streaming status
    """
    try:
        workflow_engine = WorkflowEngine()

        await workflow_engine.start_workflow(
            symbols=request.symbols, agent_configs=request.agents, exchanges=request.exchanges
        )

        return {
            "status": "success",
            "message": "Streaming started",
            "symbols": request.symbols,
            "agents": [agent["name"] for agent in request.agents],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception("Error starting streaming", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.post("/streaming/stop")
async def stop_streaming(_: StopStreamingRequest | None = None):
    """
    Stop real-time streaming.

    Parameters
    ----------
    request : StopStreamingRequest
        Stop streaming request

    Returns
    -------
    dict
        Response with streaming status
    """
    try:
        workflow_engine = WorkflowEngine()
        await workflow_engine.stop_workflow()

        return {"status": "success", "message": "Streaming stopped", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.exception("Error stopping streaming", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/streaming/status")
async def get_streaming_status():
    """
    Get current streaming status.

    Returns
    -------
    dict
        Current streaming status
    """
    try:
        workflow_engine = WorkflowEngine()
        status = await workflow_engine.get_workflow_status()

        return {"status": "success", "data": status, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.exception("Error getting streaming status", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.websocket("/ws/council-trades")
async def council_trades_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time council trading updates.

    Broadcasts:
    - Council debate consensus decisions
    - Trade executions
    - PnL updates

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    channel = "council_trades"
    await websocket_manager.connect(websocket, channel)

    try:
        # Keep connection alive and respond to pings
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json(
                        {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "subscribe_council":
                    # Subscribe to specific council updates
                    council_id = data.get("council_id")
                    logger.info("Client subscribed to council", council_id=council_id)
                    await websocket.send_json(
                        {
                            "type": "subscription_confirmed",
                            "council_id": council_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    }
                )
            except Exception as e:
                logger.exception("Error in council trades stream", error=str(e))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in council trades WebSocket", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, channel)
