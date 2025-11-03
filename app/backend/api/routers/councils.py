"""Council API endpoints for unified Council model (system councils and live trading)."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import structlog
from app.backend.api.dependencies import UnitOfWorkDep
from app.backend.api.schemas import (
    ActivePosition,
    ActivePositionsResponse,
    AgentInfo,
    ConsensusDecisionResponse,
    CouncilOverviewResponse,
    CouncilResponse,
    DebateMessage,
    GlobalActivityResponse,
    HoldTimes,
    PerformanceDataPoint,
    PortfolioHoldingDetail,
    TradeRecord,
    TradingMetricsResponse,
)
from app.backend.api.utils.agent_metadata import create_agent_info, normalize_agent_list
from app.backend.api.utils.error_handling import handle_repository_errors
from app.backend.client.aster import AsterClient
from app.backend.client.binance import BinanceClient
from app.backend.config.binance import BinanceConfig
from app.backend.db.models import Council
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository
from app.backend.db.repositories.spot_holding_repository import SpotHoldingRepository
from fastapi import APIRouter, HTTPException, Query

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/councils", tags=["councils"])


def normalize_position_side(position: FuturesPosition) -> str:
    """
    Normalize position side from "BOTH" to "LONG"/"SHORT".

    Parameters
    ----------
    position : FuturesPosition
        Position object from database

    Returns
    -------
    str
        Normalized position side ("long" or "short" in lowercase for API)
    """
    if position.position_side.upper() == "BOTH":
        # For Binance one-way mode, determine side from position_amt sign
        return "long" if position.position_amt > 0 else "short"
    return position.position_side.lower()


@handle_repository_errors
@router.get("/system", response_model=list[CouncilResponse])
async def get_system_councils(uow: UnitOfWorkDep):
    """Get all active system councils."""
    repo = uow.get_repository(Council)
    councils = await repo.get_system_councils()

    council_fields = {
        "user_id",
        "risk_settings",
        "win_rate",
        "forked_from_id",
        "meta_data",
        "visual_layout",
        "agents",
        "connections",
        "workflow_config",
        "is_system",
        "is_public",
        "is_template",
        "name",
        "description",
        "strategy",
        "tags",
        "initial_capital",
        "current_capital",
        "total_pnl",
        "total_pnl_percentage",
        "total_trades",
        "status",
        "is_active",
        "created_at",
        "updated_at",
        "last_executed_at",
        "view_count",
        "fork_count",
        "id",
    }
    patched = []
    for c in councils:
        data = CouncilResponse.model_validate(c, from_attributes=True).model_dump(exclude_none=True)
        for f in council_fields:
            if f not in data:
                data[f] = None
        patched.append(data)
    return patched


@handle_repository_errors
@router.get("/system/activity", response_model=GlobalActivityResponse)
async def get_system_councils_activity(
    uow: UnitOfWorkDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """
    Get recent activity across all system councils.

    Returns debates and trades from all system councils in a single aggregated response.
    """
    repo = uow.get_repository(Council)

    # Get all system councils
    councils = await repo.get_system_councils()

    # Create council name mapping
    council_map = {council.id: council.name for council in councils}

    # Fetch debates and trades from all councils in parallel
    all_debates = []
    all_trades = []

    for council in councils:
        try:
            # Fetch debates for this council
            debates = await repo.get_recent_debates(council.id, limit=limit)

            # Add council info to debates
            all_debates.extend(
                [
                    DebateMessage(
                        id=debate.id,
                        agent_name=debate.agent_name,
                        message=debate.message,
                        message_type=debate.message_type,
                        sentiment=debate.sentiment,
                        market_symbol=debate.market_symbol,
                        confidence=float(debate.confidence) if debate.confidence else None,
                        debate_round=debate.debate_round,
                        created_at=debate.created_at,
                        council_id=council.id,
                        council_name=council.name,
                    )
                    for debate in debates
                ]
            )

            # Fetch trades from new tables
            if council.trading_type == "futures":
                futures_repo = FuturesPositionRepository(repo.session)
                closed_positions = await futures_repo.find_closed_positions(council.id, limit=limit)

                all_trades.extend(
                    [
                        TradeRecord(
                            id=p.id,
                            symbol=p.symbol,
                            order_type="MARKET",
                            side=normalize_position_side(p),  # Normalize "BOTH" → "long"/"short"
                            quantity=float(abs(p.position_amt)),  # Always positive
                            entry_price=float(p.entry_price),
                            exit_price=float(p.mark_price) if p.mark_price else None,
                            pnl=float(p.realized_pnl) if p.realized_pnl else None,
                            pnl_percentage=None,
                            status="closed",
                            opened_at=p.opened_at,
                            closed_at=p.closed_at,
                            council_id=council.id,
                            council_name=council.name,
                        )
                        for p in closed_positions
                    ]
                )

        except Exception as e:
            logger.warning("Error fetching activity for council", council_id=council.id, error=str(e))
            # Continue with other councils
            continue

    # Sort by timestamp (most recent first)
    all_debates.sort(key=lambda d: d.created_at, reverse=True)
    all_trades.sort(key=lambda t: t.opened_at, reverse=True)

    # Limit results
    all_debates = all_debates[:limit]
    all_trades = all_trades[:limit]

    return GlobalActivityResponse(
        debates=all_debates,
        trades=all_trades,
        councils=council_map,
    )


@handle_repository_errors
@router.get("/{council_id}/overview", response_model=CouncilOverviewResponse)
async def get_council_overview(
    uow: UnitOfWorkDep,
    council_id: int,
    *,
    include_agents: Annotated[bool, Query(description="Include agent details")] = False,
    include_debates: Annotated[bool, Query(description="Include recent debate messages")] = False,
    include_trades: Annotated[bool, Query(description="Include recent trades")] = False,
    include_portfolio: Annotated[bool, Query(description="Include portfolio holdings breakdown")] = False,
):
    """Get comprehensive council overview (unified endpoint replacing /detailed, /live-status, and /stats)."""
    repo = uow.get_repository(Council)

    # Fetch council
    council = await repo.get_council_by_id(council_id)
    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    # Determine trading mode
    is_paper_trading = getattr(council, "is_paper_trading", True)

    # Get position counts from council (new position-based system)
    open_positions_count = (
        council.open_futures_count if council.trading_type == "futures" else council.active_spot_holdings
    )
    closed_positions_count = council.closed_futures_count
    actual_total_trades = council.total_trades or 0

    # Use council's last_executed_at
    latest_trade_timestamp = council.last_executed_at

    # Optional: Include agents
    agents_list = None
    if include_agents and council.agents:
        agents_data = normalize_agent_list(council.agents)
        if isinstance(agents_data, list):
            agents_list = [create_agent_info(agent_data) for agent_data in agents_data]

    # Optional: Include recent debates
    debates_list = None
    if include_debates:
        debates = await repo.get_recent_debates(council_id, limit=50)
        debates_list = [
            DebateMessage(
                id=d.id,
                agent_name=d.agent_name,
                message=d.message,
                message_type=d.message_type,
                sentiment=d.sentiment,
                market_symbol=d.market_symbol,
                confidence=float(d.confidence) if d.confidence else None,
                debate_round=d.debate_round,
                created_at=d.created_at,
            )
            for d in debates
        ]

    # Optional: Include recent trades (from new tables)
    trades_list = None
    if include_trades:
        if council.trading_type == "futures":
            futures_repo = FuturesPositionRepository(uow.session)
            closed_positions = await futures_repo.find_closed_positions(council_id, limit=20)
            trades_list = [
                TradeRecord(
                    id=p.id,
                    symbol=p.symbol,
                    order_type="MARKET",
                    side=normalize_position_side(p),  # Normalize "BOTH" → "long"/"short"
                    quantity=float(abs(p.position_amt)),  # Always positive
                    entry_price=float(p.entry_price),
                    exit_price=float(p.mark_price) if p.mark_price else None,
                    pnl=float(p.realized_pnl) if p.realized_pnl else None,
                    pnl_percentage=None,  # Calculate if needed
                    status="closed",
                    opened_at=p.opened_at,
                    closed_at=p.closed_at,
                )
                for p in closed_positions
            ]
        else:  # spot
            trades_list = []  # Spot holdings don't have "closed" trades

    # Optional: Include portfolio holdings with details (from new tables)
    portfolio_holdings = None
    if include_portfolio and council.trading_type == "spot":
        spot_repo = SpotHoldingRepository(uow.session)
        holdings = await spot_repo.find_active_holdings(council_id)

        portfolio_holdings = {}
        for h in holdings:
            portfolio_holdings[h.symbol] = PortfolioHoldingDetail(
                quantity=float(h.total),
                avg_cost=float(h.average_cost),
                total_cost=float(h.total_cost),
                current_value=float(h.current_value) if h.current_value else None,
                unrealized_pnl=float(h.unrealized_pnl) if h.unrealized_pnl else None,
            )

    # Build response
    return CouncilOverviewResponse(
        id=council.id,
        name=council.name,
        description=council.description,
        strategy=council.strategy,
        is_system=council.is_system,
        is_public=council.is_public,
        status=council.status,
        is_paper_trading=is_paper_trading,
        initial_capital=float(council.initial_capital),
        current_capital=float(council.total_account_value),
        available_capital=float(council.available_balance),
        total_pnl=float(council.total_pnl)
        if council.total_pnl
        else float(council.total_unrealized_profit + council.total_realized_pnl),
        total_pnl_percentage=float(council.total_pnl_percentage) if council.total_pnl_percentage else 0.0,
        win_rate=float(council.win_rate) if council.win_rate else None,
        total_trades=actual_total_trades,  # Use calculated value
        open_positions_count=open_positions_count,
        closed_positions_count=closed_positions_count,
        created_at=council.created_at,
        last_executed_at=latest_trade_timestamp or council.last_executed_at,  # Use latest trade timestamp
        agents=agents_list,
        recent_debates=debates_list,
        recent_trades=trades_list,
        portfolio_holdings=portfolio_holdings,
    )


@handle_repository_errors
@router.get("/{council_id}/debates", response_model=list[DebateMessage])
async def get_council_debates(
    uow: UnitOfWorkDep,
    council_id: int,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """Get recent debate messages for a council."""
    repo = uow.get_repository(Council)
    debates = await repo.get_recent_debates(council_id, limit=limit)

    return [
        DebateMessage(
            id=d.id,
            agent_name=d.agent_name,
            message=d.message,
            message_type=d.message_type,
            sentiment=d.sentiment,
            market_symbol=d.market_symbol,
            confidence=float(d.confidence) if d.confidence else None,
            debate_round=d.debate_round,
            created_at=d.created_at,
        )
        for d in debates
    ]


@handle_repository_errors
@router.get("/{council_id}/trades", response_model=list[TradeRecord])
async def get_council_trades(
    uow: UnitOfWorkDep,
    council_id: int,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Get recent closed trades for a council (from new position-based tables)."""
    council_repo = uow.get_repository(Council)
    council = await council_repo.get_council_by_id(council_id)

    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    if council.trading_type == "futures":
        futures_repo = FuturesPositionRepository(uow.session)
        closed_positions = await futures_repo.find_closed_positions(council_id, limit=limit)

        return [
            TradeRecord(
                id=p.id,
                symbol=p.symbol,
                order_type="MARKET",
                side=normalize_position_side(p),  # Normalize "BOTH" → "long"/"short"
                quantity=float(abs(p.position_amt)),  # Always positive
                entry_price=float(p.entry_price),
                exit_price=float(p.mark_price) if p.mark_price else None,
                pnl=float(p.realized_pnl) if p.realized_pnl else None,
                pnl_percentage=None,
                status="closed",
                opened_at=p.opened_at,
                closed_at=p.closed_at,
            )
            for p in closed_positions
        ]
    # spot
    # Spot doesn't have traditional "trades" - it's holdings
    return []


@handle_repository_errors
@router.get("/{council_id}/performance", response_model=list[PerformanceDataPoint])
async def get_council_performance(
    uow: UnitOfWorkDep,
    *,
    council_id: int,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    limit: Annotated[int | None, Query(ge=1, le=100000)] = None,
):
    """Get historical performance data for a council."""
    # Backward compatibility: allow legacy `limit` query param
    effective_limit = limit if limit is not None else days * 24

    repo = uow.get_repository(Council)
    performance_data = await repo.get_performance_history(council_id, limit=effective_limit)

    # Filter to requested date range
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    filtered_data = [p for p in performance_data if p.timestamp >= cutoff_date]

    return [
        PerformanceDataPoint(
            timestamp=p.timestamp,
            total_value=float(p.total_value),
            pnl=float(p.pnl),
            pnl_percentage=float(p.pnl_percentage),
            win_rate=float(p.win_rate) if p.win_rate else None,
            total_trades=p.total_trades or 0,
            open_positions=p.open_positions or 0,
        )
        for p in filtered_data
    ]


@handle_repository_errors
@router.get("/{council_id}/agents", response_model=list[AgentInfo])
async def get_council_agents(council_id: int, uow: UnitOfWorkDep):
    """Get all agents for a council."""
    repo = uow.get_repository(Council)
    council = await repo.get_council_by_id(council_id)

    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    # Parse agents from JSON
    if isinstance(council.agents, list):
        return [
            AgentInfo(
                id=agent_data.get("id", ""),
                name=agent_data.get("name", ""),
                type=agent_data.get("type", ""),
                role=agent_data.get("role"),
                traits=agent_data.get("traits"),
                specialty=agent_data.get("specialty"),
                system_prompt=agent_data.get("system_prompt"),
                position=agent_data.get("position"),
            )
            for agent_data in council.agents
        ]

    return []


@handle_repository_errors
@router.get("/{council_id}/agents/{agent_id}", response_model=AgentInfo)
async def get_council_agent(council_id: int, agent_id: str, uow: UnitOfWorkDep):
    """Get specific agent details from a council."""
    repo = uow.get_repository(Council)
    council = await repo.get_council_by_id(council_id)

    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    # Find agent in JSON
    if isinstance(council.agents, list):
        for agent_data in council.agents:
            if agent_data.get("id") == agent_id:
                return AgentInfo(
                    id=agent_data.get("id", ""),
                    name=agent_data.get("name", ""),
                    type=agent_data.get("type", ""),
                    role=agent_data.get("role"),
                    traits=agent_data.get("traits"),
                    specialty=agent_data.get("specialty"),
                    system_prompt=agent_data.get("system_prompt"),
                    position=agent_data.get("position"),
                )

    raise HTTPException(status_code=404, detail="Agent not found in council")


@handle_repository_errors
@router.get("/{council_id}/consensus", response_model=list[ConsensusDecisionResponse])
async def get_council_consensus_decisions(
    council_id: int,
    uow: UnitOfWorkDep,
    decision_type: Annotated[str | None, Query(description="Filter by decision type: BUY, SELL, HOLD")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
):
    """Get consensus decisions for a council (includes BUY, SELL, and HOLD decisions)."""
    repo = uow.get_repository(Council)

    # Verify council exists
    council = await repo.get_council_by_id(council_id)
    if not council:
        raise HTTPException(status_code=404, detail=f"Council {council_id} not found")

    # Fetch consensus decisions
    decisions = await repo.get_consensus_decisions(
        council_id=council_id,
        decision_type=decision_type,
        limit=limit,
    )

    # Convert to response models
    return [
        ConsensusDecisionResponse(
            id=decision.id,
            council_id=decision.council_id,
            decision=decision.decision,
            symbol=decision.symbol,
            confidence=float(decision.confidence) if decision.confidence else None,
            votes_buy=decision.votes_buy,
            votes_sell=decision.votes_sell,
            votes_hold=decision.votes_hold,
            total_votes=decision.total_votes,
            agent_votes=decision.agent_votes,
            reasoning=decision.reasoning,
            market_price=float(decision.market_price) if decision.market_price else None,
            was_executed=decision.was_executed,
            market_order_id=decision.market_order_id,
            execution_reason=decision.execution_reason,
            created_at=decision.created_at,
        )
        for decision in decisions
    ]


@handle_repository_errors
@router.get("/{council_id}/metrics", response_model=TradingMetricsResponse)
async def get_council_trading_metrics(council_id: int, uow: UnitOfWorkDep):
    """
    Get comprehensive trading metrics for a council.

    Returns net realized PnL, average leverage, average confidence,
    biggest win/loss, and hold time distribution.
    """
    repo = uow.get_repository(Council)

    # Verify council exists
    council = await repo.get_council_by_id(council_id)
    if not council:
        raise HTTPException(status_code=404, detail=f"Council {council_id} not found")

    # Use council metrics (calculated by CouncilMetricsService)
    return TradingMetricsResponse(
        net_realized=float(council.net_pnl),
        average_leverage=float(council.average_leverage),
        average_confidence=float(council.average_confidence * 100),  # Convert to percentage
        biggest_win=float(council.biggest_win),
        biggest_loss=float(council.biggest_loss),
        hold_times=HoldTimes(
            long=float(council.long_hold_pct),
            short=float(council.short_hold_pct),
            flat=float(council.flat_hold_pct),
        ),
    )


@handle_repository_errors
@router.get("/{council_id}/active-positions", response_model=ActivePositionsResponse)
async def get_council_active_positions(council_id: int, uow: UnitOfWorkDep):
    """
    Get all active trading positions for a council.

    Returns open positions with current prices, unrealized PnL, and liquidation prices.
    """
    council_repo = uow.get_repository(Council)

    # Verify council exists
    council = await council_repo.get_council_by_id(council_id)
    if not council:
        raise HTTPException(status_code=404, detail=f"Council {council_id} not found")

    active_positions = []
    total_unrealized = 0.0

    if council.trading_type == "futures":
        # Get futures positions from new table (direct instantiation)
        futures_repo = FuturesPositionRepository(uow.session)
        positions = await futures_repo.find_open_positions(council_id)

        # Initialize appropriate client for price updates
        if council.trading_mode == "paper":
            config = BinanceConfig(testnet=True)
            client = BinanceClient(config)
        else:
            client = AsterClient()

        for p in positions:
            try:
                # Fetch current price
                ticker = await client.aget_ticker(p.symbol)
                current_price = float(ticker.price)

                # Calculate unrealized PnL based on current price
                # For LONG: (current_price - entry_price) * position_amt
                # For SHORT: (entry_price - current_price) * position_amt
                # Note: position_amt is positive for LONG, negative for SHORT
                entry_price = float(p.entry_price)
                position_amt = float(p.position_amt)

                unrealized_pnl = (current_price - entry_price) * position_amt

                # Calculate percentage based on notional value (with leverage)
                cost_basis = abs(entry_price * position_amt)
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0

                active_positions.append(
                    ActivePosition(
                        id=p.id,
                        symbol=p.symbol,
                        side=normalize_position_side(p),  # Normalize "BOTH" → "long"/"short"
                        entry_price=entry_price,
                        current_price=current_price,
                        quantity=float(abs(position_amt)),  # Always positive
                        leverage=p.leverage,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_percentage=unrealized_pnl_pct,
                        opened_at=p.opened_at,
                        liquidation_price=float(p.liquidation_price) if p.liquidation_price else None,
                        margin_used=float(p.isolated_margin) if p.isolated_margin else None,
                        notional=float(p.notional) if p.notional else None,
                    )
                )
                total_unrealized += unrealized_pnl

            except Exception as e:
                logger.warning(
                    "Failed to fetch current price for futures position",
                    symbol=p.symbol,
                    position_id=p.id,
                    error=str(e),
                )

    else:  # spot
        # Get spot holdings from new table (direct instantiation)
        spot_repo = SpotHoldingRepository(uow.session)
        holdings = await spot_repo.find_active_holdings(council_id)

        # Initialize appropriate client
        if council.trading_mode == "paper":
            config = BinanceConfig(testnet=True)
            client = BinanceClient(config)
        else:
            client = AsterClient()

        for h in holdings:
            try:
                # Fetch current price
                ticker = await client.aget_ticker(h.symbol)
                current_price = float(ticker.price)

                # Calculate unrealized PnL
                current_value = float(h.total) * current_price
                cost_basis = float(h.total_cost)
                unrealized_pnl = current_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0

                active_positions.append(
                    ActivePosition(
                        id=h.id,
                        symbol=h.symbol,
                        side="long",  # Spot is always long
                        entry_price=float(h.average_cost),
                        current_price=current_price,
                        quantity=float(h.total),
                        leverage=1,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_percentage=unrealized_pnl_pct,
                        opened_at=h.first_acquired_at,
                    )
                )
                total_unrealized += unrealized_pnl

            except Exception as e:
                logger.warning(
                    "Failed to fetch current price for spot holding",
                    symbol=h.symbol,
                    holding_id=h.id,
                    error=str(e),
                )

    return ActivePositionsResponse(
        positions=active_positions,
        total_unrealized_pnl=total_unrealized,
    )
