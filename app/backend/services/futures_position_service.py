"""Futures position service - manages position lifecycle."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import structlog
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Type aliases for strict typing
PositionSide = Literal["LONG", "SHORT", "BOTH"]
MarginType = Literal["ISOLATED", "CROSSED"]
Platform = Literal["binance", "aster"]
TradingMode = Literal["paper", "real"]
PositionStatus = Literal["OPEN", "CLOSED", "LIQUIDATED"]


class FuturesPositionService:
    """
    Manage futures positions with Binance/Aster terminology.

    Matches Binance Futures API response structure exactly.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize futures position service.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        self.session = session
        self.repo = FuturesPositionRepository(session)

    async def aopen_position(
        self,
        council_id: int,
        symbol: str,
        position_side: PositionSide,
        position_amt: Decimal,
        entry_price: Decimal,
        leverage: int,
        margin_type: MarginType = "CROSSED",
        platform: Platform = "binance",
        trading_mode: TradingMode = "paper",
        liquidation_price: Decimal | None = None,
        isolated_margin: Decimal | None = None,
        confidence: Decimal | None = None,
        agent_reasoning: str | None = None,
        external_position_id: str | None = None,
    ) -> FuturesPosition:
        """
        Open new futures position.

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str
            Trading symbol (e.g., "BTCUSDT")
        position_side : str
            Position side ("LONG" | "SHORT" | "BOTH")
        position_amt : Decimal
            Position amount (Binance: positionAmt)
        entry_price : Decimal
            Entry price
        leverage : int
            Leverage (1-125)
        margin_type : str
            Margin type ("ISOLATED" | "CROSSED")
        platform : str
            Trading platform ("binance" | "aster")
        trading_mode : str
            Trading mode ("paper" | "real")
        liquidation_price : Decimal | None
            Liquidation price
        isolated_margin : Decimal | None
            Isolated margin (for ISOLATED mode)
        confidence : Decimal | None
            Agent confidence (0.0-1.0)
        agent_reasoning : str | None
            Agent's reasoning for opening position
        external_position_id : str | None
            Exchange position identifier

        Returns
        -------
        FuturesPosition
            Created position
        """
        # Calculate notional value: positionAmt * price (NOT multiplied by leverage for display)
        # Binance shows notional as positionAmt * markPrice
        notional = position_amt * entry_price

        position = FuturesPosition(
            council_id=council_id,
            symbol=symbol,
            position_side=position_side,
            position_amt=position_amt,
            entry_price=entry_price,
            mark_price=entry_price,  # Initialize with entry price
            leverage=leverage,
            margin_type=margin_type,
            notional=notional,
            liquidation_price=liquidation_price,
            isolated_margin=isolated_margin,
            unrealized_profit=Decimal(0),  # Starts at 0
            platform=platform,
            trading_mode=trading_mode,
            status="OPEN",
            opened_at=datetime.now(UTC),
            confidence=confidence,
            agent_reasoning=agent_reasoning,
            external_position_id=external_position_id,
        )

        self.session.add(position)

        # Update council's last_executed_at
        from app.backend.db.repositories.council_repository import CouncilRepository

        council_repo = CouncilRepository(self.session)
        council = await council_repo.get_council_by_id(council_id)
        if council:
            council.last_executed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(position)

        logger.info(
            "Futures position opened",
            position_id=position.id,
            symbol=symbol,
            side=position_side,
            amt=float(position_amt),
            leverage=leverage,
            platform=platform,
            trading_mode=trading_mode,
        )

        return position

    async def aclose_position(
        self,
        position_id: int,
        exit_price: Decimal,
        fees: Decimal = Decimal(0),
        funding_fees: Decimal = Decimal(0),
    ) -> FuturesPosition:
        """
        Close futures position and calculate realized PnL.

        Parameters
        ----------
        position_id : int
            Position ID
        exit_price : Decimal
            Exit price
        fees : Decimal
            Trading fees paid
        funding_fees : Decimal
            Funding fees paid

        Returns
        -------
        FuturesPosition
            Closed position

        Raises
        ------
        ValueError
            If position not found or already closed
        """
        position = await self.repo.get_by_id(position_id)

        if not position or position.status != "OPEN":
            raise ValueError(f"Position {position_id} not found or already closed")

        # Calculate realized PnL (Binance logic)
        if position.position_side == "LONG":
            # Long: profit when price goes UP
            pnl = (exit_price - position.entry_price) * position.position_amt
        else:  # SHORT
            # Short: profit when price goes DOWN
            pnl = (position.entry_price - exit_price) * position.position_amt

        realized_pnl = pnl - fees - funding_fees

        position.mark_price = exit_price
        position.realized_pnl = realized_pnl
        position.fees_paid = fees
        position.funding_fees = funding_fees
        position.status = "CLOSED"
        position.closed_at = datetime.now(UTC)
        position.updated_at = datetime.now(UTC)

        # Update council's last_executed_at
        from app.backend.db.repositories.council_repository import CouncilRepository

        council_repo = CouncilRepository(self.session)
        council = await council_repo.get_council_by_id(position.council_id)
        if council:
            council.last_executed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(position)

        logger.info(
            "Futures position closed",
            position_id=position_id,
            symbol=position.symbol,
            side=position.position_side,
            realized_pnl=float(realized_pnl),
        )

        return position

    async def aupdate_mark_price(
        self,
        position_id: int,
        mark_price: Decimal,
        liquidation_price: Decimal | None = None,
    ) -> FuturesPosition:
        """
        Update position with current market data.

        Parameters
        ----------
        position_id : int
            Position ID
        mark_price : Decimal
            Current mark price
        liquidation_price : Decimal | None
            Liquidation price

        Returns
        -------
        FuturesPosition
            Updated position
        """
        position = await self.repo.get_by_id(position_id)

        if not position or position.status != "OPEN":
            return position

        # Calculate unrealized PnL (Binance: unRealizedProfit)
        if position.position_side == "LONG":
            unrealized_profit = (mark_price - position.entry_price) * position.position_amt
        else:  # SHORT
            unrealized_profit = (position.entry_price - mark_price) * position.position_amt

        # Update notional
        notional = position.position_amt * mark_price

        position.mark_price = mark_price
        position.unrealized_profit = unrealized_profit
        position.notional = notional

        if liquidation_price:
            position.liquidation_price = liquidation_price

        # Track max notional
        if not position.max_notional or notional > position.max_notional:
            position.max_notional = notional

        position.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(position)

        return position

    async def aget_open_positions(
        self,
        council_id: int,
        symbol: str | None = None,
    ) -> list[FuturesPosition]:
        """
        Get all open futures positions for council.

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
        return await self.repo.find_open_positions(council_id, symbol)

    async def aget_position_history(
        self,
        council_id: int,
        limit: int = 100,
    ) -> list[FuturesPosition]:
        """
        Get closed positions history.

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
        return await self.repo.find_closed_positions(council_id, limit)

    async def aget_all_positions(self, council_id: int) -> list[FuturesPosition]:
        """
        Get all positions for council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        list[FuturesPosition]
            All positions
        """
        return await self.repo.find_all_positions(council_id)
