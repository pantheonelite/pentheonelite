"""Unit tests for FuturesPositionService."""

from decimal import Decimal

import pytest

from app.backend.services.futures_position_service import FuturesPositionService


class TestFuturesPositionService:
    """Test futures position service."""

    @pytest.fixture
    async def futures_service(self, db_session):
        """Create futures position service."""
        return FuturesPositionService(db_session)

    @pytest.mark.asyncio
    async def test_open_long_position(self, db_session, test_council, futures_service):
        """Test opening LONG position."""
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=10,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
            confidence=Decimal("0.75"),
        )

        assert position.id is not None
        assert position.position_side == "LONG"
        assert position.status == "OPEN"
        assert position.leverage == 10
        assert position.notional == Decimal(
            "50"
        )  # 0.001 * 50000 = 50 (Binance shows without leverage)
        assert position.unrealized_profit == Decimal(0)
        assert position.confidence == Decimal("0.75")

    @pytest.mark.asyncio
    async def test_open_short_position(self, db_session, test_council, futures_service):
        """Test opening SHORT position."""
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="ETHUSDT",
            position_side="SHORT",
            position_amt=Decimal("0.1"),
            entry_price=Decimal("3000"),
            leverage=5,
            margin_type="ISOLATED",
            platform="binance",
            trading_mode="paper",
            liquidation_price=Decimal("3150"),
            isolated_margin=Decimal("60"),  # (0.1 * 3000) / 5
            confidence=Decimal("0.80"),
        )

        assert position.id is not None
        assert position.position_side == "SHORT"
        assert position.margin_type == "ISOLATED"
        assert position.liquidation_price == Decimal("3150")
        assert position.isolated_margin == Decimal("60")

    @pytest.mark.asyncio
    async def test_close_position_with_profit(
        self, db_session, test_council, futures_service
    ):
        """Test closing LONG position with profit."""
        # Open position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=10,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Close with profit: entry 50000 → exit 51000
        closed = await futures_service.aclose_position(
            position_id=position.id,
            exit_price=Decimal("51000"),
            fees=Decimal("0.50"),
        )

        # PnL = (51000 - 50000) * 0.001 - 0.50 = 1.00 - 0.50 = 0.50
        assert closed.status == "CLOSED"
        assert closed.closed_at is not None
        assert closed.realized_pnl == Decimal("0.50")
        assert closed.mark_price == Decimal("51000")

    @pytest.mark.asyncio
    async def test_close_position_with_loss(
        self, db_session, test_council, futures_service
    ):
        """Test closing SHORT position with loss."""
        # Open SHORT position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="ETHUSDT",
            position_side="SHORT",
            position_amt=Decimal("0.1"),
            entry_price=Decimal("3000"),
            leverage=5,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Close with loss: entry 3000 → exit 3100 (price went up, bad for SHORT)
        closed = await futures_service.aclose_position(
            position_id=position.id,
            exit_price=Decimal("3100"),
            fees=Decimal("0.30"),
        )

        # PnL = (3000 - 3100) * 0.1 - 0.30 = -10 - 0.30 = -10.30
        assert closed.status == "CLOSED"
        assert closed.realized_pnl == Decimal("-10.30")

    @pytest.mark.asyncio
    async def test_update_unrealized_pnl_long(
        self, db_session, test_council, futures_service
    ):
        """Test unrealized PnL calculation for LONG position."""
        # Open LONG position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=10,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Update mark price (price went up)
        updated = await futures_service.aupdate_mark_price(
            position_id=position.id,
            mark_price=Decimal("52000"),
            liquidation_price=Decimal("45500"),
        )

        # LONG: (52000 - 50000) * 0.001 = 2.00 profit
        assert updated.unrealized_profit == Decimal("2.00")
        assert updated.mark_price == Decimal("52000")
        assert updated.notional == Decimal("52")  # 0.001 * 52000
        assert updated.liquidation_price == Decimal("45500")
        assert updated.max_notional == Decimal("52")

    @pytest.mark.asyncio
    async def test_update_unrealized_pnl_short(
        self, db_session, test_council, futures_service
    ):
        """Test unrealized PnL calculation for SHORT position."""
        # Open SHORT position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="ETHUSDT",
            position_side="SHORT",
            position_amt=Decimal("0.1"),
            entry_price=Decimal("3000"),
            leverage=5,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Update mark price (price went down - good for SHORT)
        updated = await futures_service.aupdate_mark_price(
            position_id=position.id,
            mark_price=Decimal("2900"),
        )

        # SHORT: (3000 - 2900) * 0.1 = 10.00 profit
        assert updated.unrealized_profit == Decimal("10.00")
        assert updated.mark_price == Decimal("2900")

    @pytest.mark.asyncio
    async def test_get_open_positions(self, db_session, test_council, futures_service):
        """Test getting open positions."""
        # Open multiple positions
        await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=10,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="ETHUSDT",
            position_side="SHORT",
            position_amt=Decimal("0.1"),
            entry_price=Decimal("3000"),
            leverage=5,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Get all open positions
        positions = await futures_service.aget_open_positions(test_council.id)
        assert len(positions) == 2

        # Get specific symbol
        btc_positions = await futures_service.aget_open_positions(
            test_council.id, "BTCUSDT"
        )
        assert len(btc_positions) == 1
        assert btc_positions[0].symbol == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_position_history(self, db_session, test_council, futures_service):
        """Test getting position history."""
        # Open and close a position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=10,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        await futures_service.aclose_position(
            position_id=position.id,
            exit_price=Decimal("51000"),
        )

        # Get history
        history = await futures_service.aget_position_history(test_council.id)
        assert len(history) == 1
        assert history[0].status == "CLOSED"

    @pytest.mark.asyncio
    async def test_max_notional_tracking(
        self, db_session, test_council, futures_service
    ):
        """Test that max_notional is tracked correctly."""
        # Open position
        position = await futures_service.aopen_position(
            council_id=test_council.id,
            symbol="BTCUSDT",
            position_side="LONG",
            position_amt=Decimal("0.001"),
            entry_price=Decimal("50000"),
            leverage=1,
            margin_type="CROSSED",
            platform="binance",
            trading_mode="paper",
        )

        # Update prices (price increases)
        await futures_service.aupdate_mark_price(position.id, Decimal("51000"))
        await futures_service.aupdate_mark_price(position.id, Decimal("52000"))
        await futures_service.aupdate_mark_price(position.id, Decimal("51500"))

        updated = await futures_service.repo.get_by_id(position.id)
        # Max should be 52 (0.001 * 52000)
        assert updated.max_notional == Decimal("52")
