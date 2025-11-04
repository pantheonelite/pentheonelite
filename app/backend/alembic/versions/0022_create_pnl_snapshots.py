"""Create pnl_snapshots table.

Revision ID: 0022
Revises: 0021
Create Date: 2025-11-01 00:03:00.000000

Time-series PnL tracking for both futures positions and spot holdings.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pnl_snapshots table for time-series tracking."""
    op.create_table(
        "pnl_snapshots",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        # Position/Holding Links
        sa.Column("futures_position_id", sa.Integer(), nullable=True),
        sa.Column("spot_holding_id", sa.Integer(), nullable=True),
        # Snapshot Data
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mark_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("notional_value", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        # For futures: liquidation risk
        sa.Column("liquidation_distance_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("margin_ratio", sa.Numeric(precision=5, scale=4), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["futures_position_id"], ["futures_positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["spot_holding_id"], ["spot_holdings.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("idx_pnl_council", "pnl_snapshots", ["council_id"])
    op.create_index("idx_pnl_futures", "pnl_snapshots", ["futures_position_id"])
    op.create_index("idx_pnl_spot", "pnl_snapshots", ["spot_holding_id"])
    op.create_index("idx_pnl_time", "pnl_snapshots", ["snapshot_time"])


def downgrade() -> None:
    """Drop pnl_snapshots table."""
    op.drop_index("idx_pnl_time", table_name="pnl_snapshots")
    op.drop_index("idx_pnl_spot", table_name="pnl_snapshots")
    op.drop_index("idx_pnl_futures", table_name="pnl_snapshots")
    op.drop_index("idx_pnl_council", table_name="pnl_snapshots")
    op.drop_table("pnl_snapshots")
