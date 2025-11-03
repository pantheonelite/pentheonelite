"""Spot holding service - manages spot asset holdings."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import structlog
from app.backend.db.models.spot_holding import SpotHolding
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.repositories.spot_holding_repository import SpotHoldingRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Type aliases for strict typing
Platform = Literal["binance", "aster"]
TradingMode = Literal["paper", "real"]
HoldingStatus = Literal["ACTIVE", "CLOSED"]


class SpotHoldingService:
    """
    Manage spot holdings (simple buy/sell without leverage).

    Matches Binance Spot API structure.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize spot holding service.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        self.session = session
        self.repo = SpotHoldingRepository(session)

    async def aupdate_holding(
        self,
        council_id: int,
        symbol: str,
        base_asset: str,
        quote_asset: str,
        quantity_delta: Decimal,
        price: Decimal,
        platform: Platform = "binance",
        trading_mode: TradingMode = "paper",
    ) -> SpotHolding:
        """
        Update spot holding (buy adds, sell reduces).

        This matches how Binance tracks spot balances.

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str
            Trading symbol
        base_asset : str
            Base asset (e.g., "BTC")
        quote_asset : str
            Quote asset (e.g., "USDT")
        quantity_delta : Decimal
            Quantity change (+ for buy, - for sell)
        price : Decimal
            Trade price
        platform : str
            Platform ("binance" | "aster")
        trading_mode : str
            Trading mode ("paper" | "real")

        Returns
        -------
        SpotHolding
            Updated or created holding

        Raises
        ------
        ValueError
            If trying to sell more than owned
        """
        # Find existing holding
        holding = await self.repo.find_by_symbol(council_id, symbol, platform, trading_mode)

        if not holding:
            # Create new holding
            holding = SpotHolding(
                council_id=council_id,
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                free=Decimal(0),
                locked=Decimal(0),
                total=Decimal(0),
                average_cost=Decimal(0),
                total_cost=Decimal(0),
                platform=platform,
                trading_mode=trading_mode,
                status="ACTIVE",
                first_acquired_at=datetime.now(UTC),
            )
            self.session.add(holding)

        # Update quantities
        old_total = holding.total
        new_total = old_total + quantity_delta

        if new_total < 0:
            raise ValueError(f"Cannot sell more than owned: {symbol}. Owned: {old_total}, Selling: {-quantity_delta}")

        # Update average cost (weighted average)
        if quantity_delta > 0:  # BUY
            old_cost = holding.total_cost
            new_cost = quantity_delta * price
            holding.total_cost = old_cost + new_cost
            holding.average_cost = holding.total_cost / new_total if new_total > 0 else Decimal(0)
        else:  # SELL
            # Average cost stays the same when selling
            pass

        holding.free = new_total
        holding.total = new_total
        holding.last_updated_at = datetime.now(UTC)
        holding.updated_at = datetime.now(UTC)

        # Close if sold everything
        if new_total == 0:
            holding.status = "CLOSED"
            holding.closed_at = datetime.now(UTC)

        # Update council's last_executed_at when holding changes
        council_repo = CouncilRepository(self.session)
        council = await council_repo.get_council_by_id(council_id)
        if council:
            council.last_executed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(holding)

        logger.info(
            "Spot holding updated",
            holding_id=holding.id,
            symbol=symbol,
            delta=float(quantity_delta),
            new_total=float(new_total),
            status=holding.status,
        )

        return holding

    async def aupdate_current_value(
        self,
        holding_id: int,
        current_price: Decimal,
    ) -> SpotHolding:
        """
        Update holding's current value and unrealized PnL.

        Parameters
        ----------
        holding_id : int
            Holding ID
        current_price : Decimal
            Current market price

        Returns
        -------
        SpotHolding
            Updated holding
        """
        holding = await self.repo.get_by_id(holding_id)

        if not holding or holding.status != "ACTIVE":
            return holding

        current_value = holding.total * current_price
        unrealized_pnl = current_value - holding.total_cost

        holding.current_price = current_price
        holding.current_value = current_value
        holding.unrealized_pnl = unrealized_pnl
        holding.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(holding)

        return holding

    async def aget_active_holdings(self, council_id: int) -> list[SpotHolding]:
        """
        Get all active holdings for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[SpotHolding]
            Active holdings
        """
        return await self.repo.find_active_holdings(council_id)

    async def aget_all_holdings(self, council_id: int) -> list[SpotHolding]:
        """
        Get all holdings for a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[SpotHolding]
            All holdings
        """
        return await self.repo.find_all_holdings(council_id)
