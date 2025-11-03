"""Update councils table for position-based trading.

Revision ID: 0023
Revises: 0022
Create Date: 2025-11-01 00:04:00.000000

Adds trading_mode, trading_type, and comprehensive metrics tracking.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update councils table with new fields for position-based trading."""
    # Remove old spot-specific fields
    op.drop_column("councils", "available_capital")
    op.drop_column("councils", "portfolio_holdings")

    # Trading Configuration
    op.add_column("councils", sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="paper"))
    op.add_column(
        "councils", sa.Column("trading_type", sa.String(length=10), nullable=False, server_default="futures")
    )

    # Account Metrics
    op.add_column(
        "councils",
        sa.Column("total_account_value", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "councils",
        sa.Column("available_balance", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "councils", sa.Column("used_balance", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
    )

    # Futures-Specific
    op.add_column(
        "councils",
        sa.Column("total_margin_used", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "councils",
        sa.Column("total_unrealized_profit", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )

    # Position/Holding Counts
    op.add_column("councils", sa.Column("open_futures_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("councils", sa.Column("closed_futures_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("councils", sa.Column("active_spot_holdings", sa.Integer(), nullable=False, server_default="0"))

    # PnL Tracking
    op.add_column(
        "councils",
        sa.Column("total_realized_pnl", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "councils", sa.Column("net_pnl", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils", sa.Column("total_fees", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils",
        sa.Column("total_funding_fees", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )

    # Trading Statistics
    op.add_column(
        "councils", sa.Column("average_leverage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils",
        sa.Column("average_confidence", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
    )
    op.add_column(
        "councils", sa.Column("biggest_win", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils", sa.Column("biggest_loss", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
    )

    # Hold Time Statistics
    op.add_column(
        "councils", sa.Column("long_hold_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils", sa.Column("short_hold_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
    )
    op.add_column(
        "councils", sa.Column("flat_hold_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="100")
    )


def downgrade() -> None:
    """Revert councils table changes."""
    # Remove new fields
    op.drop_column("councils", "flat_hold_pct")
    op.drop_column("councils", "short_hold_pct")
    op.drop_column("councils", "long_hold_pct")
    op.drop_column("councils", "biggest_loss")
    op.drop_column("councils", "biggest_win")
    op.drop_column("councils", "average_confidence")
    op.drop_column("councils", "average_leverage")
    op.drop_column("councils", "total_funding_fees")
    op.drop_column("councils", "total_fees")
    op.drop_column("councils", "net_pnl")
    op.drop_column("councils", "total_realized_pnl")
    op.drop_column("councils", "active_spot_holdings")
    op.drop_column("councils", "closed_futures_count")
    op.drop_column("councils", "open_futures_count")
    op.drop_column("councils", "total_unrealized_profit")
    op.drop_column("councils", "total_margin_used")
    op.drop_column("councils", "used_balance")
    op.drop_column("councils", "available_balance")
    op.drop_column("councils", "total_account_value")
    op.drop_column("councils", "trading_type")
    op.drop_column("councils", "trading_mode")

    # Restore old fields
    op.add_column("councils", sa.Column("portfolio_holdings", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("councils", sa.Column("available_capital", sa.Numeric(precision=20, scale=2), nullable=True))
