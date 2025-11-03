"""Repository for HedgeFundFlowRun operations."""

from typing import Any

from app.backend.db.models import HedgeFundFlowRun
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FlowRunRepository(AbstractSqlRepository[HedgeFundFlowRun]):
    """Repository for HedgeFundFlowRun CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HedgeFundFlowRun)

    async def create_run(
        self,
        flow_id: int,
        trading_mode: str = "one-time",
        schedule: str | None = None,
        duration: str | None = None,
        request_data: dict | None = None,
        initial_portfolio: dict | None = None,
    ) -> HedgeFundFlowRun:
        """
        Create a new flow run.

        Parameters
        ----------
        flow_id : int
            Associated flow ID.
        trading_mode : str, optional
            Trading mode, by default "one-time".
        schedule : str | None, optional
            Schedule configuration, by default None.
        duration : str | None, optional
            Run duration, by default None.
        request_data : dict | None, optional
            Request data, by default None.
        initial_portfolio : dict | None, optional
            Initial portfolio state, by default None.

        Returns
        -------
        HedgeFundFlowRun
            Created run instance.
        """
        return await self.create(
            flow_id=flow_id,
            trading_mode=trading_mode,
            schedule=schedule,
            duration=duration,
            request_data=request_data,
            initial_portfolio=initial_portfolio,
        )

    async def get_runs_by_flow_id(self, flow_id: int) -> list[HedgeFundFlowRun]:
        """
        Get all runs for a specific flow.

        Parameters
        ----------
        flow_id : int
            Flow ID to search for.

        Returns
        -------
        list[HedgeFundFlowRun]
            List of runs for the flow.
        """
        return await self.find_by(flow_id=flow_id)

    async def get_runs_by_status(self, status: str) -> list[HedgeFundFlowRun]:
        """
        Get runs by status.

        Parameters
        ----------
        status : str
            Status to filter by.

        Returns
        -------
        list[HedgeFundFlowRun]
            List of runs with the status.
        """
        return await self.find_by(status=status)

    async def get_active_runs(self) -> list[HedgeFundFlowRun]:
        """
        Get all active runs.

        Returns
        -------
        list[HedgeFundFlowRun]
            List of active runs.
        """
        stmt = select(HedgeFundFlowRun).where(HedgeFundFlowRun.status.in_(["RUNNING", "IN_PROGRESS", "STARTED"]))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_run_status(
        self,
        run_id: int,
        status: str,
        error_message: str | None = None,
        results: dict | None = None,
        final_portfolio: dict | None = None,
    ) -> HedgeFundFlowRun | None:
        """
        Update run status and related fields.

        Parameters
        ----------
        run_id : int
            Run ID to update.
        status : str
            New status.
        error_message : str | None, optional
            Error message if applicable, by default None.
        results : dict | None, optional
            Run results, by default None.
        final_portfolio : dict | None, optional
            Final portfolio state, by default None.

        Returns
        -------
        HedgeFundFlowRun | None
            Updated run if found, None otherwise.
        """
        update_data: dict[str, Any] = {"status": status}

        if error_message is not None:
            update_data["error_message"] = error_message
        if results is not None:
            update_data["results"] = results
        if final_portfolio is not None:
            update_data["final_portfolio"] = final_portfolio

        return await self.update(run_id, **update_data)

    async def get_latest_run_for_flow(self, flow_id: int) -> HedgeFundFlowRun | None:
        """
        Get the latest run for a specific flow.

        Parameters
        ----------
        flow_id : int
            Flow ID to search for.

        Returns
        -------
        HedgeFundFlowRun | None
            Latest run if found, None otherwise.
        """
        stmt = (
            select(HedgeFundFlowRun)
            .where(HedgeFundFlowRun.flow_id == flow_id)
            .order_by(HedgeFundFlowRun.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
