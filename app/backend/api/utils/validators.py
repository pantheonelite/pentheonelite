"""Validation utilities for API routers."""

from app.backend.db.models import HedgeFundFlow
from app.backend.db.uow import UnitOfWork
from fastapi import HTTPException


async def verify_flow_exists(uow: UnitOfWork, flow_id: int) -> None:
    """
    Verify that a flow exists, raising 404 if not found.

    Parameters
    ----------
    uow : UnitOfWork
        Unit of work instance
    flow_id : int
        Flow ID to verify

    Raises
    ------
    HTTPException
        If flow is not found (404)
    """
    flow_repo = uow.get_repository(HedgeFundFlow)
    flow = await flow_repo.get_flow_by_id(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
