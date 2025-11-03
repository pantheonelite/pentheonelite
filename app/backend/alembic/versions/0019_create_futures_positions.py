"""Create futures_positions table.

Revision ID: 0019
Revises: 0018
Create Date: 2025-11-01 00:00:00.000000

Matches Binance Futures API and Aster Perpetual API terminology exactly.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0019"
down_revision = "023e9897fd38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create futures_positions table with exact Binance/Aster terminology."""
    op.create_table(
        "futures_positions",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        # Position Identity (Binance/Aster standard)
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("position_side", sa.String(length=10), nullable=False),  # "LONG" | "SHORT" | "BOTH"
        # Position Quantities (Binance: positionAmt)
        sa.Column("position_amt", sa.Numeric(precision=20, scale=8), nullable=False),
        # Prices (Binance/Aster standard)
        sa.Column("entry_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("mark_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("liquidation_price", sa.Numeric(precision=20, scale=8), nullable=True),
        # Leverage & Margin (Binance/Aster standard)
        sa.Column("leverage", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("margin_type", sa.String(length=10), nullable=False),  # "ISOLATED" | "CROSSED"
        sa.Column("isolated_margin", sa.Numeric(precision=20, scale=2), nullable=True),
        # Notional Value (Binance standard)
        sa.Column("notional", sa.Numeric(precision=20, scale=2), nullable=True),
        # PnL (Binance: unRealizedProfit)
        sa.Column("unrealized_profit", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(precision=20, scale=2), nullable=True),
        # Platform Integration
        sa.Column("platform", sa.String(length=20), nullable=False),  # "binance" | "aster"
        sa.Column("trading_mode", sa.String(length=10), nullable=False),  # "paper" | "real"
        sa.Column("external_position_id", sa.String(length=100), nullable=True),
        # Status & Lifecycle
        sa.Column("status", sa.String(length=20), nullable=False),  # "OPEN" | "CLOSED" | "LIQUIDATED"
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        # Metrics
        sa.Column("max_notional", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("fees_paid", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        sa.Column("funding_fees", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
        # Agent Decision Context
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("agent_reasoning", sa.Text(), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("idx_futures_council", "futures_positions", ["council_id"])
    op.create_index("idx_futures_symbol", "futures_positions", ["symbol"])
    op.create_index("idx_futures_status", "futures_positions", ["status"])
    op.create_index("idx_futures_opened", "futures_positions", ["opened_at"])
    op.create_index("idx_futures_side", "futures_positions", ["position_side"])


def downgrade() -> None:
    """Drop futures_positions table."""
    op.drop_index("idx_futures_side", table_name="futures_positions")
    op.drop_index("idx_futures_opened", table_name="futures_positions")
    op.drop_index("idx_futures_status", table_name="futures_positions")
    op.drop_index("idx_futures_symbol", table_name="futures_positions")
    op.drop_index("idx_futures_council", table_name="futures_positions")
    op.drop_table("futures_positions")
