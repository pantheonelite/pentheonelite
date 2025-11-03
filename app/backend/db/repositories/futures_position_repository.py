"""Futures position repository."""

import structlog
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class FuturesPositionRepository(AbstractSqlRepository[FuturesPosition]):
    """Repository for futures positions."""

    def __init__(self, session: AsyncSession):
        """
        Initialize futures position repository.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        super().__init__(session, FuturesPosition)

    async def find_open_positions(self, council_id: int, symbol: str | None = None) -> list[FuturesPosition]:
        """
        Find all open positions for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str | None
            Optional symbol filter

        Returns
        -------
        list[FuturesPosition]
            Open positions
        """
        query = select(FuturesPosition).where(
            FuturesPosition.council_id == council_id, FuturesPosition.status == "OPEN"
        )

        if symbol:
            query = query.where(FuturesPosition.symbol == symbol)

        query = query.order_by(FuturesPosition.opened_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_closed_positions(self, council_id: int, limit: int = 100) -> list[FuturesPosition]:
        """
        Find closed positions for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        limit : int
            Maximum number of results

        Returns
        -------
        list[FuturesPosition]
            Closed positions
        """
        query = (
            select(FuturesPosition)
            .where(FuturesPosition.council_id == council_id, FuturesPosition.status.in_(["CLOSED", "LIQUIDATED"]))
            .order_by(FuturesPosition.closed_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_all_positions(self, council_id: int) -> list[FuturesPosition]:
        """
        Find all positions for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[FuturesPosition]
            All positions
        """
        query = (
            select(FuturesPosition)
            .where(FuturesPosition.council_id == council_id)
            .order_by(FuturesPosition.opened_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_symbol_and_side(
        self, council_id: int, symbol: str, position_side: str, status: str = "OPEN"
    ) -> FuturesPosition | None:
        """
        Find position by symbol and side.

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str
            Trading symbol
        position_side : str
            Position side ("LONG" | "SHORT" | "BOTH")
        status : str
            Position status

        Returns
        -------
        FuturesPosition | None
            Found position or None
        """
        query = select(FuturesPosition).where(
            FuturesPosition.council_id == council_id,
            FuturesPosition.symbol == symbol,
            FuturesPosition.position_side == position_side,
            FuturesPosition.status == status,
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
