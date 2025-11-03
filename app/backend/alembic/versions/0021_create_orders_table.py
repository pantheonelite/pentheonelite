"""Create unified orders table.

Revision ID: 0021
Revises: 0020
Create Date: 2025-11-01 00:02:00.000000

Unified orders table for both futures and spot with exact Binance status enums.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create orders table with Binance order status enums."""
    op.create_table(
        "orders",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        # Position/Holding Links
        sa.Column("futures_position_id", sa.Integer(), nullable=True),
        sa.Column("spot_holding_id", sa.Integer(), nullable=True),
        # Order Identity (Binance standard)
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("client_order_id", sa.String(length=100), nullable=True),
        sa.Column("order_id", sa.BigInteger(), nullable=True),  # Exchange order ID
        # Order Details (Binance standard)
        sa.Column("side", sa.String(length=10), nullable=False),  # "BUY" | "SELL"
        sa.Column("type", sa.String(length=30), nullable=False),  # "MARKET" | "LIMIT" | etc.
        sa.Column("position_side", sa.String(length=10), nullable=True),  # "LONG" | "SHORT" | "BOTH" (futures only)
        # Quantities (Binance: origQty, executedQty)
        sa.Column("orig_qty", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("executed_qty", sa.Numeric(precision=20, scale=8), nullable=False, server_default="0"),
        # Prices
        sa.Column("price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("stop_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("avg_price", sa.Numeric(precision=20, scale=8), nullable=True),
        # Order Config (Binance standard)
        sa.Column("time_in_force", sa.String(length=10), nullable=True),  # "GTC" | "IOC" | "FOK"
        sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("close_position", sa.Boolean(), nullable=False, server_default="false"),
        # Status (Binance enum exactly)
        # "NEW" | "PARTIALLY_FILLED" | "FILLED" | "CANCELED" | "REJECTED" | "EXPIRED"
        sa.Column("status", sa.String(length=30), nullable=False),
        # Platform Integration
        sa.Column("platform", sa.String(length=20), nullable=False),  # "binance" | "aster"
        sa.Column("trading_mode", sa.String(length=10), nullable=False),  # "paper" | "real"
        sa.Column("trading_type", sa.String(length=10), nullable=False),  # "futures" | "spot"
        # Timing (Binance standard fields)
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        # Fees & Commission
        sa.Column("commission", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("commission_asset", sa.String(length=10), nullable=True),
        # Agent Context
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        # Metadata
        sa.Column("meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["futures_position_id"], ["futures_positions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["spot_holding_id"], ["spot_holdings.id"], ondelete="SET NULL"),
    )

    # Create indexes
    op.create_index("idx_orders_council", "orders", ["council_id"])
    op.create_index("idx_orders_symbol", "orders", ["symbol"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_futures_pos", "orders", ["futures_position_id"])
    op.create_index("idx_orders_spot_hold", "orders", ["spot_holding_id"])
    op.create_index("idx_orders_external", "orders", ["order_id"])


def downgrade() -> None:
    """Drop orders table."""
    op.drop_index("idx_orders_external", table_name="orders")
    op.drop_index("idx_orders_spot_hold", table_name="orders")
    op.drop_index("idx_orders_futures_pos", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_index("idx_orders_symbol", table_name="orders")
    op.drop_index("idx_orders_council", table_name="orders")
    op.drop_table("orders")
