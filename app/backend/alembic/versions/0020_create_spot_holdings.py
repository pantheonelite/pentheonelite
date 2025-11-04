"""Create spot_holdings table.

Revision ID: 0020
Revises: 0019
Create Date: 2025-11-01 00:01:00.000000

Matches Binance Spot API terminology for spot asset holdings.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create spot_holdings table with Binance Spot API terminology."""
    op.create_table(
        "spot_holdings",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        # Asset Identity
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("base_asset", sa.String(length=10), nullable=False),  # e.g., "BTC"
        sa.Column("quote_asset", sa.String(length=10), nullable=False),  # e.g., "USDT"
        # Holding Quantities (Binance Spot standard)
        sa.Column("free", sa.Numeric(precision=20, scale=8), nullable=False),  # Available balance
        sa.Column("locked", sa.Numeric(precision=20, scale=8), nullable=False, server_default="0"),  # Locked in orders
        sa.Column("total", sa.Numeric(precision=20, scale=8), nullable=False),  # Total = free + locked
        # Cost Basis
        sa.Column("average_cost", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("total_cost", sa.Numeric(precision=20, scale=2), nullable=False),
        # Current Value
        sa.Column("current_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("current_value", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(precision=20, scale=2), nullable=True),
        # Platform Integration
        sa.Column("platform", sa.String(length=20), nullable=False),  # "binance" | "aster"
        sa.Column("trading_mode", sa.String(length=10), nullable=False),  # "paper" | "real"
        # Status
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),  # "ACTIVE" | "CLOSED"
        # Lifecycle
        sa.Column("first_acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "council_id", "symbol", "platform", "trading_mode", name="uq_spot_council_symbol_platform_mode"
        ),
    )

    # Create indexes
    op.create_index("idx_spot_council", "spot_holdings", ["council_id"])
    op.create_index("idx_spot_symbol", "spot_holdings", ["symbol"])
    op.create_index("idx_spot_status", "spot_holdings", ["status"])


def downgrade() -> None:
    """Drop spot_holdings table."""
    op.drop_index("idx_spot_status", table_name="spot_holdings")
    op.drop_index("idx_spot_symbol", table_name="spot_holdings")
    op.drop_index("idx_spot_council", table_name="spot_holdings")
    op.drop_table("spot_holdings")
