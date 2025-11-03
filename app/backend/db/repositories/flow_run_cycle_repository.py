"""Repository for HedgeFundFlowRunCycle operations."""

from datetime import datetime
from typing import Any

from app.backend.db.models import HedgeFundFlowRunCycle
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FlowRunCycleRepository(AbstractSqlRepository[HedgeFundFlowRunCycle]):
    """Repository for HedgeFundFlowRunCycle CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HedgeFundFlowRunCycle)

    async def create_cycle(
        self,
        flow_run_id: int,
        cycle_number: int,
        started_at: str,
        trigger_reason: str | None = None,
        market_conditions: dict | None = None,
    ) -> HedgeFundFlowRunCycle:
        """
        Create a new flow run cycle.

        Parameters
        ----------
        flow_run_id : int
            Associated flow run ID.
        cycle_number : int
            Cycle number within the run.
        started_at : str
            ISO timestamp when cycle started.
        trigger_reason : str | None, optional
            Reason for cycle trigger, by default None.
        market_conditions : dict | None, optional
            Market conditions snapshot, by default None.

        Returns
        -------
        HedgeFundFlowRunCycle
            Created cycle instance.
        """
        return await self.create(
            flow_run_id=flow_run_id,
            cycle_number=cycle_number,
            started_at=datetime.fromisoformat(started_at),
            trigger_reason=trigger_reason,
            market_conditions=market_conditions,
        )

    async def get_cycles_by_run_id(self, flow_run_id: int) -> list[HedgeFundFlowRunCycle]:
        """
        Get all cycles for a specific flow run.

        Parameters
        ----------
        flow_run_id : int
            Flow run ID to search for.

        Returns
        -------
        list[HedgeFundFlowRunCycle]
            List of cycles for the run.
        """
        stmt = (
            select(HedgeFundFlowRunCycle)
            .where(HedgeFundFlowRunCycle.flow_run_id == flow_run_id)
            .order_by(HedgeFundFlowRunCycle.cycle_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cycles_by_status(self, status: str) -> list[HedgeFundFlowRunCycle]:
        """
        Get cycles by status.

        Parameters
        ----------
        status : str
            Status to filter by.

        Returns
        -------
        list[HedgeFundFlowRunCycle]
            List of cycles with the status.
        """
        return await self.find_by(status=status)

    async def update_cycle_results(
        self,
        cycle_id: int,
        analyst_signals: dict | None = None,
        trading_decisions: dict | None = None,
        executed_trades: dict | None = None,
        portfolio_snapshot: dict | None = None,
        performance_metrics: dict | None = None,
        status: str | None = None,
        error_message: str | None = None,
        llm_calls_count: int | None = None,
        api_calls_count: int | None = None,
        estimated_cost: str | None = None,
    ) -> HedgeFundFlowRunCycle | None:
        """
        Update cycle with analysis and trading results.

        Parameters
        ----------
        cycle_id : int
            Cycle ID to update.
        analyst_signals : dict | None, optional
            Analyst signals data, by default None.
        trading_decisions : dict | None, optional
            Trading decisions data, by default None.
        executed_trades : dict | None, optional
            Executed trades data, by default None.
        portfolio_snapshot : dict | None, optional
            Portfolio snapshot, by default None.
        performance_metrics : dict | None, optional
            Performance metrics, by default None.
        status : str | None, optional
            New status, by default None.
        error_message : str | None, optional
            Error message if applicable, by default None.
        llm_calls_count : int | None, optional
            Number of LLM calls, by default None.
        api_calls_count : int | None, optional
            Number of API calls, by default None.
        estimated_cost : str | None, optional
            Estimated cost, by default None.

        Returns
        -------
        HedgeFundFlowRunCycle | None
            Updated cycle if found, None otherwise.
        """
        update_data: dict[str, Any] = {}

        if analyst_signals is not None:
            update_data["analyst_signals"] = analyst_signals
        if trading_decisions is not None:
            update_data["trading_decisions"] = trading_decisions
        if executed_trades is not None:
            update_data["executed_trades"] = executed_trades
        if portfolio_snapshot is not None:
            update_data["portfolio_snapshot"] = portfolio_snapshot
        if performance_metrics is not None:
            update_data["performance_metrics"] = performance_metrics
        if status is not None:
            update_data["status"] = status
        if error_message is not None:
            update_data["error_message"] = error_message
        if llm_calls_count is not None:
            update_data["llm_calls_count"] = llm_calls_count
        if api_calls_count is not None:
            update_data["api_calls_count"] = api_calls_count
        if estimated_cost is not None:
            update_data["estimated_cost"] = estimated_cost

        return await self.update(cycle_id, **update_data)

    async def complete_cycle(
        self,
        cycle_id: int,
        completed_at: str,
        analyst_signals: dict | None = None,
        trading_decisions: dict | None = None,
        executed_trades: dict | None = None,
        portfolio_snapshot: dict | None = None,
        performance_metrics: dict | None = None,
    ) -> HedgeFundFlowRunCycle | None:
        """
        Complete a cycle with final results.

        Parameters
        ----------
        cycle_id : int
            Cycle ID to complete.
        completed_at : str
            ISO timestamp when cycle completed.
        analyst_signals : dict | None, optional
            Final analyst signals, by default None.
        trading_decisions : dict | None, optional
            Final trading decisions, by default None.
        executed_trades : dict | None, optional
            Final executed trades, by default None.
        portfolio_snapshot : dict | None, optional
            Final portfolio snapshot, by default None.
        performance_metrics : dict | None, optional
            Final performance metrics, by default None.

        Returns
        -------
        HedgeFundFlowRunCycle | None
            Completed cycle if found, None otherwise.
        """
        update_data: dict[str, Any] = {
            "completed_at": datetime.fromisoformat(completed_at),
            "status": "COMPLETED",
        }

        if analyst_signals is not None:
            update_data["analyst_signals"] = analyst_signals
        if trading_decisions is not None:
            update_data["trading_decisions"] = trading_decisions
        if executed_trades is not None:
            update_data["executed_trades"] = executed_trades
        if portfolio_snapshot is not None:
            update_data["portfolio_snapshot"] = portfolio_snapshot
        if performance_metrics is not None:
            update_data["performance_metrics"] = performance_metrics

        return await self.update(cycle_id, **update_data)

    async def get_latest_cycle_for_run(self, flow_run_id: int) -> HedgeFundFlowRunCycle | None:
        """
        Get the latest cycle for a specific flow run.

        Parameters
        ----------
        flow_run_id : int
            Flow run ID to search for.

        Returns
        -------
        HedgeFundFlowRunCycle | None
            Latest cycle if found, None otherwise.
        """
        stmt = (
            select(HedgeFundFlowRunCycle)
            .where(HedgeFundFlowRunCycle.flow_run_id == flow_run_id)
            .order_by(HedgeFundFlowRunCycle.cycle_number.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
