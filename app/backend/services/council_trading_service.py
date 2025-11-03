"""Council trading service - position-based trading for councils."""

from decimal import Decimal
from typing import Literal

import structlog
from app.backend.db.repositories.council_repository import CouncilRepository
from app.backend.services.council_metrics_service import CouncilMetricsService
from app.backend.services.unified_trading_service import UnifiedTradingService
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Type aliases
Decision = Literal["BUY", "SELL", "LONG", "SHORT", "HOLD", "CLOSE"]
OrderSide = Literal["BUY", "SELL"]


class CouncilTradingService:
    """
    Service for executing position-based trades for councils.

    Handles:
    - Position-based trading (LONG/SHORT/SPOT)
    - Routes to Binance Testnet (paper) or Aster (real)
    - Multi-symbol trade execution
    - PnL tracking and metrics updates
    - Consensus execution
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the council trading service.

        Parameters
        ----------
        session : AsyncSession
            Database session for repository operations
        """
        self.session = session
        self.repo = CouncilRepository(session)
        self.metrics_service = CouncilMetricsService(session)

    async def aexecute_consensus_trade(
        self,
        council_id: int,
        consensus: dict[str, str | float | int],
    ) -> dict[str, bool | str | int | None]:
        """
        Execute position-based trade from consensus decision.

        Parameters
        ----------
        council_id : int
            Council ID
        consensus : dict
            Consensus decision with keys:
            - decision: str (BUY, SELL, LONG, SHORT, HOLD, CLOSE)
            - symbol: str
            - confidence: float
            - leverage: int (optional, for futures)

        Returns
        -------
        dict
            Trade result with keys:
            - success: bool
            - position_id or holding_id: int | None
            - order_id: int | None
            - reason: str
            - was_executed: bool
        """
        try:
            decision = str(consensus["decision"])
            symbol = str(consensus["symbol"])
            confidence = Decimal(str(consensus.get("confidence", 0.5)))
            leverage = int(consensus.get("leverage", 1)) if "leverage" in consensus else None
            agent_reasoning = consensus.get("reasoning")

            logger.info(
                "Processing consensus trade",
                council_id=council_id,
                decision=decision,
                symbol=symbol,
                confidence=float(confidence),
            )

            # Get council to determine trading type
            council = await self.repo.get_by_id(council_id)
            if not council:
                return {
                    "success": False,
                    "reason": "council_not_found",
                    "was_executed": False,
                }

            # Handle HOLD decision
            if decision == "HOLD":
                logger.info("HOLD decision - no trade executed", council_id=council_id, symbol=symbol)
                return {
                    "success": True,
                    "position_id": None,
                    "holding_id": None,
                    "order_id": None,
                    "reason": "hold_decision",
                    "was_executed": False,
                }

            # Check confidence threshold
            min_confidence = Decimal("0.5")
            if confidence < min_confidence:
                logger.warning(
                    "Confidence below threshold, skipping trade",
                    confidence=float(confidence),
                    threshold=float(min_confidence),
                )
                return {
                    "success": True,
                    "position_id": None,
                    "holding_id": None,
                    "order_id": None,
                    "reason": "low_confidence",
                    "was_executed": False,
                }

            # Create unified trading service for this council
            trading_service = UnifiedTradingService(self.session, council)

            # Map decision to order side
            side: OrderSide
            if decision in ["BUY", "LONG"]:
                side = "BUY"
            elif decision in ["SELL", "SHORT"]:
                side = "SELL"
            else:
                logger.warning("Unknown decision type", decision=decision)
                return {
                    "success": False,
                    "reason": "unknown_decision",
                    "was_executed": False,
                }

            # Calculate position size
            position_size = self._calculate_position_size(
                confidence=confidence,
                council_capital=council.available_balance or council.initial_capital,
            )

            # Execute trade
            result = await trading_service.aexecute_trade(
                symbol=symbol,
                side=side,
                position_size_usd=position_size,  # Fixed: renamed from quantity to position_size_usd
                confidence=confidence,
                agent_reasoning=str(agent_reasoning) if agent_reasoning else None,
                leverage=leverage,
            )

            # Update council metrics
            await self.metrics_service.aupdate_all_metrics(council_id)

            return {
                "success": result.get("success", False),
                "position_id": result.get("position_id"),
                "holding_id": result.get("holding_id"),
                "order_id": result.get("order_id"),
                "reason": "trade_executed" if result.get("success") else result.get("error", "unknown_error"),
                "was_executed": result.get("success", False),
            }

        except Exception as e:
            logger.exception("Failed to execute consensus trade", council_id=council_id, error=str(e))
            return {
                "success": False,
                "reason": f"error: {e!s}",
                "was_executed": False,
            }

    async def aexecute_multi_symbol_trades(
        self,
        council_id: int,
        consensuses: list[dict[str, str | float | int]],
    ) -> dict[str, list[dict]]:
        """
        Execute trades for multiple symbols.

        Parameters
        ----------
        council_id : int
            Council ID
        consensuses : list[dict]
            List of consensus decisions

        Returns
        -------
        dict
            Results with keys:
            - trades_executed: list of successful trades
            - trades_skipped: list of skipped trades
        """
        trades_executed = []
        trades_skipped = []

        for consensus in consensuses:
            result = await self.aexecute_consensus_trade(council_id, consensus)

            if result["was_executed"]:
                trades_executed.append(
                    {
                        "symbol": consensus["symbol"],
                        "decision": consensus["decision"],
                        "result": result,
                    }
                )
            else:
                trades_skipped.append(
                    {
                        "symbol": consensus["symbol"],
                        "decision": consensus["decision"],
                        "reason": result.get("reason"),
                    }
                )

        logger.info(
            "Multi-symbol trades completed",
            council_id=council_id,
            executed=len(trades_executed),
            skipped=len(trades_skipped),
        )

        return {
            "trades_executed": trades_executed,
            "trades_skipped": trades_skipped,
        }

    def _calculate_position_size(
        self,
        confidence: Decimal,
        council_capital: Decimal,
    ) -> Decimal:
        """
        Calculate position size based on confidence.

        Parameters
        ----------
        confidence : Decimal
            Agent confidence (0.0-1.0)
        council_capital : Decimal
            Available capital

        Returns
        -------
        Decimal
            Position size in base currency
        """
        # Position size = confidence * available_capital
        # This gives us a quantity that will be converted to asset quantity
        # by the trading service
        return confidence * council_capital
