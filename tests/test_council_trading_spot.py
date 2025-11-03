"""Tests for council trading service (spot trading)."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend.services.council_trading_service import CouncilTradingService


class TestCouncilTradingServiceSpot:
    """Test council trading service spot trading functionality."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    async def trading_service(self, mock_session):
        """Create trading service instance."""
        service = CouncilTradingService(mock_session, paper_trading=True)

        # Mock dependencies
        service.portfolio_service = AsyncMock()
        service.aster_client = AsyncMock()
        service.repo = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_execute_buy_with_sufficient_capital(self, trading_service):
        """Test BUY order with sufficient capital."""
        # Setup consensus
        consensus = {"decision": "BUY", "symbol": "BTCUSDT", "confidence": 0.8}

        # Mock portfolio and capital
        trading_service.portfolio_service.aget_portfolio.return_value = {}
        trading_service.portfolio_service.aget_available_capital.return_value = Decimal(
            "10000"
        )
        trading_service.portfolio_service.acalculate_position_size.return_value = (
            Decimal("1600")
        )

        # Mock price
        mock_ticker = MagicMock(price=50000)
        trading_service.aster_client.aget_ticker.return_value = mock_ticker

        # Mock council
        mock_council = MagicMock(available_capital=Decimal("10000"))
        trading_service.repo.get_council_by_id.return_value = mock_council

        # Mock methods
        trading_service.portfolio_service.aupdate_holding = AsyncMock()
        trading_service.repo.create_market_order = AsyncMock()

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify
        assert result["success"] is True
        assert result["order"] is not None
        assert result["paper_trading"] is True

        # Verify holding was updated (BUY = positive delta)
        trading_service.portfolio_service.aupdate_holding.assert_called_once()
        call_args = trading_service.portfolio_service.aupdate_holding.call_args
        assert call_args[1]["quantity_delta"] > 0

    @pytest.mark.asyncio
    async def test_execute_buy_insufficient_capital(self, trading_service):
        """Test BUY order fails with insufficient capital."""
        # Setup consensus
        consensus = {"decision": "BUY", "symbol": "BTCUSDT", "confidence": 0.8}

        # Mock portfolio and capital - insufficient
        trading_service.portfolio_service.aget_portfolio.return_value = {}
        trading_service.portfolio_service.aget_available_capital.return_value = Decimal(
            "500"
        )
        trading_service.portfolio_service.acalculate_position_size.return_value = (
            Decimal("1600")
        )

        # Mock price
        mock_ticker = MagicMock(price=50000)
        trading_service.aster_client.aget_ticker.return_value = mock_ticker

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify - should fail
        assert result["success"] is False
        assert result["error"] == "insufficient_capital"

    @pytest.mark.asyncio
    async def test_execute_sell_with_holdings(self, trading_service):
        """Test SELL order with sufficient holdings."""
        # Setup consensus
        consensus = {"decision": "SELL", "symbol": "BTCUSDT", "confidence": 0.8}

        # Mock portfolio with holdings
        portfolio = {
            "BTCUSDT": {"quantity": Decimal("0.5"), "avg_cost": Decimal("50000")}
        }
        trading_service.portfolio_service.aget_portfolio.return_value = portfolio
        trading_service.portfolio_service.aget_available_capital.return_value = Decimal(
            "10000"
        )

        # Mock price
        mock_ticker = MagicMock(price=60000)
        trading_service.aster_client.aget_ticker.return_value = mock_ticker

        # Mock council
        mock_council = MagicMock(available_capital=Decimal("10000"))
        trading_service.repo.get_council_by_id.return_value = mock_council

        # Mock methods
        trading_service.portfolio_service.aupdate_holding = AsyncMock()
        trading_service.repo.create_market_order = AsyncMock()

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify
        assert result["success"] is True
        assert result["order"] is not None

        # Verify holding was updated (SELL = negative delta)
        trading_service.portfolio_service.aupdate_holding.assert_called_once()
        call_args = trading_service.portfolio_service.aupdate_holding.call_args
        assert call_args[1]["quantity_delta"] < 0

    @pytest.mark.asyncio
    async def test_execute_sell_no_holdings(self, trading_service):
        """Test SELL order fails without holdings."""
        # Setup consensus
        consensus = {"decision": "SELL", "symbol": "BTCUSDT", "confidence": 0.8}

        # Mock portfolio without holdings
        trading_service.portfolio_service.aget_portfolio.return_value = {}
        trading_service.portfolio_service.aget_available_capital.return_value = Decimal(
            "10000"
        )

        # Mock price
        mock_ticker = MagicMock(price=60000)
        trading_service.aster_client.aget_ticker.return_value = mock_ticker

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify - should fail
        assert result["success"] is False
        assert result["error"] == "insufficient_holdings"

    @pytest.mark.asyncio
    async def test_execute_hold_decision(self, trading_service):
        """Test HOLD decision skips trading."""
        # Setup consensus
        consensus = {"decision": "HOLD", "symbol": "BTCUSDT", "confidence": 0.6}

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify - should succeed but not execute trade
        assert result["success"] is True
        assert result["order"] is None
        assert result["reason"] == "hold_decision"

    @pytest.mark.asyncio
    async def test_low_confidence_skip(self, trading_service):
        """Test trade is skipped if confidence below threshold."""
        # Setup consensus with low confidence
        consensus = {"decision": "BUY", "symbol": "BTCUSDT", "confidence": 0.3}

        # Execute
        result = await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify - should skip due to low confidence
        assert result["success"] is True
        assert result["order"] is None
        assert result["reason"] == "low_confidence"

    @pytest.mark.asyncio
    async def test_confidence_based_position_sizing(self, trading_service):
        """Test position size scales with confidence."""
        # Setup consensus with 60% confidence
        consensus = {"decision": "BUY", "symbol": "BTCUSDT", "confidence": 0.6}

        # Mock portfolio and capital
        available_capital = Decimal("10000")
        trading_service.portfolio_service.aget_portfolio.return_value = {}
        trading_service.portfolio_service.aget_available_capital.return_value = (
            available_capital
        )

        # Expected position size: 10000 * 0.6 * 0.2 = 1200 (20% max)
        expected_position = Decimal("1200")
        trading_service.portfolio_service.acalculate_position_size.return_value = (
            expected_position
        )

        # Mock price
        mock_ticker = MagicMock(price=50000)
        trading_service.aster_client.aget_ticker.return_value = mock_ticker

        # Mock methods
        mock_council = MagicMock(available_capital=available_capital)
        trading_service.repo.get_council_by_id.return_value = mock_council
        trading_service.portfolio_service.aupdate_holding = AsyncMock()
        trading_service.repo.create_market_order = AsyncMock()

        # Execute
        await trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify position size calculation was called with correct confidence
        trading_service.portfolio_service.acalculate_position_size.assert_called_once_with(
            available_capital, 0.6, trading_service.settings.max_position_pct
        )

    @pytest.mark.asyncio
    async def test_update_pnl(self, trading_service):
        """Test PnL update calculation."""
        # Mock portfolio value and PnL
        trading_service.portfolio_service.aget_portfolio_value.return_value = Decimal(
            "12500"
        )
        trading_service.portfolio_service.acalculate_pnl.return_value = {
            "unrealized_pnl": 2500.0,
            "pnl_percentage": 25.0,
            "holdings_pnl": {},
        }
        trading_service.portfolio_service.aget_portfolio.return_value = {
            "BTCUSDT": {"quantity": Decimal("0.5")}
        }

        # Mock repo methods
        mock_council = MagicMock(win_rate=Decimal("0.6"), total_trades=10)
        trading_service.repo.get_council_by_id.return_value = mock_council
        trading_service.repo.update_performance_metrics = AsyncMock()
        trading_service.repo.create_performance_snapshot = AsyncMock()

        # Execute
        pnl_data = await trading_service.aupdate_pnl(council_id=1)

        # Verify
        assert pnl_data["unrealized_pnl"] == 2500.0
        assert pnl_data["pnl_percentage"] == 25.0

        # Verify metrics were updated
        trading_service.repo.update_performance_metrics.assert_called_once()
        trading_service.repo.create_performance_snapshot.assert_called_once()


class TestCouncilTradingServiceLive:
    """Test live trading mode (non-paper)."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    async def live_trading_service(self, mock_session):
        """Create trading service in live mode."""
        service = CouncilTradingService(mock_session, paper_trading=False)

        # Mock dependencies
        service.portfolio_service = AsyncMock()
        service.aster_client = AsyncMock()
        service.repo = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_live_trade_execution(self, live_trading_service):
        """Test live trade goes through Aster API."""
        # Setup consensus
        consensus = {"decision": "BUY", "symbol": "BTCUSDT", "confidence": 0.8}

        # Mock portfolio from Aster (live mode)
        live_trading_service.portfolio_service.aget_portfolio.return_value = {}
        live_trading_service.portfolio_service.aget_available_capital.return_value = (
            Decimal("10000")
        )
        live_trading_service.portfolio_service.acalculate_position_size.return_value = (
            Decimal("1600")
        )

        # Mock price and order
        mock_ticker = MagicMock(price=50000)
        live_trading_service.aster_client.aget_ticker.return_value = mock_ticker

        mock_order = MagicMock(
            order_id="LIVE_123",
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.032,
            price=50000,
            status="FILLED",
        )
        live_trading_service.aster_client.aplace_order.return_value = mock_order

        # Mock repo
        live_trading_service.repo.create_market_order = AsyncMock()

        # Execute
        result = await live_trading_service.aexecute_consensus_trade(
            council_id=1, consensus=consensus
        )

        # Verify
        assert result["success"] is True
        assert result["order"] == mock_order
        assert result["paper_trading"] is False

        # Verify order was placed via Aster
        live_trading_service.aster_client.aplace_order.assert_called_once()

        # Verify portfolio was NOT manually updated (fetched from Aster on next cycle)
        live_trading_service.portfolio_service.aupdate_holding.assert_not_called()
