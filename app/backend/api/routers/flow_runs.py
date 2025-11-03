"""Flow run management endpoints."""

from typing import Annotated

from app.backend.api.dependencies import UnitOfWorkDep
from app.backend.api.schemas import (
    ErrorResponse,
    FlowRunCreateRequest,
    FlowRunResponse,
    FlowRunSummaryResponse,
    FlowRunUpdateRequest,
)
from app.backend.api.utils.error_handling import handle_repository_errors
from app.backend.api.utils.validators import verify_flow_exists
from app.backend.db.models import HedgeFundFlowRun
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/flows/{flow_id}/runs", tags=["flow-runs"])


@handle_repository_errors
@router.post(
    "/",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_flow_run(flow_id: int, request: FlowRunCreateRequest, uow: UnitOfWorkDep):
    """Create a new flow run for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    flow_run = await run_repo.create_run(flow_id=flow_id, request_data=request.request_data)
    return FlowRunResponse.model_validate(flow_run)


@handle_repository_errors
@router.get(
    "/",
    response_model=list[FlowRunSummaryResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_runs(
    flow_id: int,
    uow: UnitOfWorkDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of runs to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of runs to skip")] = 0,
):
    """Get all runs for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    flow_runs = await run_repo.get_runs_by_flow_id(flow_id)
    # Apply pagination
    paginated_runs = flow_runs[offset : offset + limit] if limit else flow_runs[offset:]
    return [FlowRunSummaryResponse.model_validate(run) for run in paginated_runs]


@handle_repository_errors
@router.get(
    "/active",
    response_model=FlowRunResponse | None,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_active_flow_run(flow_id: int, uow: UnitOfWorkDep):
    """Get the current active (IN_PROGRESS) run for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    active_runs = await run_repo.get_active_runs()
    # Filter for this specific flow
    active_run = next((run for run in active_runs if run.flow_id == flow_id), None)
    return FlowRunResponse.model_validate(active_run) if active_run else None


@handle_repository_errors
@router.get(
    "/latest",
    response_model=FlowRunResponse | None,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_latest_flow_run(flow_id: int, uow: UnitOfWorkDep):
    """Get the most recent run for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    latest_run = await run_repo.get_latest_run_for_flow(flow_id)
    return FlowRunResponse.model_validate(latest_run) if latest_run else None


@handle_repository_errors
@router.get(
    "/{run_id}",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_run(flow_id: int, run_id: int, uow: UnitOfWorkDep):
    """Get a specific flow run by ID."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    flow_run = await run_repo.get_by_id(run_id)
    if not flow_run or flow_run.flow_id != flow_id:
        raise HTTPException(status_code=404, detail="Flow run not found")

    return FlowRunResponse.model_validate(flow_run)


@handle_repository_errors
@router.put(
    "/{run_id}",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_flow_run(flow_id: int, run_id: int, request: FlowRunUpdateRequest, uow: UnitOfWorkDep):
    """Update an existing flow run."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    # Verify the run exists and belongs to this flow
    existing_run = await run_repo.get_by_id(run_id)
    if not existing_run or existing_run.flow_id != flow_id:
        raise HTTPException(status_code=404, detail="Flow run not found")

    flow_run = await run_repo.update(
        id=run_id, status=request.status, results=request.results, error_message=request.error_message
    )

    if not flow_run:
        raise HTTPException(status_code=404, detail="Flow run not found")

    return FlowRunResponse.model_validate(flow_run)


@handle_repository_errors
@router.delete(
    "/{run_id}",
    responses={
        204: {"description": "Flow run deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_flow_run(flow_id: int, run_id: int, uow: UnitOfWorkDep):
    """Delete a flow run."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    # Verify run exists and belongs to this flow
    existing_run = await run_repo.get_by_id(run_id)
    if not existing_run or existing_run.flow_id != flow_id:
        raise HTTPException(status_code=404, detail="Flow run not found")

    success = await run_repo.delete(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flow run not found")

    return {"message": "Flow run deleted successfully"}


@handle_repository_errors
@router.delete(
    "/",
    responses={
        204: {"description": "All flow runs deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_all_flow_runs(flow_id: int, uow: UnitOfWorkDep):
    """Delete all runs for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    flow_runs = await run_repo.get_runs_by_flow_id(flow_id)
    deleted_count = 0
    for run in flow_runs:
        if await run_repo.delete(run.id):
            deleted_count += 1

    return {"message": f"Deleted {deleted_count} flow runs successfully"}


@handle_repository_errors
@router.get(
    "/count",
    responses={
        200: {"description": "Flow run count"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_run_count(flow_id: int, uow: UnitOfWorkDep):
    """Get the total count of runs for the specified flow."""
    await verify_flow_exists(uow, flow_id)

    run_repo = uow.get_repository(HedgeFundFlowRun)
    flow_runs = await run_repo.get_runs_by_flow_id(flow_id)
    return {"flow_id": flow_id, "total_runs": len(flow_runs)}
