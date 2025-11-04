"""Aster DEX WebSocket endpoints for real-time cryptocurrency trading."""

import json
from datetime import datetime

import structlog
from app.backend.api.schemas import StartAsterStreamingRequest, StopAsterStreamingRequest
from app.backend.client.aster.websocket import MockAsterWebSocketClient
from app.backend.src.agents.streaming_agent import AsterStreamingAnalystAgent
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.stdlib.get_logger(__name__)
router = APIRouter()


class AsterWebSocketManager:
    """Manages Aster DEX WebSocket connections and broadcasting."""

    def __init__(self):
        """Initialize Aster WebSocket manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.aster_agents: dict[str, AsterStreamingAnalystAgent] = {}

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

        logger.info("Aster WebSocket connected", channel=channel)

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

        logger.info("Aster WebSocket disconnected", channel=channel)

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
                    logger.exception("Error broadcasting to Aster WebSocket", error=str(e))
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
            logger.exception("Error sending to Aster WebSocket", error=str(e))


@router.websocket("/ws/aster/crypto-data/{symbol}")
async def aster_crypto_data_stream(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time Aster DEX crypto data.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    symbol : str
        Trading pair symbol (e.g., BTCUSDT)
    """
    aster_websocket_manager = AsterWebSocketManager()
    channel = f"aster_crypto_data_{symbol}"
    await aster_websocket_manager.connect(websocket, channel)

    try:
        # Subscribe to Aster WebSocket data streams
        aster_client = MockAsterWebSocketClient()

        async def ticker_callback(data):
            await aster_websocket_manager.send_to_connection(
                websocket,
                {
                    "type": "aster_ticker",
                    "symbol": symbol,
                    "data": data.dict() if hasattr(data, "dict") else data,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        async def orderbook_callback(data):
            await aster_websocket_manager.send_to_connection(
                websocket,
                {
                    "type": "aster_orderbook",
                    "symbol": symbol,
                    "data": data.dict() if hasattr(data, "dict") else data,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        async def trades_callback(data):
            await aster_websocket_manager.send_to_connection(
                websocket,
                {
                    "type": "aster_trades",
                    "symbol": symbol,
                    "data": data.dict() if hasattr(data, "dict") else data,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Subscribe to Aster streams
        await aster_client.subscribe_ticker(symbol, ticker_callback)
        await aster_client.subscribe_orderbook(symbol, orderbook_callback)
        await aster_client.subscribe_trades(symbol, trades_callback)

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
        logger.exception("Error in Aster crypto data stream", error=str(e))
    finally:
        await aster_websocket_manager.disconnect(websocket, channel)


@router.websocket("/ws/aster/agent-signals")
async def aster_agent_signals_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Aster DEX agent signals.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    aster_websocket_manager = AsterWebSocketManager()
    channel = "aster_agent_signals"
    await aster_websocket_manager.connect(websocket, channel)

    try:
        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "subscribe_aster_agent":
                    # Subscribe to specific Aster agent signals
                    agent_id = data.get("agent_id")
                    if agent_id and agent_id in aster_websocket_manager.aster_agents:
                        agent = aster_websocket_manager.aster_agents[agent_id]
                        await agent.stream_signals_to_websocket(websocket)

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
        logger.exception("Error in Aster agent signals stream", error=str(e))
    finally:
        await aster_websocket_manager.disconnect(websocket, channel)


@router.websocket("/ws/aster/trading-control")
async def aster_trading_control_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Aster DEX trading control.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection
    """
    aster_websocket_manager = AsterWebSocketManager()
    channel = "aster_trading_control"
    await aster_websocket_manager.connect(websocket, channel)

    try:
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "start_aster_agents":
                    # Start Aster streaming agents
                    request_data = data.get("data", {})
                    symbols = request_data.get("symbols", [])
                    agents = request_data.get("agents", [])
                    api_key = request_data.get("api_key")
                    api_secret = request_data.get("api_secret")

                    for agent_config in agents:
                        config = {
                            "name": agent_config["name"],
                            "description": agent_config.get("description", ""),
                            "persona": agent_config.get("persona", ""),
                        }

                        agent = AsterStreamingAnalystAgent(
                            config,
                            analysis_threshold=agent_config.get("analysis_threshold", 0.01),
                            min_analysis_interval=agent_config.get("min_analysis_interval", 30),
                            api_key=api_key,
                            api_secret=api_secret,
                        )

                        aster_websocket_manager.aster_agents[config["name"]] = agent
                        await agent.start_streaming(symbols)

                        # Subscribe agent signals to WebSocket
                        await agent.stream_signals_to_websocket(websocket)

                    await websocket.send_json(
                        {
                            "type": "aster_agents_started",
                            "symbols": symbols,
                            "agents": [agent["name"] for agent in agents],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "stop_aster_agents":
                    # Stop Aster streaming agents
                    for agent in aster_websocket_manager.aster_agents.values():
                        await agent.stop_streaming()

                    aster_websocket_manager.aster_agents.clear()

                    await websocket.send_json(
                        {"type": "aster_agents_stopped", "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "get_aster_status":
                    # Get Aster agents status
                    status = {}
                    for agent_id, agent in aster_websocket_manager.aster_agents.items():
                        status[agent_id] = await agent.get_aster_streaming_status()

                    await websocket.send_json(
                        {"type": "aster_status", "status": status, "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "add_aster_agent":
                    # Add a new Aster agent
                    agent_data = data.get("data", {})
                    config = {
                        "name": agent_data.get("name"),
                        "description": agent_data.get("description", ""),
                        "persona": agent_data.get("persona", ""),
                    }
                    symbols = agent_data.get("symbols", [])
                    api_key = agent_data.get("api_key")
                    api_secret = agent_data.get("api_secret")

                    agent = AsterStreamingAnalystAgent(config, api_key=api_key, api_secret=api_secret)

                    aster_websocket_manager.aster_agents[config["name"]] = agent
                    await agent.start_streaming(symbols)
                    await agent.stream_signals_to_websocket(websocket)

                    await websocket.send_json(
                        {
                            "type": "aster_agent_added",
                            "agent_id": config["name"],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "remove_aster_agent":
                    # Remove an Aster agent
                    agent_id = data.get("agent_id")
                    if agent_id in aster_websocket_manager.aster_agents:
                        await aster_websocket_manager.aster_agents[agent_id].stop_streaming()
                        del aster_websocket_manager.aster_agents[agent_id]

                        await websocket.send_json(
                            {
                                "type": "aster_agent_removed",
                                "agent_id": agent_id,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                elif data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.exception("Error in Aster trading control", error=str(e))
                await websocket.send_json(
                    {"type": "error", "message": str(e), "timestamp": datetime.now().isoformat()}
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Error in Aster trading control stream", error=str(e))
    finally:
        await aster_websocket_manager.disconnect(websocket, channel)


@router.post("/aster/start-streaming")
async def start_aster_streaming(request: StartAsterStreamingRequest):
    """
    Start real-time streaming for specified symbols and agents on Aster DEX.

    Parameters
    ----------
    request : StartAsterStreamingRequest
        Aster streaming configuration request

    Returns
    -------
    dict
        Response with Aster streaming status
    """
    aster_websocket_manager = AsterWebSocketManager()
    try:
        for agent_config in request.agents:
            config = {
                "name": agent_config["name"],
                "description": agent_config.get("description", ""),
                "persona": agent_config.get("persona", ""),
            }

            agent = AsterStreamingAnalystAgent(
                config,
                analysis_threshold=agent_config.get("analysis_threshold", 0.01),
                min_analysis_interval=agent_config.get("min_analysis_interval", 30),
                api_key=request.api_key,
                api_secret=request.api_secret,
            )

            aster_websocket_manager.aster_agents[config["name"]] = agent
            await agent.start_streaming(request.symbols)

        return {
            "status": "success",
            "message": "Aster streaming started",
            "symbols": request.symbols,
            "agents": [agent["name"] for agent in request.agents],
            "exchange": "aster",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception("Error starting Aster streaming", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.post("/aster/stop-streaming")
async def stop_aster_streaming(request: StopAsterStreamingRequest):
    """
    Stop real-time Aster DEX streaming.

    Parameters
    ----------
    request : StopAsterStreamingRequest
        Stop Aster streaming request

    Returns
    -------
    dict
        Response with Aster streaming status
    """
    aster_websocket_manager = AsterWebSocketManager()
    try:
        for agent in aster_websocket_manager.aster_agents.values():
            await agent.stop_streaming(request.symbols)

        if request.symbols is None:
            aster_websocket_manager.aster_agents.clear()

        return {"status": "success", "message": "Aster streaming stopped", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.exception("Error stopping Aster streaming", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/aster/streaming-status")
async def get_aster_streaming_status():
    """
    Get current Aster DEX streaming status.

    Returns
    -------
    dict
        Current Aster streaming status
    """
    aster_websocket_manager = AsterWebSocketManager()
    try:
        status = {}
        for agent_id, agent in aster_websocket_manager.aster_agents.items():
            status[agent_id] = await agent.get_aster_streaming_status()

        return {
            "status": "success",
            "data": {"agents": status, "total_agents": len(aster_websocket_manager.aster_agents), "exchange": "aster"},
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception("Error getting Aster streaming status", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/aster/supported-symbols")
async def get_aster_supported_symbols():
    """
    Get supported trading symbols on Aster DEX.

    Returns
    -------
    dict
        List of supported symbols
    """
    try:
        # This would typically come from Aster DEX API
        # For now, return common symbols
        common_symbols = [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "DOTUSDT",
            "DOGEUSDT",
            "AVAXUSDT",
            "MATICUSDT",
            "TRUMPUSDT",
        ]

        return {
            "status": "success",
            "data": {"symbols": common_symbols, "exchange": "aster"},
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception("Error getting Aster supported symbols", error=str(e))
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}
