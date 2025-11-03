import asyncio
import contextlib

import structlog
from app.backend.api.dependencies import UnitOfWorkDep
from app.backend.api.events import CompleteEvent, ErrorEvent, ProgressUpdateEvent, StartEvent
from app.backend.api.schemas import (
    BacktestDayResult,
    BacktestPerformanceMetrics,
    BacktestRequest,
    ErrorResponse,
    HedgeFundRequest,
)
from app.backend.db.models import ApiKey
from app.backend.services.crypto_backtest_service import CryptoBacktestService
from app.backend.services.graph import GraphService
from app.backend.src.main import run_crypto_hedge_fund
from app.backend.src.utils.analysts import get_crypto_analyst_nodes
from app.backend.src.utils.progress import get_progress
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/hedge-fund")


@router.post(
    path="/run",
    responses={
        200: {"description": "Successful response with streaming updates"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def run(request_data: HedgeFundRequest, request: Request, uow: UnitOfWorkDep):
    """Run a crypto hedge fund simulation with real-time streaming updates."""
    try:
        # Hydrate API keys from database if not provided
        if not request_data.api_keys:
            repo = uow.get_repository(ApiKey)
            api_keys = await repo.get_all_api_keys(include_inactive=False)
            request_data.api_keys = {k.provider: k.key_value for k in api_keys}

        # Create the crypto portfolio
        portfolio = {
            "cash": request_data.initial_cash,
            "positions": {
                symbol: {
                    "amount": 0.0,
                    "cost_basis": 0.0,
                }
                for symbol in request_data.tickers
            },
            "realized_gains": dict.fromkeys(request_data.tickers, 0.0),
        }

        # Use GraphService to create workflow from graph structure
        graph_service = GraphService()
        graph = graph_service.create_graph(
            graph_nodes=request_data.graph_nodes,
            graph_edges=request_data.graph_edges if hasattr(request_data, "graph_edges") else [],
        )
        graph = graph.compile()

        # Log a test progress update for debugging
        progress_tracker = get_progress()
        progress_tracker.update_status("system", None, "Preparing hedge fund run")

        # Convert model_provider to string if it's an enum
        model_provider = request_data.model_provider
        if hasattr(model_provider, "value"):
            model_provider = model_provider.value

        # Function to detect client disconnection
        async def wait_for_disconnect():
            """Wait for client disconnect and return True when it happens."""
            try:
                while True:
                    message = await request.receive()
                    if message["type"] == "http.disconnect":
                        return True
            except Exception:
                return True

        # Set up streaming response
        async def event_generator():
            # Queue for progress updates
            progress_queue = asyncio.Queue()
            run_task = None
            disconnect_task = None

            # Simple handler to add updates to the queue
            def progress_handler(agent_name, ticker, status, analysis, timestamp):
                event = ProgressUpdateEvent(
                    agent=agent_name, ticker=ticker, status=status, timestamp=timestamp, analysis=analysis
                )
                progress_queue.put_nowait(event)

            # Register our handler with the progress tracker
            progress_tracker.register_handler(progress_handler)

            try:
                # Start the crypto hedge fund execution in a background task
                run_task = asyncio.create_task(
                    run_crypto_hedge_fund(
                        symbols=request_data.tickers,
                        start_date=request_data.start_date,
                        end_date=request_data.end_date,
                        portfolio=portfolio,
                        selected_analysts=request_data.graph_nodes,
                        model_name=request_data.model_name,
                        model_provider=model_provider,
                    )
                )

                # Start the disconnect detection task
                disconnect_task = asyncio.create_task(wait_for_disconnect())

                # Send initial message
                yield StartEvent().to_sse()

                # Stream progress updates until run_task completes or client disconnects
                while not run_task.done():
                    # Check if client disconnected
                    if disconnect_task.done():
                        logger.info(
                            "Client disconnected, cancelling hedge fund execution",
                            endpoint="hedge_fund/run",
                        )
                        run_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await run_task
                        return

                    # Either get a progress update or wait a bit
                    try:
                        event = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                        yield event.to_sse()
                    except TimeoutError:
                        # Just continue the loop
                        pass

                # Get the final result
                try:
                    result = await run_task
                except asyncio.CancelledError:
                    logger.info("Hedge fund task was cancelled", endpoint="hedge_fund/run")
                    return

                if not result or not result.get("messages"):
                    yield ErrorEvent(message="Failed to generate hedge fund decisions").to_sse()
                    return

                # Send the final result
                graph_service = GraphService()
                final_data = CompleteEvent(
                    data={
                        "decisions": graph_service.parse_hedge_fund_response(result.get("messages", [])[-1].content),
                        "analyst_signals": result.get("data", {}).get("analyst_signals", {}),
                        "risk_signals": result.get("data", {}).get("risk_signals", {}),
                        "current_prices": result.get("data", {}).get("current_prices", {}),
                    }
                )
                yield final_data.to_sse()

            except asyncio.CancelledError:
                logger.info("Hedge fund event generator cancelled", endpoint="hedge_fund/run")
                return
            finally:
                # Clean up
                progress_tracker.unregister_handler(progress_handler)
                if run_task and not run_task.done():
                    run_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await run_task
                if disconnect_task and not disconnect_task.done():
                    disconnect_task.cancel()

        # Return a streaming response
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {e!s}") from e


@router.post(
    path="/backtest",
    responses={
        200: {"description": "Successful response with streaming backtest updates"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def backtest(request_data: BacktestRequest, request: Request, uow: UnitOfWorkDep):
    """Run a continuous backtest over a time period with streaming updates."""
    try:
        # Hydrate API keys from database if not provided
        if not request_data.api_keys:
            repo = uow.get_repository(ApiKey)
            api_keys = await repo.get_all_api_keys(include_inactive=False)
            request_data.api_keys = {k.provider: k.key_value for k in api_keys}

        # Convert model_provider to string if it's an enum
        model_provider = request_data.model_provider
        if hasattr(model_provider, "value"):
            model_provider = model_provider.value

        # Create crypto backtest service using the new refactored system
        backtest_service = CryptoBacktestService(
            symbols=request_data.tickers,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            initial_capital=request_data.initial_capital,
            model_name=request_data.model_name,
            model_provider=model_provider,
            selected_analysts=request_data.graph_nodes,
        )

        # Function to detect client disconnection
        async def wait_for_disconnect():
            """Wait for client disconnect and return True when it happens."""
            try:
                while True:
                    message = await request.receive()
                    if message["type"] == "http.disconnect":
                        return True
            except Exception:
                return True

        # Set up streaming response
        async def event_generator():
            progress_queue = asyncio.Queue()
            backtest_task = None
            disconnect_task = None

            # Global progress handler to capture individual agent updates during backtest
            def progress_handler(agent_name, ticker, status, analysis, timestamp):
                event = ProgressUpdateEvent(
                    agent=agent_name, ticker=ticker, status=status, timestamp=timestamp, analysis=analysis
                )
                progress_queue.put_nowait(event)

            # Progress callback to handle backtest-specific updates
            def progress_callback(update):
                if update["type"] == "progress":
                    current_date = update["current_date"]
                    current_step = update["current_step"]
                    total_dates = update["total_dates"]
                    event = ProgressUpdateEvent(
                        agent="backtest",
                        ticker=None,
                        status=f"Processing {current_date} ({current_step}/{total_dates})",
                        timestamp=None,
                        analysis=None,
                    )
                    progress_queue.put_nowait(event)
                elif update["type"] == "backtest_result":
                    # Convert day result to a streaming event
                    backtest_result = BacktestDayResult(**update["data"])

                    # Send the full day result data as JSON in the analysis field
                    import json

                    analysis_data = json.dumps(update["data"])

                    portfolio_value = backtest_result.portfolio_value
                    event = ProgressUpdateEvent(
                        agent="backtest",
                        ticker=None,
                        status=f"Completed {backtest_result.date} - Portfolio: ${portfolio_value:,.2f}",
                        timestamp=None,
                        analysis=analysis_data,
                    )
                    progress_queue.put_nowait(event)

            # Register our handler with the progress tracker to capture agent updates
            progress_tracker = get_progress()
            progress_tracker.register_handler(progress_handler)

            try:
                # Start the backtest in a background task
                backtest_task = asyncio.create_task(
                    backtest_service.arun_backtest(progress_callback=progress_callback)
                )

                # Start the disconnect detection task
                disconnect_task = asyncio.create_task(wait_for_disconnect())

                # Send initial message
                yield StartEvent().to_sse()

                # Stream progress updates until backtest_task completes or client disconnects
                while not backtest_task.done():
                    # Check if client disconnected
                    if disconnect_task.done():
                        logger.info(
                            "Client disconnected, cancelling backtest execution",
                            endpoint="hedge_fund/backtest",
                        )
                        backtest_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await backtest_task
                        return

                    # Either get a progress update or wait a bit
                    try:
                        event = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                        yield event.to_sse()
                    except TimeoutError:
                        # Just continue the loop
                        pass

                # Get the final result
                try:
                    result = await backtest_task
                except asyncio.CancelledError:
                    logger.info("Backtest task was cancelled", endpoint="hedge_fund/backtest")
                    return

                if not result:
                    yield ErrorEvent(message="Failed to complete backtest").to_sse()
                    return

                # Send the final result
                performance_metrics = BacktestPerformanceMetrics(**result["performance_metrics"])
                final_data = CompleteEvent(
                    data={
                        "performance_metrics": performance_metrics.model_dump(),
                        "final_portfolio": result["final_portfolio"],
                        "total_days": len(result["results"]),
                    }
                )
                yield final_data.to_sse()

            except asyncio.CancelledError:
                logger.info("Backtest event generator cancelled", endpoint="hedge_fund/backtest")
                return
            finally:
                # Clean up
                progress_tracker.unregister_handler(progress_handler)
                if backtest_task and not backtest_task.done():
                    backtest_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await backtest_task
                if disconnect_task and not disconnect_task.done():
                    disconnect_task.cancel()

        # Return a streaming response
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while processing the backtest request: {e!s}"
        ) from e


@router.get(
    path="/agents",
    responses={
        200: {"description": "List of available crypto agents"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_agents():
    """Get the list of available crypto agents."""
    try:
        analyst_nodes = get_crypto_analyst_nodes()
        agents = [{"key": key, "name": name} for key, (name, _) in analyst_nodes.items()]
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {e!s}") from e
