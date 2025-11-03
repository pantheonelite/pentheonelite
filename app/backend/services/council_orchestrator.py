"""Council orchestrator service - coordinates trading agent debates and execution."""

import asyncio
from datetime import UTC, datetime

import structlog
from app.backend.db.models.council import Council, CouncilRun
from app.backend.db.session_manager import session_manager
from app.backend.db.uow import UnitOfWork
from app.backend.services.council_trading_service import CouncilTradingService
from app.backend.services.debate_service import DebateService
from app.backend.services.graph import GraphService
from app.backend.services.portfolio_context_service import PortfolioContextService

logger = structlog.get_logger(__name__)


class CouncilOrchestrator:
    """
    Orchestrates trading council operations with position-based trading.

    Manages the complete lifecycle of council trading:
    - Loading active councils
    - Running debate cycles via GraphService
    - Determining consensus from agent signals
    - Executing position-based trades (uses council.trading_mode per council)
    - Calculating and updating PnL
    - Broadcasting events via WebSocket
    """

    def __init__(
        self,
        *,
        symbols_override: list[str] | None = None,
        schedule_interval_seconds: int = 14400,
    ):
        """
        Initialize the council orchestrator.

        Parameters
        ----------
        symbols_override : list[str] | None
            Override trading symbols for all councils. If None, uses default symbols.
        schedule_interval_seconds : int
            Interval between council cycles in seconds. Default: 14400 (4 hours)
        """
        self.graph_service = GraphService()
        self.symbols_override = symbols_override

        # Council settings
        self.schedule_interval = schedule_interval_seconds
        self.consensus_threshold = 0.6  # 60% agreement needed for trades

        # Track running councils
        self.running_councils: dict[int, bool] = {}
        self.websocket_manager = None  # Set externally

        logger.info("Council orchestrator initialized")

        if symbols_override:
            logger.info("Symbol override enabled", symbols=", ".join(symbols_override))

    async def start(self, council_ids: list[int] | None = None) -> None:
        """
        Start the orchestrator daemon.

        Parameters
        ----------
        council_ids : list[int] | None
            Specific council IDs to run. If None, runs all active system councils.
        """
        logger.info(
            "🚀 Starting Council Orchestrator Daemon",
            council_ids=council_ids,
            schedule_interval_hours=self.schedule_interval / 3600,
        )

        try:
            # Use scoped=False to avoid disposing the connection pool
            async with session_manager.session(scoped=False) as session, UnitOfWork(session) as uow:
                # Load system councils
                logger.info("Loading councils from database...")
                if council_ids:
                    councils = []
                    for cid in council_ids:
                        logger.debug("Looking for council ID", council_id=cid)
                        repo = uow.get_repository(Council)
                        council = await repo.get_council_by_id(cid)
                        if council:
                            councils.append(council)
                            logger.info(
                                "✓ Found council",
                                name=council.name,
                                council_id=council.id,
                                trading_mode=council.trading_mode,
                                trading_type=council.trading_type,
                            )
                        else:
                            logger.warning("✗ Council not found", council_id=cid)
                else:
                    # Load all active system councils
                    repo = uow.get_repository(Council)
                    councils = await repo.get_system_councils()
                    logger.info("Loaded active system councils", count=len(councils))

                if not councils:
                    logger.warning("No councils to run!")
                    return

                logger.info(
                    "Loaded system councils",
                    count=len(councils),
                    councils=[c.name for c in councils],
                )

                # Start council tasks with continuous loops
                tasks = []
                for council in councils:
                    if council.id is not None:
                        task = asyncio.create_task(self._run_council_loop(council.id, council.name))
                        tasks.append(task)
                        self.running_councils[council.id] = True

                # Wait for all council tasks
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.exception("Orchestrator daemon failed", error=str(e))
            raise

    async def _run_council_loop(self, council_id: int, council_name: str):
        """
        Run continuous loop for a single council.

        Parameters
        ----------
        council_id : int
            Council ID
        council_name : str
            Council name for logging
        """
        logger.info(
            "Starting council loop",
            council_id=council_id,
            council_name=council_name,
            interval_seconds=self.schedule_interval,
        )

        while self.running_councils.get(council_id, False):
            try:
                # Run council cycle
                await self.run_council_cycle(council_id)

                # Wait for next scheduled interval
                logger.info(
                    "Waiting for next cycle",
                    council_id=council_id,
                    interval_seconds=self.schedule_interval,
                )
                await asyncio.sleep(self.schedule_interval)

            except Exception:
                logger.exception(
                    "Error in council loop",
                    council_id=council_id,
                    council_name=council_name,
                )
                # Wait before retrying
                await asyncio.sleep(60)

        logger.info("Council loop stopped", council_id=council_id)

    async def stop(self):
        """Stop all running councils."""
        logger.info("Stopping orchestrator - signaling all councils to stop")

        # Signal all councils to stop
        for council_id in list(self.running_councils.keys()):
            self.running_councils[council_id] = False

        logger.info("All councils signaled to stop")

    async def run_council_cycle(self, council_id: int) -> dict[str, bool | str | list]:
        """
        Run a single council trading cycle.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        dict
            Cycle results with keys:
            - success: bool
            - consensuses: list
            - trades_executed: int
            - trades_skipped: int
        """
        try:
            # Use scoped=False to avoid disposing the connection pool
            async with session_manager.session(scoped=False) as session, UnitOfWork(session) as uow:
                repo = uow.get_repository(Council)
                council = await repo.get_council_by_id(council_id)

                if not council:
                    logger.error("Council not found", council_id=council_id)
                    return {"success": False, "error": "council_not_found"}

                logger.info(
                    "🎯 Running council cycle",
                    council_id=council.id,
                    council_name=council.name,
                    trading_mode=council.trading_mode,
                    trading_type=council.trading_type,
                )

                # 1. Create council run record
                run = CouncilRun(
                    council_id=council_id,
                    user_id=council.user_id or 1,  # Use council's user_id or default to 1 for system councils
                    trading_mode=council.trading_mode,  # "paper" or "real"
                    status="IN_PROGRESS",
                    started_at=datetime.now(UTC),
                    meta_data={},
                )
                session.add(run)
                await session.commit()

                # 2. Determine symbols to trade
                symbols = self.symbols_override or ["BTCUSDT", "ETHUSDT"]

                # 3. Fetch current portfolio context for agents
                portfolio_service = PortfolioContextService(session)
                portfolio = await portfolio_service.aget_portfolio_context(
                    council=council,
                    symbols=symbols,
                )

                logger.info(
                    "Portfolio context fetched",
                    council_id=council.id,
                    total_positions=portfolio.get("total_positions", 0),
                    available_balance=portfolio.get("available_balance", 0),
                )

                # 4. Run agent debate
                logger.info("Running agent debate", symbols_count=len(symbols))

                # Use DebateService for consistent agent execution
                debate_service = DebateService(session)
                debate_result = await debate_service.aexecute_debate(
                    council=council,
                    symbols=symbols,
                    start_date=None,
                    end_date=None,
                )

                if not debate_result.get("success"):
                    logger.error("Debate execution failed", error=debate_result.get("error"))
                    return {
                        "success": False,
                        "error": debate_result.get("error", "Unknown debate error"),
                    }

                # Extract signals from debate result
                debate_signals = debate_result.get("signals", {})

                # 5. Determine consensus
                consensuses = await debate_service.adetermine_consensus(
                    council_id=council.id,
                    signals=debate_signals,
                    threshold=self.consensus_threshold,
                )

                logger.info(
                    "Consensus determined",
                    symbols_count=len(consensuses),
                    council_id=council_id,
                )

                # 6. Execute trades
                trading_service = CouncilTradingService(session)
                trade_results = await trading_service.aexecute_multi_symbol_trades(
                    council_id=council_id,
                    consensuses=consensuses,
                )

                trades_executed = trade_results.get("trades_executed", [])
                trades_skipped = trade_results.get("trades_skipped", [])

                # 7. Update run record
                run.status = "COMPLETED"
                run.completed_at = datetime.now(UTC)
                run.results = {
                    "consensuses": consensuses,
                    "trades_executed": len(trades_executed),
                    "trades_skipped": len(trades_skipped),
                    "symbols_processed": len(consensuses),
                }

                await session.commit()

                # 8. Broadcast events
                if self.websocket_manager:
                    for consensus in consensuses:
                        await self._broadcast_consensus(council_id, consensus)

                logger.info(
                    "✅ Council cycle completed",
                    council_id=council_id,
                    trades_executed=len(trades_executed),
                    trades_skipped=len(trades_skipped),
                )

                return {
                    "success": True,
                    "consensuses": consensuses,
                    "trades_executed": len(trades_executed),
                    "trades_skipped": len(trades_skipped),
                }

        except Exception as e:
            logger.exception("Council cycle failed", council_id=council_id, error=str(e))
            return {"success": False, "error": str(e)}

    def _extract_agent_signals(self, debate_results: dict, symbol: str) -> list[dict[str, str | float]]:
        """
        Extract agent signals for a specific symbol from debate results.

        Parameters
        ----------
        debate_results : dict
            LangGraph debate results
        symbol : str
            Trading symbol

        Returns
        -------
        list[dict]
            List of agent signals
        """
        # Extract from debate results
        # This is simplified - adjust based on actual GraphService output structure
        signals = []

        if "agent_signals" in debate_results:
            signals = [
                signal
                for signal in debate_results["agent_signals"].values()
                if isinstance(signal, dict) and signal.get("symbol") == symbol
            ]

        return signals

    async def _broadcast_consensus(self, council_id: int, consensus: dict) -> None:
        """
        Broadcast consensus event via WebSocket.

        Parameters
        ----------
        council_id : int
            Council ID
        consensus : dict
            Consensus data
        """
        if not self.websocket_manager:
            return

        try:
            await self.websocket_manager.broadcast(
                f"council_{council_id}",
                {
                    "type": "consensus",
                    "data": consensus,
                },
            )
        except Exception as e:
            logger.warning("Failed to broadcast consensus", error=str(e))
