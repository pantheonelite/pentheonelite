"""Flow management endpoints for hedge fund workflows."""

from typing import Annotated

from app.backend.api.dependencies import UnitOfWorkDep
from app.backend.api.schemas import (
    ErrorResponse,
    FlowCreateRequest,
    FlowResponse,
    FlowSummaryResponse,
    FlowUpdateRequest,
)
from app.backend.api.utils.error_handling import handle_repository_errors
from app.backend.db.models import HedgeFundFlow
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/flows", tags=["flows"])


@handle_repository_errors
@router.post(
    "/",
    response_model=FlowResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_flow(request: FlowCreateRequest, uow: UnitOfWorkDep):
    """Create a new hedge fund flow."""
    repo = uow.get_repository(HedgeFundFlow)
    flow = await repo.create_flow(
        name=request.name,
        description=request.description,
        nodes=request.nodes,
        edges=request.edges,
        viewport=request.viewport,
        data=request.data,
        is_template=request.is_template,
        tags=request.tags,
    )
    return FlowResponse.model_validate(flow)


@handle_repository_errors
@router.get(
    "/",
    response_model=list[FlowSummaryResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flows(
    uow: UnitOfWorkDep,
    *,
    include_templates: Annotated[bool, Query()] = True,
):
    """Get all flows (summary view)."""
    repo = uow.get_repository(HedgeFundFlow)
    flows = await repo.get_all_flows(include_templates=include_templates)
    return [FlowSummaryResponse.model_validate(flow) for flow in flows]


@handle_repository_errors
@router.get(
    "/{flow_id}",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow(flow_id: int, uow: UnitOfWorkDep):
    """Get a specific flow by ID."""
    repo = uow.get_repository(HedgeFundFlow)
    flow = await repo.get_flow_by_id(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowResponse.model_validate(flow)


@handle_repository_errors
@router.put(
    "/{flow_id}",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_flow(flow_id: int, request: FlowUpdateRequest, uow: UnitOfWorkDep):
    """Update an existing flow."""
    repo = uow.get_repository(HedgeFundFlow)
    flow = await repo.update_flow(
        flow_id=flow_id,
        name=request.name,
        description=request.description,
        nodes=request.nodes,
        edges=request.edges,
        viewport=request.viewport,
        data=request.data,
        is_template=request.is_template,
        tags=request.tags,
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowResponse.model_validate(flow)


@handle_repository_errors
@router.delete(
    "/{flow_id}",
    responses={
        204: {"description": "Flow deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_flow(flow_id: int, uow: UnitOfWorkDep):
    """Delete a flow."""
    repo = uow.get_repository(HedgeFundFlow)
    success = await repo.delete_flow(flow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"message": "Flow deleted successfully"}


@handle_repository_errors
@router.post(
    "/{flow_id}/duplicate",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def duplicate_flow(flow_id: int, uow: UnitOfWorkDep, new_name: str | None = None):
    """Create a copy of an existing flow."""
    repo = uow.get_repository(HedgeFundFlow)
    flow = await repo.duplicate_flow(flow_id, new_name=new_name)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowResponse.model_validate(flow)


@handle_repository_errors
@router.get(
    "/search/{name}",
    response_model=list[FlowSummaryResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def search_flows(name: str, uow: UnitOfWorkDep):
    """Search flows by name."""
    repo = uow.get_repository(HedgeFundFlow)
    flows = await repo.get_flows_by_name(name)
    return [FlowSummaryResponse.model_validate(flow) for flow in flows]
