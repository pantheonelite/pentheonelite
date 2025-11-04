"""Update councils table for position-based trading.

Revision ID: 0023
Revises: 0022
Create Date: 2025-11-01 00:04:00.000000

Adds trading_mode, trading_type, and comprehensive metrics tracking.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update councils table with new fields for position-based trading."""
    # Check existing columns to avoid duplicate column errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col["name"] for col in inspector.get_columns("councils")}
    
    # Remove old spot-specific fields (only if they exist)
    if "available_capital" in existing_columns:
        op.drop_column("councils", "available_capital")
    if "portfolio_holdings" in existing_columns:
        op.drop_column("councils", "portfolio_holdings")

    # Trading Configuration (only add if they don't exist)
    if "trading_mode" not in existing_columns:
        op.add_column("councils", sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="paper"))
    if "trading_type" not in existing_columns:
        op.add_column(
            "councils", sa.Column("trading_type", sa.String(length=10), nullable=False, server_default="futures")
        )

    # Account Metrics (only add if they don't exist)
    if "total_account_value" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("total_account_value", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )
    if "available_balance" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("available_balance", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )
    if "used_balance" not in existing_columns:
        op.add_column(
            "councils", sa.Column("used_balance", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
        )

    # Futures-Specific (only add if they don't exist)
    if "total_margin_used" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("total_margin_used", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )
    if "total_unrealized_profit" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("total_unrealized_profit", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )

    # Position/Holding Counts (only add if they don't exist)
    if "open_futures_count" not in existing_columns:
        op.add_column("councils", sa.Column("open_futures_count", sa.Integer(), nullable=False, server_default="0"))
    if "closed_futures_count" not in existing_columns:
        op.add_column("councils", sa.Column("closed_futures_count", sa.Integer(), nullable=False, server_default="0"))
    if "active_spot_holdings" not in existing_columns:
        op.add_column("councils", sa.Column("active_spot_holdings", sa.Integer(), nullable=False, server_default="0"))

    # PnL Tracking (only add if they don't exist)
    if "total_realized_pnl" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("total_realized_pnl", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )
    if "net_pnl" not in existing_columns:
        op.add_column(
            "councils", sa.Column("net_pnl", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
        )
    if "total_fees" not in existing_columns:
        op.add_column(
            "councils", sa.Column("total_fees", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
        )
    if "total_funding_fees" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("total_funding_fees", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        )

    # Trading Statistics (only add if they don't exist)
    if "average_leverage" not in existing_columns:
        op.add_column(
            "councils", sa.Column("average_leverage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
        )
    if "average_confidence" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column("average_confidence", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
        )
    if "biggest_win" not in existing_columns:
        op.add_column(
            "councils", sa.Column("biggest_win", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
        )
    if "biggest_loss" not in existing_columns:
        op.add_column(
            "councils", sa.Column("biggest_loss", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0")
        )

    # Hold Time Statistics (only add if they don't exist)
    if "long_hold_pct" not in existing_columns:
        op.add_column(
            "councils", sa.Column("long_hold_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
        )
    if "short_hold_pct" not in existing_columns:
        op.add_column(
            "councils", sa.Column("short_hold_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0")
        )
    if "flat_hold_pct" not in existing_columns:
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
