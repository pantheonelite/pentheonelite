"""Tests for portfolio service (spot trading)."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend.services.portfolio_service import PortfolioService


class TestPortfolioService:
    """Test portfolio service functionality."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    async def portfolio_service(self, mock_session):
        """Create portfolio service instance."""
        return PortfolioService(mock_session)

    @pytest.mark.asyncio
    async def test_get_portfolio_paper_trading(self, portfolio_service, mock_session):
        """Test fetching portfolio from DB for paper trading."""
        # Setup mock data
        holdings = [
            MagicMock(
                symbol="BTCUSDT",
                quantity=Decimal("0.5"),
                average_cost=Decimal("50000"),
                total_cost=Decimal("25000"),
            ),
            MagicMock(
                symbol="ETHUSDT",
                quantity=Decimal("2.0"),
                average_cost=Decimal("3000"),
                total_cost=Decimal("6000"),
            ),
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = holdings
        mock_session.execute.return_value = mock_result

        # Test
        portfolio = await portfolio_service.aget_portfolio(
            council_id=1, paper_trading=True
        )

        # Verify
        assert len(portfolio) == 2
        assert portfolio["BTCUSDT"]["quantity"] == Decimal("0.5")
        assert portfolio["BTCUSDT"]["avg_cost"] == Decimal("50000")
        assert portfolio["ETHUSDT"]["quantity"] == Decimal("2.0")

    @pytest.mark.asyncio
    async def test_update_holding_buy(self, portfolio_service, mock_session):
        """Test updating holding after BUY trade."""
        # Setup existing holding
        existing_holding = MagicMock(
            council_id=1,
            symbol="BTCUSDT",
            quantity=Decimal("0.5"),
            average_cost=Decimal("50000"),
            total_cost=Decimal("25000"),
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_holding
        mock_session.execute.return_value = mock_result

        # Test BUY: Add 0.3 BTC at $60000
        await portfolio_service.aupdate_holding(
            council_id=1,
            symbol="BTCUSDT",
            quantity_delta=Decimal("0.3"),
            price=Decimal("60000"),
        )

        # Verify weighted average cost calculation
        # (0.5 * 50000 + 0.3 * 60000) / (0.5 + 0.3) = 53750
        assert existing_holding.quantity == Decimal("0.8")
        assert existing_holding.average_cost == Decimal("53750")
        assert existing_holding.total_cost == Decimal("43000")

    @pytest.mark.asyncio
    async def test_update_holding_sell(self, portfolio_service, mock_session):
        """Test updating holding after SELL trade."""
        # Setup existing holding
        existing_holding = MagicMock(
            council_id=1,
            symbol="BTCUSDT",
            quantity=Decimal("0.5"),
            average_cost=Decimal("50000"),
            total_cost=Decimal("25000"),
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_holding
        mock_session.execute.return_value = mock_result

        # Test SELL: Sell 0.2 BTC
        await portfolio_service.aupdate_holding(
            council_id=1,
            symbol="BTCUSDT",
            quantity_delta=Decimal("-0.2"),
            price=Decimal("60000"),
        )

        # Verify - average cost stays the same, quantity decreases
        assert existing_holding.quantity == Decimal("0.3")
        assert existing_holding.average_cost == Decimal("50000")
        assert existing_holding.total_cost == Decimal("15000")

    @pytest.mark.asyncio
    async def test_calculate_position_size(self, portfolio_service):
        """Test position size calculation based on confidence."""
        available_capital = Decimal("10000")
        confidence = 0.8
        max_position_pct = 0.2

        position_size = portfolio_service.acalculate_position_size(
            available_capital, confidence, max_position_pct
        )

        # Expected: 10000 * 0.8 * 0.2 = 1600
        assert position_size == Decimal("1600")

    @pytest.mark.asyncio
    async def test_get_available_capital_paper(self, portfolio_service, mock_session):
        """Test getting available capital from DB (paper trading)."""
        # Setup mock council
        council = MagicMock(
            id=1,
            available_capital=Decimal("8500"),
            initial_capital=Decimal("10000"),
        )

        portfolio_service.repo = AsyncMock()
        portfolio_service.repo.get_council_by_id.return_value = council

        # Test
        capital = await portfolio_service.aget_available_capital(
            council_id=1, paper_trading=True
        )

        # Verify
        assert capital == Decimal("8500")

    @pytest.mark.asyncio
    async def test_calculate_pnl(self, portfolio_service, mock_session):
        """Test unrealized PnL calculation."""
        # Setup mock portfolio
        portfolio = {
            "BTCUSDT": {
                "quantity": Decimal("0.5"),
                "avg_cost": Decimal("50000"),
                "total_cost": Decimal("25000"),
            },
            "ETHUSDT": {
                "quantity": Decimal("2.0"),
                "avg_cost": Decimal("3000"),
                "total_cost": Decimal("6000"),
            },
        }

        # Mock methods
        portfolio_service.aget_portfolio = AsyncMock(return_value=portfolio)

        # Mock ticker prices
        mock_btc_ticker = MagicMock(price=55000)  # $5k profit per BTC
        mock_eth_ticker = MagicMock(price=3500)  # $500 profit per ETH

        async def mock_get_ticker(symbol):
            if symbol == "BTCUSDT":
                return mock_btc_ticker
            elif symbol == "ETHUSDT":
                return mock_eth_ticker

        portfolio_service.aster_client = AsyncMock()
        portfolio_service.aster_client.aget_ticker = mock_get_ticker

        # Test
        pnl_data = await portfolio_service.acalculate_pnl(
            council_id=1, paper_trading=True
        )

        # Verify
        # BTC PnL: (55000 - 50000) * 0.5 = 2500
        # ETH PnL: (3500 - 3000) * 2.0 = 1000
        # Total: 3500
        assert pnl_data["unrealized_pnl"] == 3500.0
        assert "holdings_pnl" in pnl_data
        assert pnl_data["holdings_pnl"]["BTCUSDT"]["pnl"] == 2500.0
        assert pnl_data["holdings_pnl"]["ETHUSDT"]["pnl"] == 1000.0


class TestPortfolioServiceIntegration:
    """Integration tests for portfolio service (requires test database)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_trade_cycle(self):
        """Test complete trade cycle: BUY -> hold -> SELL."""
        # This would require actual database setup
        # Skipping for now - would be part of integration test suite
        pass
