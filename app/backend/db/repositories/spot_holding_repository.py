"""Spot holding repository."""

import structlog
from app.backend.db.models.spot_holding import SpotHolding
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class SpotHoldingRepository(AbstractSqlRepository[SpotHolding]):
    """Repository for spot holdings."""

    def __init__(self, session: AsyncSession):
        """
        Initialize spot holding repository.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        super().__init__(session, SpotHolding)

    async def find_by_symbol(
        self, council_id: int, symbol: str, platform: str, trading_mode: str
    ) -> SpotHolding | None:
        """
        Find holding by symbol.

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str
            Trading symbol
        platform : str
            Platform ("binance" | "aster")
        trading_mode : str
            Trading mode ("paper" | "real")

        Returns
        -------
        SpotHolding | None
            Found holding or None
        """
        query = select(SpotHolding).where(
            SpotHolding.council_id == council_id,
            SpotHolding.symbol == symbol,
            SpotHolding.platform == platform,
            SpotHolding.trading_mode == trading_mode,
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_active_holdings(self, council_id: int) -> list[SpotHolding]:
        """
        Find all active holdings for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[SpotHolding]
            Active holdings
        """
        query = select(SpotHolding).where(SpotHolding.council_id == council_id, SpotHolding.status == "ACTIVE")

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_all_holdings(self, council_id: int) -> list[SpotHolding]:
        """
        Find all holdings for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[SpotHolding]
            All holdings
        """
        query = (
            select(SpotHolding)
            .where(SpotHolding.council_id == council_id)
            .order_by(SpotHolding.first_acquired_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
