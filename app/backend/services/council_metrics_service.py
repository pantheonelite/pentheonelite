"""Council metrics service - calculates performance statistics."""

from datetime import UTC, datetime
from decimal import Decimal

import structlog
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository
from app.backend.db.repositories.spot_holding_repository import SpotHoldingRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class CouncilMetricsService:
    """
    Calculate and update all council metrics.

    Metrics displayed:
    - Total Account Value
    - Available Balance
    - Total Margin Used
    - Total Unrealized Profit
    - Total Realized PnL
    - Net PnL
    - Total Fees
    - Average Leverage
    - Average Confidence
    - Biggest Win/Loss
    - Hold Time Statistics (Long/Short/Flat %)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize council metrics service.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        self.session = session
        self.council_repo = CouncilRepository(session)
        self.futures_repo = FuturesPositionRepository(session)
        self.spot_repo = SpotHoldingRepository(session)

    async def aupdate_all_metrics(self, council_id: int) -> None:
        """
        Update all council metrics.

        Parameters
        ----------
        council_id : int
            Council ID
        """
        council = await self.council_repo.get_by_id(council_id)

        if not council:
            logger.warning("Council not found", council_id=council_id)
            return

        if council.trading_type == "futures":
            await self._update_futures_metrics(council_id)
        else:
            await self._update_spot_metrics(council_id)

    async def _update_futures_metrics(self, council_id: int) -> None:
        """
        Update metrics for futures trading council.

        Parameters
        ----------
        council_id : int
            Council ID
        """
        council = await self.council_repo.get_by_id(council_id)
        positions = await self.futures_repo.find_all_positions(council_id)
        open_positions = [p for p in positions if p.status == "OPEN"]
        closed_positions = [p for p in positions if p.status == "CLOSED"]

        # Total unrealized profit (match Binance field name)
        total_unrealized_profit = sum(p.unrealized_profit or Decimal(0) for p in open_positions)

        # Total realized PnL
        total_realized_pnl = sum(p.realized_pnl or Decimal(0) for p in closed_positions)

        # Fees
        total_fees = sum((p.fees_paid or Decimal(0)) for p in positions)
        total_funding_fees = sum((p.funding_fees or Decimal(0)) for p in positions)

        # Net PnL (realized - fees)
        net_pnl = total_realized_pnl - total_fees

        # Margin (for CROSSED mode, margin is calculated from account)
        # For ISOLATED mode, sum isolated_margin
        total_margin_used = sum(p.isolated_margin or Decimal(0) for p in open_positions)

        # Account value = initial_capital + realized_pnl + unrealized_profit - fees
        total_account_value = council.initial_capital + total_realized_pnl + total_unrealized_profit - total_fees

        # Available balance (simplified: account_value - margin_used)
        available_balance = max(Decimal(0), total_account_value - total_margin_used)
        used_balance = total_margin_used

        # Trading Statistics
        avg_leverage = self._calculate_average_leverage(positions)
        avg_confidence = self._calculate_average_confidence(positions)
        biggest_win = max((p.realized_pnl or Decimal(0) for p in closed_positions), default=Decimal(0))
        biggest_loss = min((p.realized_pnl or Decimal(0) for p in closed_positions), default=Decimal(0))

        # Hold time statistics
        hold_stats = await self._calculate_hold_time_stats(positions)

        # Update council
        council.total_account_value = total_account_value
        council.available_balance = available_balance
        council.used_balance = used_balance
        council.total_margin_used = total_margin_used
        council.total_unrealized_profit = total_unrealized_profit
        council.total_realized_pnl = total_realized_pnl
        council.net_pnl = net_pnl
        council.total_fees = total_fees
        council.total_funding_fees = total_funding_fees
        council.open_futures_count = len(open_positions)
        council.closed_futures_count = len(closed_positions)
        council.average_leverage = avg_leverage
        council.average_confidence = avg_confidence
        council.biggest_win = biggest_win
        council.biggest_loss = biggest_loss
        council.long_hold_pct = hold_stats["long_pct"]
        council.short_hold_pct = hold_stats["short_pct"]
        council.flat_hold_pct = hold_stats["flat_pct"]

        # Update legacy fields for backwards compatibility
        council.current_capital = total_account_value
        council.total_pnl = total_realized_pnl + total_unrealized_profit
        council.total_pnl_percentage = (
            ((total_realized_pnl + total_unrealized_profit) / council.initial_capital * 100)
            if council.initial_capital > 0
            else Decimal(0)
        )
        council.total_trades = len(closed_positions)

        # Calculate win rate
        if closed_positions:
            winning_trades = sum(1 for p in closed_positions if (p.realized_pnl or Decimal(0)) > 0)
            council.win_rate = Decimal(winning_trades) / Decimal(len(closed_positions)) * 100
        else:
            council.win_rate = Decimal(0)

        # Update last_executed_at when metrics are recalculated (only if not already set by position service)
        if not council.last_executed_at:
            council.last_executed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(council)

        logger.info(
            "Futures metrics updated",
            council_id=council_id,
            account_value=float(total_account_value),
            unrealized_profit=float(total_unrealized_profit),
            realized_pnl=float(total_realized_pnl),
            open_positions=len(open_positions),
        )

    async def _update_spot_metrics(self, council_id: int) -> None:
        """
        Update metrics for spot trading council.

        Parameters
        ----------
        council_id : int
            Council ID
        """
        council = await self.council_repo.get_by_id(council_id)
        holdings = await self.spot_repo.find_all_holdings(council_id)
        active_holdings = [h for h in holdings if h.status == "ACTIVE"]

        # Total unrealized PnL from holdings
        total_unrealized_pnl = sum(h.unrealized_pnl or Decimal(0) for h in active_holdings)

        # Total invested
        total_invested = sum(h.total_cost or Decimal(0) for h in active_holdings)

        # Account value = cash + holdings value
        # For spot, cash = initial_capital - total_invested + realized_pnl
        # Simplified: initial_capital + unrealized_pnl
        total_account_value = council.initial_capital + total_unrealized_pnl

        # Update council
        council.total_account_value = total_account_value
        council.available_balance = council.initial_capital - total_invested
        council.total_unrealized_profit = total_unrealized_pnl
        council.active_spot_holdings = len(active_holdings)

        # Legacy fields
        council.current_capital = total_account_value
        council.total_pnl = total_unrealized_pnl
        council.total_pnl_percentage = (
            (total_unrealized_pnl / council.initial_capital * 100) if council.initial_capital > 0 else Decimal(0)
        )

        await self.session.commit()
        await self.session.refresh(council)

        logger.info(
            "Spot metrics updated",
            council_id=council_id,
            account_value=float(total_account_value),
            unrealized_pnl=float(total_unrealized_pnl),
            active_holdings=len(active_holdings),
        )

    def _calculate_average_leverage(self, positions: list[FuturesPosition]) -> Decimal:
        """
        Calculate average leverage across all positions.

        Parameters
        ----------
        positions : list
            List of futures positions

        Returns
        -------
        Decimal
            Average leverage
        """
        if not positions:
            return Decimal(0)

        total_leverage = sum(p.leverage for p in positions)
        return Decimal(total_leverage) / Decimal(len(positions))

    def _calculate_average_confidence(self, positions: list[FuturesPosition]) -> Decimal:
        """
        Calculate average confidence across all positions.

        Parameters
        ----------
        positions : list
            List of futures positions

        Returns
        -------
        Decimal
            Average confidence
        """
        positions_with_confidence = [p for p in positions if p.confidence is not None]

        if not positions_with_confidence:
            return Decimal(0)

        total_confidence = sum(p.confidence for p in positions_with_confidence)
        return total_confidence / Decimal(len(positions_with_confidence))

    async def _calculate_hold_time_stats(self, positions: list) -> dict[str, Decimal]:
        """
        Calculate hold time statistics (Long/Short/Flat percentages).

        Parameters
        ----------
        council_id : int
            Council ID
        positions : list
            List of futures positions

        Returns
        -------
        dict[str, Decimal]
            Hold time statistics with keys:
            - long_pct: Percentage of time in LONG positions
            - short_pct: Percentage of time in SHORT positions
            - flat_pct: Percentage of time with no positions
        """
        if not positions:
            return {
                "long_pct": Decimal(0),
                "short_pct": Decimal(0),
                "flat_pct": Decimal(100),
            }

        # Calculate total time from first position to now
        first_opened = min(p.opened_at for p in positions)
        total_time = (datetime.now(UTC) - first_opened).total_seconds()

        if total_time == 0:
            return {
                "long_pct": Decimal(0),
                "short_pct": Decimal(0),
                "flat_pct": Decimal(100),
            }

        # Calculate time in each position type
        long_time = Decimal(0)
        short_time = Decimal(0)

        for position in positions:
            # Calculate how long position was held
            if position.closed_at:
                hold_duration = (position.closed_at - position.opened_at).total_seconds()
            else:  # Still open
                hold_duration = (datetime.now(UTC) - position.opened_at).total_seconds()

            if position.position_side == "LONG":
                long_time += Decimal(hold_duration)
            elif position.position_side == "SHORT":
                short_time += Decimal(hold_duration)

        # Calculate percentages
        total_time_decimal = Decimal(total_time)
        long_pct = (long_time / total_time_decimal * 100) if total_time_decimal > 0 else Decimal(0)
        short_pct = (short_time / total_time_decimal * 100) if total_time_decimal > 0 else Decimal(0)
        flat_pct = 100 - long_pct - short_pct

        return {
            "long_pct": long_pct,
            "short_pct": short_pct,
            "flat_pct": max(Decimal(0), flat_pct),  # Ensure non-negative
        }
