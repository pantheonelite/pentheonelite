"""Repository for unified Council operations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.backend.db.models import AgentDebate
from app.backend.db.models.consensus import ConsensusDecision
from app.backend.db.models.council import Council, CouncilRun, CouncilRunCycle
from app.backend.db.repositories.base_repository import AbstractSqlRepository
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class CouncilRepository(AbstractSqlRepository[Council]):
    """
    Repository for unified Council operations.

    Handles both system councils (pre-made templates) and user councils (custom).
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository.

        Parameters
        ----------
        session : AsyncSession
            Database session
        """
        super().__init__(session, Council)

    @staticmethod
    def _load_all_attributes(council: Council) -> Council:
        """
        Trigger loading of all lazy attributes while in session.

        This prevents MissingGreenlet errors when serializing outside session.

        Parameters
        ----------
        council : Council
            Council object to load

        Returns
        -------
        Council
            Same council with all attributes loaded
        """
        # Access all attributes to trigger loading
        _ = (
            council.id,
            council.user_id,
            council.is_system,
            council.is_public,
            council.is_template,
            council.name,
            council.description,
            council.strategy,
            council.tags,
            council.agents,
            council.connections,
            council.workflow_config,
            council.visual_layout,
            council.initial_capital,
            council.risk_settings,
            council.current_capital,
            council.total_pnl,
            council.total_pnl_percentage,
            council.win_rate,
            council.total_trades,
            council.status,
            council.is_active,
            council.created_at,
            council.updated_at,
            council.last_executed_at,
            council.view_count,
            council.fork_count,
            council.forked_from_id,
            council.meta_data,
        )
        return council

    async def create_council(
        self,
        name: str,
        agents: dict,
        connections: dict,
        user_id: int | None = None,
        description: str | None = None,
        strategy: str | None = None,
        tags: list[str] | None = None,
        workflow_config: dict | None = None,
        visual_layout: dict | None = None,
        initial_capital: float = 100000,
        risk_settings: dict | None = None,
        is_system: bool = False,
        is_public: bool = False,
        is_template: bool = False,
        is_paper_trading: bool = True,
        forked_from_id: int | None = None,
        trading_mode: str = "paper",
        trading_type: str = "futures",
    ) -> Council:
        """
        Create a new council.

        Parameters
        ----------
        name : str
            Council name
        agents : dict
            Agent configuration
        connections : dict
            Agent connections/collaborations
        user_id : int | None
            Owner user ID (None for system councils)
        description : str | None
            Council description
        strategy : str | None
            Trading strategy
        tags : list[str] | None
            Tags for categorization
        workflow_config : dict | None
            Execution rules, voting thresholds
        visual_layout : dict | None
            UI rendering info (viewport, positions)
        initial_capital : float
            Starting capital
        risk_settings : dict | None
            Risk management rules
        is_system : bool
            Is this a system council (template)
        is_public : bool
            Is this publicly visible
        is_template : bool
            Can this be used as a template
        is_paper_trading : bool
            Is this paper trading (True) or real trading (False)
        forked_from_id : int | None
            If forked, the source council ID

        Returns
        -------
        Council
            Created council
        """
        council = Council(
            name=name,
            agents=agents,
            connections=connections,
            user_id=user_id,
            description=description,
            strategy=strategy,
            tags=tags,
            workflow_config=workflow_config,
            visual_layout=visual_layout,
            initial_capital=initial_capital,
            risk_settings=risk_settings,
            is_system=is_system,
            is_public=is_public,
            is_template=is_template,
            is_paper_trading=is_paper_trading,
            forked_from_id=forked_from_id,
            status="draft",
            created_at=datetime.utcnow(),
        )

        self.session.add(council)
        await self.session.commit()
        await self.session.refresh(council)

        # If forked, increment fork count on source
        if forked_from_id:
            await self._increment_fork_count(forked_from_id)

        return council

    async def get_council_by_id(self, council_id: int) -> Council | None:
        """
        Get council by ID.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        Council | None
            Council if found
        """
        result = await self.session.execute(select(Council).where(Council.id == council_id))
        council = result.scalar_one_or_none()
        return self._load_all_attributes(council) if council else None

    async def get_user_councils(
        self,
        user_id: int,
        include_templates: bool = True,
        include_forked: bool = True,
    ) -> list[Council]:
        """
        Get all councils owned by a user.

        Parameters
        ----------
        user_id : int
            User ID
        include_templates : bool
            Include template councils
        include_forked : bool
            Include forked councils

        Returns
        -------
        list[Council]
            User's councils
        """
        query = select(Council).where(Council.user_id == user_id)

        if not include_templates:
            query = query.where(Council.is_template.is_(False))

        if not include_forked:
            query = query.where(Council.forked_from_id.is_(None))

        query = query.order_by(Council.updated_at.desc())

        result = await self.session.execute(query)
        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def get_system_councils(self) -> list[Council]:
        """
        Get all system councils (pre-made templates).

        Returns
        -------
        list[Council]
            System councils
        """
        result = await self.session.execute(select(Council).where(Council.is_system.is_(True)).order_by(Council.name))
        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def get_public_councils(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Council]:
        """
        Get public user councils (shareable).

        Parameters
        ----------
        limit : int
            Maximum number of results
        offset : int
            Pagination offset

        Returns
        -------
        list[Council]
            Public councils
        """
        result = await self.session.execute(
            select(Council)
            .where(and_(Council.is_public.is_(True), Council.is_system.is_(False)))
            .order_by(Council.view_count.desc(), Council.fork_count.desc())
            .limit(limit)
            .offset(offset)
        )
        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def get_all_accessible_councils(
        self,
        user_id: int | None = None,
    ) -> list[Council]:
        """
        Get all councils accessible to a user.

        Includes:
        - All system councils
        - User's own councils (if user_id provided)
        - Public user councils

        Parameters
        ----------
        user_id : int | None
            User ID (None for anonymous/system view)

        Returns
        -------
        list[Council]
            Accessible councils
        """
        conditions = [
            Council.is_system.is_(True),  # All system councils
            Council.is_public.is_(True),  # All public councils
        ]

        if user_id:
            conditions.append(Council.user_id == user_id)  # User's own councils

        result = await self.session.execute(
            select(Council).where(or_(*conditions)).order_by(Council.updated_at.desc())
        )
        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def update_council(
        self,
        council_id: int,
        name: str | None = None,
        description: str | None = None,
        agents: dict | None = None,
        connections: dict | None = None,
        workflow_config: dict | None = None,
        visual_layout: dict | None = None,
        strategy: str | None = None,
        tags: list[str] | None = None,
        initial_capital: float | None = None,
        risk_settings: dict | None = None,
        is_public: bool | None = None,
        is_template: bool | None = None,
        status: str | None = None,
    ) -> Council | None:
        """
        Update council configuration.

        Parameters
        ----------
        council_id : int
            Council ID
        ... (other parameters)

        Returns
        -------
        Council | None
            Updated council if found
        """
        council = await self.get_council_by_id(council_id)
        if not council:
            return None

        if name is not None:
            council.name = name
        if description is not None:
            council.description = description
        if agents is not None:
            council.agents = agents
        if connections is not None:
            council.connections = connections
        if workflow_config is not None:
            council.workflow_config = workflow_config
        if visual_layout is not None:
            council.visual_layout = visual_layout
        if strategy is not None:
            council.strategy = strategy
        if tags is not None:
            council.tags = tags
        if initial_capital is not None:
            council.initial_capital = initial_capital
        if risk_settings is not None:
            council.risk_settings = risk_settings
        if is_public is not None:
            council.is_public = is_public
        if is_template is not None:
            council.is_template = is_template
        if status is not None:
            council.status = status

        council.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(council)

        return council

    async def delete_council(self, council_id: int) -> bool:
        """
        Delete a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        council = await self.get_council_by_id(council_id)
        if not council:
            return False

        await self.session.delete(council)
        await self.session.commit()

        return True

    async def fork_council(
        self,
        source_council_id: int,
        user_id: int,
        new_name: str | None = None,
    ) -> Council | None:
        """
        Fork an existing council (system or public user council).

        Parameters
        ----------
        source_council_id : int
            Source council ID
        user_id : int
            New owner user ID
        new_name : str | None
            Custom name for forked council (defaults to "Copy of {original}")

        Returns
        -------
        Council | None
            Forked council if source found
        """
        source = await self.get_council_by_id(source_council_id)
        if not source:
            return None

        fork_name = new_name or f"Copy of {source.name}"

        return await self.create_council(
            name=fork_name,
            agents=source.agents,
            connections=source.connections,
            user_id=user_id,
            description=source.description,
            strategy=source.strategy,
            tags=source.tags,
            workflow_config=source.workflow_config,
            visual_layout=source.visual_layout,
            initial_capital=float(source.initial_capital),
            risk_settings=source.risk_settings,
            is_system=False,  # Forks are never system councils
            is_public=False,  # Default to private
            is_template=False,
            is_paper_trading=getattr(source, "is_paper_trading", True),  # Preserve paper trading flag
            forked_from_id=source_council_id,
        )

    async def update_performance_metrics(
        self,
        council_id: int,
        current_capital: float | None = None,
        total_pnl: float | None = None,
        total_pnl_percentage: float | None = None,
        win_rate: float | None = None,
        total_trades: int | None = None,
    ) -> Council | None:
        """
        Update council performance metrics.

        Parameters
        ----------
        council_id : int
            Council ID
        current_capital : float | None
            Current capital
        total_pnl : float | None
            Total profit/loss
        total_pnl_percentage : float | None
            Total PnL percentage
        win_rate : float | None
            Win rate percentage
        total_trades : int | None
            Total number of trades

        Returns
        -------
        Council | None
            Updated council if found
        """
        council = await self.get_council_by_id(council_id)
        if not council:
            return None

        if current_capital is not None:
            council.current_capital = current_capital
        if total_pnl is not None:
            council.total_pnl = total_pnl
        if total_pnl_percentage is not None:
            council.total_pnl_percentage = total_pnl_percentage
        if win_rate is not None:
            council.win_rate = win_rate
        if total_trades is not None:
            council.total_trades = total_trades

        council.last_executed_at = datetime.utcnow()
        council.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(council)

        return council

    async def increment_view_count(self, council_id: int) -> bool:
        """
        Increment council view count.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if updated
        """
        council = await self.get_council_by_id(council_id)
        if not council:
            return False

        council.view_count += 1
        await self.session.commit()

        return True

    async def _increment_fork_count(self, council_id: int) -> bool:
        """
        Increment fork count (internal use).

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        bool
            True if updated
        """
        council = await self.get_council_by_id(council_id)
        if not council:
            return False

        council.fork_count += 1
        await self.session.commit()

        return True

    async def search_councils(
        self,
        query: str,
        user_id: int | None = None,
        include_system: bool = True,
        include_public: bool = True,
        limit: int = 50,
    ) -> list[Council]:
        """
        Search councils by name or description.

        Parameters
        ----------
        query : str
            Search query
        user_id : int | None
            User ID (to include their private councils)
        include_system : bool
            Include system councils
        include_public : bool
            Include public councils
        limit : int
            Maximum results

        Returns
        -------
        list[Council]
            Matching councils
        """
        search_pattern = f"%{query}%"

        conditions = [
            or_(
                Council.name.ilike(search_pattern),
                Council.description.ilike(search_pattern),
            )
        ]

        visibility_conditions = []
        if include_system:
            visibility_conditions.append(Council.is_system.is_(True))
        if include_public:
            visibility_conditions.append(Council.is_public.is_(True))
        if user_id:
            visibility_conditions.append(Council.user_id == user_id)

        if visibility_conditions:
            conditions.append(or_(*visibility_conditions))

        result = await self.session.execute(
            select(Council).where(and_(*conditions)).order_by(Council.name).limit(limit)
        )

        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def get_all_councils(self) -> list[Council]:
        """Get all councils."""
        result = await self.session.execute(select(Council))
        councils = list(result.scalars().all())
        return [self._load_all_attributes(c) for c in councils]

    async def check_council_names_exist(self, names: set[str]) -> set[str]:
        """
        Check which council names exist in the database.
        
        This is more efficient than loading all councils when checking
        for specific names, reducing lock timeout risks.
        
        Parameters
        ----------
        names : set[str]
            Set of council names to check
            
        Returns
        -------
        set[str]
            Set of council names that exist in the database
        """
        if not names:
            return set()
        
        result = await self.session.execute(
            select(Council.name).where(Council.name.in_(names))
        )
        existing_names = {row[0] for row in result.all()}
        return existing_names

    # ========================================================================
    # Agent Debate Methods
    # ========================================================================

    async def get_recent_debates(self, council_id: int, limit: int = 50) -> list:
        """
        Get recent debates for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        limit : int
            Maximum number of debates to return

        Returns
        -------
        list
            List of AgentDebate objects
        """
        result = await self.session.execute(
            select(AgentDebate)
            .where(AgentDebate.council_id == council_id)
            .order_by(AgentDebate.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_debate_message(
        self,
        council_id: int,
        agent_name: str,
        message: str,
        message_type: str = "analysis",
        sentiment: str | None = None,
        market_symbol: str | None = None,
        confidence: float | None = None,
        debate_round: int | None = None,
    ):
        """
        Create a debate message.

        Parameters
        ----------
        council_id : int
            Council ID
        agent_name : str
            Name of the agent
        message : str
            Debate message content
        message_type : str
            Type of message (default: "analysis")
        sentiment : str | None
            Sentiment (bullish, bearish, neutral)
        market_symbol : str | None
            Market symbol being discussed
        confidence : float | None
            Confidence level (0-100)
        debate_round : int | None
            Debate round number

        Returns
        -------
        AgentDebate
            Created debate message
        """
        debate = AgentDebate(
            council_id=council_id,
            agent_name=agent_name,
            message=message,
            message_type=message_type,
            sentiment=sentiment,
            market_symbol=market_symbol,
            confidence=confidence,
            debate_round=debate_round,
        )

        self.session.add(debate)
        await self.session.commit()
        await self.session.refresh(debate)

        return debate

    # ========================================================================
    # Market Order Methods
    # ========================================================================

    async def get_market_orders(
        self,
        council_id: int,
        status: str | None = None,
        limit: int = 100,
    ) -> list:
        """
        Get market orders for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        status : str | None
            Filter by status (e.g., "open", "closed")
        limit : int
            Maximum number of orders to return

        Returns
        -------
        list
            List of MarketOrder objects
        """
        from app.backend.db.models import MarketOrder

        query = select(MarketOrder).where(MarketOrder.council_id == council_id)

        if status:
            query = query.where(MarketOrder.status == status)

        query = query.order_by(MarketOrder.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_market_order(
        self,
        council_id: int,
        symbol: str,
        order_type: str,
        side: str,
        quantity: float | Decimal,
        entry_price: float | Decimal,
        opened_at,
        status: str = "filled",
        confidence: float | Decimal | None = None,
        position_size_pct: float | Decimal | None = None,
        is_paper_trade: bool = True,
    ):
        """
        Create a market order (spot trading version).

        Parameters
        ----------
        council_id : int
            Council ID
        symbol : str
            Market symbol
        order_type : str
            Order type (e.g., "market", "limit")
        side : str
            Order side ("buy" or "sell" for spot trading)
        quantity : float | Decimal
            Order quantity
        entry_price : float | Decimal
            Entry price
        opened_at : datetime
            When the order was opened
        status : str
            Order status (default "filled" for spot trades)
        confidence : float | Decimal | None
            Agent confidence level (0.0-1.0)
        position_size_pct : float | Decimal | None
            Percentage of capital used
        is_paper_trade : bool
            Whether this is a paper trade

        Returns
        -------
        MarketOrder
            Created market order
        """
        from app.backend.db.models import MarketOrder

        order = MarketOrder(
            council_id=council_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=Decimal(str(quantity)),
            entry_price=Decimal(str(entry_price)),
            opened_at=opened_at,
            status=status,
            confidence=Decimal(str(confidence)) if confidence is not None else None,
            position_size_pct=Decimal(str(position_size_pct)) if position_size_pct is not None else None,
            is_paper_trade=is_paper_trade,
        )

        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)

        return order

    async def close_market_order(
        self,
        order_id: int,
        exit_price: float,
        closed_at,
    ):
        """
        Close a market order and update council capital.

        When closing a position:
        1. Calculates realized PnL
        2. Returns capital: position_value + realized_pnl to available capital

        Parameters
        ----------
        order_id : int
            Order ID
        exit_price : float
            Exit price
        closed_at : datetime
            When the order was closed

        Returns
        -------
        MarketOrder | None
            Updated market order if found
        """
        from app.backend.db.models import MarketOrder

        result = await self.session.execute(select(MarketOrder).where(MarketOrder.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            return None

        order.exit_price = Decimal(str(exit_price))
        order.closed_at = closed_at
        order.status = "closed"

        # Calculate PnL based on side
        if order.side == "long":  # Long position: profit when price goes up
            pnl = (Decimal(str(exit_price)) - order.entry_price) * order.quantity
        else:  # Short position: profit when price goes down
            pnl = (order.entry_price - Decimal(str(exit_price))) * order.quantity

        order.pnl = pnl
        order.pnl_percentage = (
            (pnl / (order.entry_price * order.quantity)) * 100 if order.entry_price > 0 else Decimal(0)
        )

        # Get council and update capital
        council = await self.get_council_by_id(order.council_id)
        if council:
            # Capital to return = position value + realized PnL
            position_value = float(order.entry_price * order.quantity)
            capital_to_return = position_value + float(pnl)

            new_current_capital = float(council.current_capital or council.initial_capital) + capital_to_return
            council.current_capital = new_current_capital

        await self.session.commit()
        await self.session.refresh(order)

        return order

    # ========================================================================
    # Performance History Methods
    # ========================================================================

    async def get_performance_history(
        self,
        council_id: int,
        limit: int = 100,
    ) -> list:
        """
        Get performance history for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        limit : int
            Maximum number of snapshots to return

        Returns
        -------
        list
            List of CouncilPerformance objects
        """
        from app.backend.db.models import CouncilPerformance

        result = await self.session.execute(
            select(CouncilPerformance)
            .where(CouncilPerformance.council_id == council_id)
            .order_by(CouncilPerformance.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_council_account_values(
        self,
        days: int = 72,
        limit: int = 1000,
    ) -> dict[int, dict]:
        """
        Get account values for each council separately over time.

        Returns data grouped by council_id so each council can be displayed as a separate line.

        Parameters
        ----------
        days : int
            Number of days to look back
        limit : int
            Maximum number of snapshots per council

        Returns
        -------
        dict[int, dict]
            Dictionary mapping council_id to:
            - council_name: str
            - data_points: list[dict] with keys: timestamp, total_value
            - current_value: float
        """
        from app.backend.db.models import CouncilPerformance
        from collections import defaultdict

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Get all performance snapshots for system councils within time range
        result = await self.session.execute(
            select(
                Council.id.label("council_id"),
                Council.name.label("council_name"),
                CouncilPerformance.timestamp,
                CouncilPerformance.total_value,
                Council.current_capital,
            )
            .join(Council, Council.id == CouncilPerformance.council_id)
            .where(
                and_(
                    Council.is_system.is_(True),
                    CouncilPerformance.timestamp >= cutoff_date,
                )
            )
            .order_by(Council.id, CouncilPerformance.timestamp.asc())
            .limit(limit * 20)  # Get more records for grouping
        )

        rows = result.all()

        # Group by council_id and hour
        councils_data: dict[int, dict[str, any]] = defaultdict(lambda: {
            "council_name": "",
            "hourly_data": defaultdict(float),
            "timestamps": set(),
            "current_value": 0.0,
        })

        for row in rows:
            council_id = row.council_id
            if council_id not in councils_data:
                councils_data[council_id]["council_name"] = row.council_name
                councils_data[council_id]["current_value"] = float(row.current_capital or 0)

            # Round timestamp to nearest hour for grouping
            hour_key = row.timestamp.replace(minute=0, second=0, microsecond=0)
            councils_data[council_id]["hourly_data"][hour_key] = float(row.total_value)
            councils_data[council_id]["timestamps"].add(hour_key)

        # Get current values for councils that might not have snapshots yet
        current_result = await self.session.execute(
            select(
                Council.id,
                Council.name,
                Council.current_capital,
            )
            .where(
                and_(
                    Council.is_system.is_(True),
                    Council.current_capital.is_not(None),
                )
            )
        )

        for row in current_result.all():
            council_id = row.id
            if council_id not in councils_data:
                councils_data[council_id] = {
                    "council_name": row.name,
                    "hourly_data": defaultdict(float),
                    "timestamps": set(),
                    "current_value": float(row.current_capital or 0),
                }
            else:
                councils_data[council_id]["current_value"] = float(row.current_capital or 0)

        # Convert to final format
        result_data = {}
        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        
        for council_id, data in councils_data.items():
            # Convert hourly data to sorted list
            data_points = sorted(
                [
                    {
                        "timestamp": timestamp,
                        "total_value": data["hourly_data"][timestamp],
                    }
                    for timestamp in sorted(data["timestamps"])
                ],
                key=lambda x: x["timestamp"],
            )

            # Add current value if different from last snapshot or no data exists
            if data_points:
                last_value = data_points[-1]["total_value"]
                if abs(data["current_value"] - last_value) > 0.01 or (now - data_points[-1]["timestamp"]).total_seconds() > 3600:
                    data_points.append({
                        "timestamp": now,
                        "total_value": data["current_value"],
                    })
            elif data["current_value"] > 0:
                data_points.append({
                    "timestamp": now,
                    "total_value": data["current_value"],
                })

            result_data[council_id] = {
                "council_name": data["council_name"],
                "data_points": data_points,
                "current_value": data["current_value"],
            }

        return result_data

    async def create_performance_snapshot(
        self,
        council_id: int,
        timestamp,
        total_value: float,
        pnl: float,
        pnl_percentage: float,
        win_rate: float,
        total_trades: int,
        open_positions: int,
    ):
        """
        Create a performance snapshot.

        Parameters
        ----------
        council_id : int
            Council ID
        timestamp : datetime
            Timestamp of snapshot
        total_value : float
            Total portfolio value
        pnl : float
            Profit and loss
        pnl_percentage : float
            PnL percentage
        win_rate : float
            Win rate percentage
        total_trades : int
            Total number of trades
        open_positions : int
            Number of open positions

        Returns
        -------
        CouncilPerformance
            Created performance snapshot
        """
        from app.backend.db.models import CouncilPerformance

        snapshot = CouncilPerformance(
            council_id=council_id,
            timestamp=timestamp,
            total_value=Decimal(str(total_value)),
            pnl=Decimal(str(pnl)),
            pnl_percentage=Decimal(str(pnl_percentage)),
            win_rate=Decimal(str(win_rate)) if win_rate is not None else None,
            total_trades=total_trades,
            open_positions=open_positions,
        )

        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)

        return snapshot

    async def update_council_metrics(self, council_id: int):
        """
        Update council metrics (PnL, win rate, etc.).

        Calculates and updates council performance metrics based on
        current market orders and positions.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        Council | None
            Updated council if found
        """
        from app.backend.db.models import MarketOrder

        council = await self.get_council_by_id(council_id)
        if not council:
            return None

        # Get all closed orders
        closed_orders_result = await self.session.execute(
            select(MarketOrder).where(
                and_(
                    MarketOrder.council_id == council_id,
                    MarketOrder.status == "closed",
                )
            )
        )
        closed_orders = list(closed_orders_result.scalars().all())

        # Get all open orders
        open_orders_result = await self.session.execute(
            select(MarketOrder).where(
                and_(
                    MarketOrder.council_id == council_id,
                    MarketOrder.status == "open",
                )
            )
        )
        open_orders = list(open_orders_result.scalars().all())

        # Calculate realized PnL from closed positions
        total_pnl = sum(order.pnl for order in closed_orders if order.pnl)
        winning_trades = sum(1 for order in closed_orders if order.pnl and order.pnl > 0)
        total_closed = len(closed_orders)
        total_trades = total_closed

        win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0
        pnl_percentage = (total_pnl / council.initial_capital * 100) if council.initial_capital > 0 else 0

        # Calculate capital tied up in open positions
        capital_in_open_positions = sum(float(order.entry_price * order.quantity) for order in open_orders)

        # Calculate current available capital
        # = initial capital + realized gains - capital tied up in open positions
        current_capital = float(council.initial_capital) + float(total_pnl) - capital_in_open_positions

        # Update council
        council.current_capital = current_capital
        council.total_pnl = total_pnl
        council.total_pnl_percentage = Decimal(str(pnl_percentage))
        council.win_rate = Decimal(str(win_rate))
        council.total_trades = total_trades
        council.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(council)

        return council

    # ========================================================================
    # Consensus Decision Methods
    # ========================================================================

    async def create_consensus_decision(
        self,
        council_id: int,
        decision: str,
        symbol: str,
        confidence: float,
        votes_buy: int,
        votes_sell: int,
        votes_hold: int,
        agent_votes: dict,
        council_run_id: int | None = None,
        council_run_cycle_id: int | None = None,
        reasoning: str | None = None,
        market_price: float | None = None,
        market_conditions: dict | None = None,
        was_executed: bool = False,
        market_order_id: int | None = None,
        execution_reason: str | None = None,
        meta_data: dict | None = None,
    ) -> ConsensusDecision:
        """
        Create a consensus decision record.

        Parameters
        ----------
        council_id : int
            Council ID
        decision : str
            Consensus decision (BUY, SELL, HOLD)
        symbol : str
            Trading symbol
        confidence : float
            Average agent confidence (0.0-1.0)
        votes_buy : int
            Number of BUY votes
        votes_sell : int
            Number of SELL votes
        votes_hold : int
            Number of HOLD votes
        agent_votes : dict
            Mapping of agent names to their votes
        council_run_id : int | None
            Associated council run ID
        council_run_cycle_id : int | None
            Associated council run cycle ID
        reasoning : str | None
            Reasoning for the decision
        market_price : float | None
            Market price at time of decision
        market_conditions : dict | None
            Market conditions at time of decision
        was_executed : bool
            Whether the decision resulted in a trade execution
        market_order_id : int | None
            Associated market order ID (if executed)
        execution_reason : str | None
            Reason for execution/non-execution
        meta_data : dict | None
            Additional metadata

        Returns
        -------
        ConsensusDecision
            Created consensus decision
        """
        total_votes = votes_buy + votes_sell + votes_hold

        consensus = ConsensusDecision(
            council_id=council_id,
            council_run_id=council_run_id,
            council_run_cycle_id=council_run_cycle_id,
            decision=decision,
            symbol=symbol,
            confidence=Decimal(str(confidence)),
            votes_buy=votes_buy,
            votes_sell=votes_sell,
            votes_hold=votes_hold,
            total_votes=total_votes,
            agent_votes=agent_votes,
            reasoning=reasoning,
            market_price=Decimal(str(market_price)) if market_price is not None else None,
            market_conditions=market_conditions,
            was_executed=was_executed,
            market_order_id=market_order_id,
            execution_reason=execution_reason,
            meta_data=meta_data,
        )

        self.session.add(consensus)
        await self.session.commit()
        await self.session.refresh(consensus)

        return consensus

    async def get_consensus_decisions(
        self,
        council_id: int,
        decision_type: str | None = None,
        limit: int = 100,
    ) -> list[ConsensusDecision]:
        """
        Get consensus decisions for a council.

        Parameters
        ----------
        council_id : int
            Council ID
        decision_type : str | None
            Filter by decision type (BUY, SELL, HOLD)
        limit : int
            Maximum number of decisions to return

        Returns
        -------
        list[ConsensusDecision]
            List of consensus decisions
        """
        query = select(ConsensusDecision).where(ConsensusDecision.council_id == council_id)

        if decision_type:
            query = query.where(ConsensusDecision.decision == decision_type)

        query = query.order_by(ConsensusDecision.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_consensus_execution(
        self,
        consensus_id: int,
        was_executed: bool,
        market_order_id: int | None = None,
        execution_reason: str | None = None,
    ) -> ConsensusDecision | None:
        """
        Update consensus decision execution status.

        Parameters
        ----------
        consensus_id : int
            Consensus decision ID
        was_executed : bool
            Whether the decision was executed
        market_order_id : int | None
            Associated market order ID
        execution_reason : str | None
            Reason for execution/non-execution

        Returns
        -------
        ConsensusDecision | None
            Updated consensus decision
        """
        result = await self.session.execute(select(ConsensusDecision).where(ConsensusDecision.id == consensus_id))
        consensus = result.scalar_one_or_none()

        if not consensus:
            return None

        consensus.was_executed = was_executed
        consensus.market_order_id = market_order_id
        consensus.execution_reason = execution_reason

        await self.session.commit()
        await self.session.refresh(consensus)

        return consensus

    # ========================================================================
    # Council Run Cycle Methods
    # ========================================================================

    async def create_council_run_cycle(
        self,
        council_run_id: int,
        cycle_number: int,
        started_at: datetime,
        analyst_signals: dict | None = None,
        trading_decisions: dict | None = None,
        market_conditions: dict | None = None,
        trigger_reason: str | None = None,
    ) -> CouncilRunCycle:
        """
        Create a council run cycle.

        Parameters
        ----------
        council_run_id : int
            Council run ID
        cycle_number : int
            Cycle number
        started_at : datetime
            When the cycle started
        analyst_signals : dict | None
            Agent signals from debate
        trading_decisions : dict | None
            Trading decisions made
        market_conditions : dict | None
            Market conditions at cycle start
        trigger_reason : str | None
            Reason for triggering this cycle

        Returns
        -------
        CouncilRunCycle
            Created cycle
        """
        cycle = CouncilRunCycle(
            council_run_id=council_run_id,
            cycle_number=cycle_number,
            started_at=started_at,
            analyst_signals=analyst_signals,
            trading_decisions=trading_decisions,
            market_conditions=market_conditions,
            status="IN_PROGRESS",
            trigger_reason=trigger_reason,
        )

        self.session.add(cycle)
        await self.session.commit()
        await self.session.refresh(cycle)

        return cycle

    async def update_council_run_cycle(
        self,
        cycle_id: int,
        status: str | None = None,
        completed_at: datetime | None = None,
        analyst_signals: dict | None = None,
        trading_decisions: dict | None = None,
        executed_trades: dict | None = None,
        portfolio_snapshot: dict | None = None,
        performance_metrics: dict | None = None,
        error_message: str | None = None,
        llm_calls_count: int | None = None,
        api_calls_count: int | None = None,
    ) -> CouncilRunCycle | None:
        """
        Update a council run cycle.

        Parameters
        ----------
        cycle_id : int
            Cycle ID
        ... (other parameters)

        Returns
        -------
        CouncilRunCycle | None
            Updated cycle
        """
        result = await self.session.execute(select(CouncilRunCycle).where(CouncilRunCycle.id == cycle_id))
        cycle = result.scalar_one_or_none()

        if not cycle:
            return None

        if status is not None:
            cycle.status = status
        if completed_at is not None:
            cycle.completed_at = completed_at
        if analyst_signals is not None:
            cycle.analyst_signals = analyst_signals
        if trading_decisions is not None:
            cycle.trading_decisions = trading_decisions
        if executed_trades is not None:
            cycle.executed_trades = executed_trades
        if portfolio_snapshot is not None:
            cycle.portfolio_snapshot = portfolio_snapshot
        if performance_metrics is not None:
            cycle.performance_metrics = performance_metrics
        if error_message is not None:
            cycle.error_message = error_message
        if llm_calls_count is not None:
            cycle.llm_calls_count = llm_calls_count
        if api_calls_count is not None:
            cycle.api_calls_count = api_calls_count

        await self.session.commit()
        await self.session.refresh(cycle)

        return cycle

    # ========================================================================
    # Council Status Methods
    # ========================================================================

    async def get_council_live_status(self, council_id: int) -> dict:
        """
        Get live status of a council.

        Parameters
        ----------
        council_id : int
            Council ID

        Returns
        -------
        dict
            Dictionary containing:
            - council: Council object
            - latest_cycle: Latest CouncilRunCycle or None
            - open_positions: List of open MarketOrder objects
        """
        from app.backend.db.models import MarketOrder

        council = await self.get_council_by_id(council_id)

        # Get latest council run (using imported CouncilRun from top of file)
        latest_run_result = await self.session.execute(
            select(CouncilRun)
            .where(CouncilRun.council_id == council_id)
            .order_by(CouncilRun.created_at.desc())
            .limit(1)
        )
        latest_run = latest_run_result.scalar_one_or_none()

        # Get latest cycle from the latest run (using imported CouncilRunCycle from top of file)
        latest_cycle = None
        if latest_run:
            latest_cycle_result = await self.session.execute(
                select(CouncilRunCycle)
                .where(CouncilRunCycle.council_run_id == latest_run.id)
                .order_by(CouncilRunCycle.created_at.desc())
                .limit(1)
            )
            latest_cycle = latest_cycle_result.scalar_one_or_none()

        # Get open positions
        open_positions_result = await self.session.execute(
            select(MarketOrder).where(
                and_(
                    MarketOrder.council_id == council_id,
                    MarketOrder.status == "open",
                )
            )
        )
        open_positions = list(open_positions_result.scalars().all())

        return {
            "council": council,
            "latest_cycle": latest_cycle,
            "open_positions": open_positions,
        }


__all__ = ["CouncilRepository"]
