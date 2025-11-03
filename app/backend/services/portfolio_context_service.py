"""Portfolio context service - builds comprehensive portfolio state for agent decision-making."""

from decimal import Decimal

import structlog
from app.backend.db.models.council import Council
from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class PortfolioContextService:
    """
    Build portfolio context for agent decision-making.

    Fetches and normalizes position data from database, calculates risk metrics,
    and provides comprehensive portfolio state for agents to make informed trading decisions.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize portfolio context service.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        self.session = session
        self.futures_repo = FuturesPositionRepository(session)

    async def aget_portfolio_context(
        self,
        council: Council,
        symbols: list[str],  # noqa: ARG002
    ) -> dict:
        """
        Fetch and build comprehensive portfolio context for agents.

        Parameters
        ----------
        council : Council
            Council object with capital information
        symbols : list[str]
            Trading symbols to include in context

        Returns
        -------
        dict
            Portfolio context with normalized positions and risk metrics
        """
        try:
            # Fetch open futures positions
            futures_positions = await self.futures_repo.find_open_positions(council.id)

            # Build positions dictionary with normalized sides
            positions = {}
            total_notional = Decimal(0)
            total_unrealized_pnl = Decimal(0)
            total_margin_used = Decimal(0)

            for pos in futures_positions:
                # Normalize position side from "BOTH" to "LONG"/"SHORT"
                normalized_side = self._normalize_position_side(pos)

                # Calculate position metrics
                position_amt_abs = abs(pos.position_amt)
                notional = position_amt_abs * pos.entry_price * pos.leverage if pos.entry_price else Decimal(0)
                margin_used = notional / pos.leverage if pos.leverage else notional

                positions[pos.symbol] = {
                    "side": normalized_side,
                    "position_amt": float(position_amt_abs),
                    "entry_price": float(pos.entry_price),
                    "current_price": float(pos.mark_price or pos.entry_price),
                    "mark_price": float(pos.mark_price or pos.entry_price),
                    "unrealized_pnl": float(pos.unrealized_profit or 0),
                    "leverage": pos.leverage,
                    "notional": float(notional),
                    "liquidation_price": float(pos.liquidation_price) if pos.liquidation_price else None,
                    "margin_used": float(margin_used),
                    "opened_at": pos.opened_at.isoformat() if pos.opened_at else None,
                }

                total_notional += notional
                total_unrealized_pnl += pos.unrealized_profit or Decimal(0)
                total_margin_used += margin_used

            # Calculate portfolio metrics
            available_balance = council.available_balance or council.initial_capital
            total_value = available_balance + total_unrealized_pnl
            margin_usage_ratio = float(total_margin_used / available_balance) if available_balance > 0 else 0

            # Assess liquidation risk
            liquidation_risk = self._assess_liquidation_risk(positions)

            portfolio_context = {
                "council_id": council.id,
                "initial_capital": float(council.initial_capital),
                "available_balance": float(available_balance),
                "total_value": float(total_value),
                "unrealized_pnl": float(total_unrealized_pnl),
                "positions": positions,
                "total_positions": len(positions),
                "total_notional": float(total_notional),
                "margin_usage_ratio": margin_usage_ratio,
                "liquidation_risk": liquidation_risk,
            }

            logger.info(
                "Portfolio context built",
                council_id=council.id,
                total_positions=len(positions),
                total_value=float(total_value),
                unrealized_pnl=float(total_unrealized_pnl),
            )
        except Exception as e:
            logger.exception("Failed to build portfolio context", council_id=council.id, error=str(e))
            # Return minimal portfolio context on error
            return {
                "council_id": council.id,
                "initial_capital": float(council.initial_capital),
                "available_balance": float(council.available_balance or council.initial_capital),
                "total_value": float(council.available_balance or council.initial_capital),
                "unrealized_pnl": 0.0,
                "positions": {},
                "total_positions": 0,
                "total_notional": 0.0,
                "margin_usage_ratio": 0.0,
                "liquidation_risk": "unknown",
            }
        else:
            return portfolio_context

    def _normalize_position_side(self, position) -> str:
        """
        Normalize position side from "BOTH" to "LONG"/"SHORT".

        Parameters
        ----------
        position : FuturesPosition
            Position object from database

        Returns
        -------
        str
            Normalized position side ("LONG" or "SHORT")
        """
        if position.position_side == "BOTH":
            # For Binance one-way mode, determine side from position_amt sign
            return "LONG" if position.position_amt > 0 else "SHORT"
        return position.position_side

    def _assess_liquidation_risk(self, positions: dict) -> str:
        """
        Assess overall liquidation risk across all positions.

        Parameters
        ----------
        positions : dict
            Dictionary of positions with liquidation prices

        Returns
        -------
        str
            Risk level: "low", "medium", "high", or "critical"
        """
        if not positions:
            return "low"

        risk_count = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for pos in positions.values():
            liquidation_price = pos.get("liquidation_price")
            current_price = pos.get("current_price")
            side = pos.get("side")

            if not liquidation_price or not current_price:
                continue

            # Calculate distance to liquidation
            if side == "LONG":
                distance_pct = ((current_price - liquidation_price) / current_price) * 100
            else:  # SHORT
                distance_pct = ((liquidation_price - current_price) / current_price) * 100

            # Classify risk
            if distance_pct < 5:
                risk_count["critical"] += 1
            elif distance_pct < 10:
                risk_count["high"] += 1
            elif distance_pct < 20:
                risk_count["medium"] += 1
            else:
                risk_count["low"] += 1

        # Determine overall risk
        if risk_count["critical"] > 0:
            return "critical"
        if risk_count["high"] > 0:
            return "high"
        if risk_count["medium"] > 0:
            return "medium"
        return "low"
