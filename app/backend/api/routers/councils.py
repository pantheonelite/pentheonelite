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
    CouncilCreateRequest,
    CouncilOverviewResponse,
    CouncilResponse,
    DebateMessage,
    GlobalActivityResponse,
    HoldTimes,
    PerformanceDataPoint,
    PortfolioHoldingDetail,
    TotalAccountValueDataPoint,
    TotalAccountValueResponse,
    TradeRecord,
    TradingMetricsResponse,
)
from app.backend.api.utils.agent_metadata import create_agent_info, normalize_agent_list
from app.backend.api.utils.error_handling import handle_repository_errors
from app.backend.client.aster import AsterClient
from app.backend.client.binance import BinanceClient
from app.backend.config.binance import BinanceConfig
from app.backend.db.models import Council, Wallet
from app.backend.db.models.futures_position import FuturesPosition
from app.backend.db.repositories.wallet_repository import WalletRepository
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
        "wallet_id",
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
                from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository

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
                            pnl_percentage=(
                                float((p.realized_pnl / (p.entry_price * abs(p.position_amt))) * 100)
                                if p.realized_pnl is not None and p.entry_price > 0 and p.position_amt != 0
                                else None
                            ),
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
            from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository

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
                    pnl_percentage=(
                        float((p.realized_pnl / (p.entry_price * abs(p.position_amt))) * 100)
                        if p.realized_pnl is not None and p.entry_price > 0 and p.position_amt != 0
                        else None
                    ),
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
    if include_portfolio:
        if council.trading_type == "spot":
            from app.backend.db.repositories.spot_holding_repository import SpotHoldingRepository

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

    # Get wallet CA (Contract Address) and wallet name if wallet exists
    wallet_ca = None
    wallet_name = None
    if council.wallet_id:
        wallet_repo = WalletRepository(uow.session)
        wallet_ca = await wallet_repo.get_wallet_ca_by_id(council.wallet_id)
        wallet_name = await wallet_repo.get_wallet_name_by_id(council.wallet_id)

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
        wallet_ca=wallet_ca,
        wallet_name=wallet_name,
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
    """
    Get recent closed trades for a council from wallet API.

    Falls back to database if wallet is not available.
    """
    council_repo = uow.get_repository(Council)
    council = await council_repo.get_council_by_id(council_id)

    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    if council.trading_type == "futures":
        # Try to get trades from wallet API first
        wallet = None
        client = None
        if council.wallet_id:
            wallet_repo = WalletRepository(uow.session)
            wallet = await wallet_repo.get_by_id(council.wallet_id)
            if wallet and wallet.is_active and wallet.api_key and wallet.secret_key:
                try:
                    # Initialize client with wallet credentials
                    if council.trading_mode == "paper" and wallet.exchange.lower() == "binance":
                        config = BinanceConfig(
                            api_key=wallet.api_key,
                            api_secret=wallet.secret_key,
                            testnet=True,
                        )
                        client = BinanceClient(config)
                    elif council.trading_mode == "real" and wallet.exchange.lower() == "aster":
                        client = AsterClient(api_key=wallet.api_key, api_secret=wallet.secret_key)
                except Exception as e:
                    logger.warning(
                        "Failed to initialize client with wallet credentials, falling back to database",
                        council_id=council_id,
                        wallet_id=wallet.id,
                        error=str(e),
                    )

        # Try to get trades from wallet API
        if client and council.trading_mode == "paper":
            try:
                # Get symbols from database to know which symbols to query
                from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository

                futures_repo = FuturesPositionRepository(uow.session)
                
                # Get all unique symbols from closed positions to query orders
                all_positions = await futures_repo.find_all_positions(council_id)
                symbols = list(set(p.symbol for p in all_positions if p.status in ["CLOSED", "LIQUIDATED"]))
                
                # If no symbols in database, try to get from wallet positions
                if not symbols:
                    try:
                        positions = await client.aget_positions()
                        symbols = list(set(pos.symbol for pos in positions))
                    except Exception:
                        pass
                
                # Get all orders from wallet API for each symbol
                all_orders = []
                for symbol in symbols[:10]:  # Limit to 10 symbols to avoid too many API calls
                    try:
                        orders = await client.aget_all_orders(symbol=symbol, limit=limit)
                        all_orders.extend(orders)
                    except Exception as e:
                        logger.warning(
                            "Failed to get orders from wallet API for symbol",
                            symbol=symbol,
                            error=str(e),
                        )
                
                # Create a map of closed positions by symbol for P&L lookup
                closed_positions_map = {p.symbol: p for p in all_positions if p.status in ["CLOSED", "LIQUIDATED"]}
                
                # Filter only closed trades:
                # 1. Orders with reduce_only=True (closing orders)
                # 2. Orders that match with closed positions in database
                closed_orders = [
                    order for order in all_orders
                    if order.status in ["FILLED", "CANCELED", "EXPIRED"] 
                    and order.filled_quantity > 0
                    and (
                        order.reduce_only  # Closing orders
                        or order.symbol in closed_positions_map  # Match with closed positions
                    )
                ]
                
                # Sort by timestamp descending and limit
                closed_orders.sort(key=lambda x: x.timestamp, reverse=True)
                closed_orders = closed_orders[:limit]
                
                # Convert to TradeRecord format
                trade_records = []
                for order in closed_orders:
                    # Determine side from position_side
                    if order.position_side == "BOTH":
                        side = "long" if order.side == "BUY" else "short"
                    else:
                        side = order.position_side.lower()
                    
                    # Try to get P&L from matching position in database
                    pnl = None
                    pnl_percentage = None
                    entry_price = order.average_price or order.price or 0.0
                    exit_price = None
                    closed_at = order.timestamp if order.status == "FILLED" else None
                    
                    # Try to match with closed position for accurate P&L data
                    if order.symbol in closed_positions_map:
                        position = closed_positions_map[order.symbol]
                        # Use position's realized_pnl if available
                        if position.realized_pnl is not None:
                            pnl = float(position.realized_pnl)
                            entry_price = float(position.entry_price)
                            exit_price = float(position.mark_price) if position.mark_price else None
                            closed_at = position.closed_at
                            # Only include trades that actually have closed_at (closed positions)
                            if not closed_at:
                                continue  # Skip positions without closed_at
                    
                    # Only include trades that have closed_at (actually closed)
                    if not closed_at:
                        continue  # Skip trades without closed_at
                    
                    # Calculate P&L percentage if we have P&L and entry price
                    if pnl is not None and entry_price > 0 and order.filled_quantity > 0:
                        cost_basis = entry_price * order.filled_quantity
                        pnl_percentage = (pnl / cost_basis * 100) if cost_basis > 0 else None
                    
                    trade_records.append(
                        TradeRecord(
                            id=order.order_id,  # Use order_id as id
                            symbol=order.symbol,
                            order_type=order.type,
                            side=side,
                            quantity=order.filled_quantity,
                            entry_price=entry_price,
                            exit_price=exit_price or (order.average_price if order.reduce_only else None),
                            pnl=pnl,
                            pnl_percentage=pnl_percentage,
                            status="closed",  # Always set to "closed" for closed trades
                            opened_at=order.timestamp,
                            closed_at=closed_at,
                        )
                    )
                
                if trade_records:
                    return trade_records[:25]
            except Exception as e:
                logger.warning(
                    "Failed to fetch trades from wallet API, falling back to database",
                    council_id=council_id,
                    error=str(e),
                )
        
        # Fallback to database
        from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository

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
                pnl_percentage=(
                    float((p.realized_pnl / (p.entry_price * abs(p.position_amt))) * 100)
                    if p.realized_pnl is not None and p.entry_price > 0 and p.position_amt != 0
                    else None
                ),
                status="closed",
                opened_at=p.opened_at,
                closed_at=p.closed_at,
            )
            for p in closed_positions
        ]
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
@router.get("/system/total-account-value", response_model=TotalAccountValueResponse)
async def get_total_account_value(
    uow: UnitOfWorkDep,
    days: Annotated[int, Query(ge=1, le=365)] = 72,
):
    """
    Get account values for all system councils over time.
    
    Returns data with each council as a separate line, similar to nof1.ai's total account value chart.
    """
    from decimal import Decimal

    repo = uow.get_repository(Council)
    councils_data = await repo.get_council_account_values(days=days)

    if not councils_data:
        # Return empty response if no data
        return TotalAccountValueResponse(
            councils=[],
            total_current_value=0.0,
            total_change_dollar=0.0,
            total_change_percentage=0.0,
        )

    # Process each council's data
    council_series = []
    total_current_value = 0.0
    total_first_value = 0.0

    for council_id, data in councils_data.items():
        data_points = data["data_points"]
        if not data_points:
            continue

        # Sort by timestamp
        data_points.sort(key=lambda x: x["timestamp"])

        # Calculate current value (latest)
        current_value = data["current_value"] if data["current_value"] > 0 else (data_points[-1]["total_value"] if data_points else 0.0)
        first_value = data_points[0]["total_value"] if data_points else current_value
        
        change_dollar = current_value - first_value
        change_percentage = (
            (change_dollar / first_value * 100) if first_value > 0 else 0.0
        )

        total_current_value += current_value
        total_first_value += first_value

        # Create data points with change calculations
        processed_points = []
        for i, point in enumerate(data_points):
            prev_value = (
                data_points[i - 1]["total_value"]
                if i > 0
                else point["total_value"]
            )
            point_change_dollar = point["total_value"] - prev_value
            point_change_percentage = (
                (point_change_dollar / prev_value * 100) if prev_value > 0 else 0.0
            )

            processed_points.append(
                TotalAccountValueDataPoint(
                    timestamp=point["timestamp"],
                    total_value=point["total_value"],
                    change_dollar=point_change_dollar,
                    change_percentage=point_change_percentage,
                )
            )

        council_series.append(
            CouncilAccountValueSeries(
                council_id=council_id,
                council_name=data["council_name"],
                data_points=processed_points,
                current_value=current_value,
                change_dollar=change_dollar,
                change_percentage=change_percentage,
            )
        )

    # Calculate total changes
    total_change_dollar = total_current_value - total_first_value
    total_change_percentage = (
        (total_change_dollar / total_first_value * 100) if total_first_value > 0 else 0.0
    )

    return TotalAccountValueResponse(
        councils=council_series,
        total_current_value=total_current_value,
        total_change_dollar=total_change_dollar,
        total_change_percentage=total_change_percentage,
    )


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
    Get all active trading positions for a council from wallet API.

    Returns open positions with current prices, unrealized PnL, and liquidation prices.
    Falls back to database if wallet is not available.
    """
    council_repo = uow.get_repository(Council)

    # Verify council exists
    council = await council_repo.get_council_by_id(council_id)
    if not council:
        raise HTTPException(status_code=404, detail=f"Council {council_id} not found")

    active_positions = []
    total_unrealized = 0.0

    # Try to get positions from wallet API first
    wallet = None
    client = None
    if council.wallet_id:
        wallet_repo = WalletRepository(uow.session)
        wallet = await wallet_repo.get_by_id(council.wallet_id)
        if wallet and wallet.is_active and wallet.api_key and wallet.secret_key:
            try:
                # Initialize client with wallet credentials
                if council.trading_mode == "paper" and wallet.exchange.lower() == "binance":
                    config = BinanceConfig(
                        api_key=wallet.api_key,
                        api_secret=wallet.secret_key,
                        testnet=True,
                    )
                    client = BinanceClient(config)
                elif council.trading_mode == "real" and wallet.exchange.lower() == "aster":
                    client = AsterClient(api_key=wallet.api_key, api_secret=wallet.secret_key)
            except Exception as e:
                logger.warning(
                    "Failed to initialize client with wallet credentials, falling back to database",
                    council_id=council_id,
                    wallet_id=wallet.id,
                    error=str(e),
                )

    if council.trading_type == "futures":
        # Try to get positions from wallet API
        if client:
            try:
                # Get positions from wallet API
                positions = await client.aget_positions()
                
                # Map wallet API positions to ActivePosition format
                for pos in positions:
                    try:
                        # Determine side from position_amount sign (for BOTH mode) or position_side
                        if pos.position_side == "BOTH":
                            side = "long" if pos.position_amount > 0 else "short"
                        else:
                            side = pos.position_side.lower()
                        
                        # Calculate unrealized PnL percentage
                        cost_basis = abs(pos.entry_price * pos.position_amount)
                        unrealized_pnl_pct = (pos.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                        
                        # Calculate notional (position_amount * mark_price)
                        notional = abs(pos.position_amount * pos.mark_price)
                        
                        active_positions.append(
                            ActivePosition(
                                id=0,  # No database ID for wallet positions
                                symbol=pos.symbol,
                                side=side,
                                entry_price=pos.entry_price,
                                current_price=pos.mark_price,
                                quantity=abs(pos.position_amount),
                                leverage=pos.leverage,
                                unrealized_pnl=pos.unrealized_pnl,
                                unrealized_pnl_percentage=unrealized_pnl_pct,
                                opened_at=pos.timestamp,  # Use timestamp from API
                                liquidation_price=pos.liquidation_price,
                                margin_used=None,  # Not available from API
                                notional=notional,
                            )
                        )
                        total_unrealized += pos.unrealized_pnl
                    except Exception as e:
                        logger.warning(
                            "Failed to process position from wallet API",
                            symbol=pos.symbol if hasattr(pos, 'symbol') else 'unknown',
                            error=str(e),
                        )
                
                # Return positions from wallet API
                return ActivePositionsResponse(
                    positions=active_positions,
                    total_unrealized_pnl=total_unrealized,
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch positions from wallet API, falling back to database",
                    council_id=council_id,
                    error=str(e),
                )
        
        # Fallback to database
        from app.backend.db.repositories.futures_position_repository import FuturesPositionRepository

        futures_repo = FuturesPositionRepository(uow.session)
        positions = await futures_repo.find_open_positions(council_id)

        # Initialize appropriate client for price updates
        # Use wallet credentials if available, otherwise fall back to environment variables
        if not client:
            if council.trading_mode == "paper":
                # Try wallet credentials first
                if wallet and wallet.exchange.lower() == "binance":
                    try:
                        config = BinanceConfig(
                            api_key=wallet.api_key,
                            api_secret=wallet.secret_key,
                            testnet=True,
                        )
                        client = BinanceClient(config)
                    except Exception as e:
                        logger.warning(
                            "Failed to use wallet credentials for fallback, using environment variables",
                            error=str(e),
                        )
                        config = BinanceConfig(testnet=True)
                        client = BinanceClient(config)
                else:
                    config = BinanceConfig(testnet=True)
                    client = BinanceClient(config)
            else:
                # Real trading - try wallet first
                if wallet and wallet.exchange.lower() == "aster":
                    try:
                        client = AsterClient(api_key=wallet.api_key, api_secret=wallet.secret_key)
                    except Exception as e:
                        logger.warning(
                            "Failed to use wallet credentials for fallback, using environment variables",
                            error=str(e),
                        )
                        client = AsterClient()
                else:
                    client = AsterClient()

        for p in positions:
            try:
                # Fetch current price
                ticker = await client.aget_ticker(p.symbol)
                current_price = float(ticker.price)

                # Calculate unrealized PnL based on current price
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
        from app.backend.db.repositories.spot_holding_repository import SpotHoldingRepository

        spot_repo = SpotHoldingRepository(uow.session)
        holdings = await spot_repo.find_active_holdings(council_id)

        # Initialize appropriate client
        if not client:
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


@handle_repository_errors
@router.post("/", response_model=CouncilResponse)
async def create_council(request: CouncilCreateRequest, uow: UnitOfWorkDep):
    """
    Create a new council.
    
    If wallet information (api_key, secret_key) is provided, a wallet will be
    created and linked to the council.
    """
    council_repo = uow.get_repository(Council)
    
    # Create the council
    council = await council_repo.create_council(
        name=request.name,
        agents=request.agents,
        connections=request.connections,
        description=request.description,
        strategy=request.strategy,
        tags=request.tags,
        workflow_config=request.workflow_config,
        visual_layout=request.visual_layout,
        initial_capital=request.initial_capital,
        risk_settings=request.risk_settings,
        is_public=request.is_public,
        is_template=request.is_template,
    )
    
    # Create wallet if wallet info is provided
    if request.api_key and request.secret_key:
        wallet_repo = WalletRepository(uow.session)
        # Default to "binance" if exchange not provided
        exchange = request.exchange or "binance"
        wallet = await wallet_repo.create_wallet(
            council_id=council.id,
            exchange=exchange,
            api_key=request.api_key,
            secret_key=request.secret_key,
            ca=request.ca,
            is_active=True,
        )
        logger.info(
            "Created wallet for council",
            council_id=council.id,
            wallet_id=wallet.id,
        )
    
    # Reload council to get wallet_id if wallet was created
    council = await council_repo.get_council_by_id(council.id)
    
    return CouncilResponse.model_validate(council, from_attributes=True)
