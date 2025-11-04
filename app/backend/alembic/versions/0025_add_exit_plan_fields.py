"""Add exit plan fields to futures_positions.

Revision ID: 0025
Revises: 0024
Create Date: 2025-11-02 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add exit plan fields to futures_positions table."""
    # Add stop loss fields
    op.add_column(
        "futures_positions",
        sa.Column("stop_loss_price", sa.Numeric(20, 8), nullable=True),
    )
    op.add_column(
        "futures_positions",
        sa.Column("stop_loss_order_id", sa.String(100), nullable=True),
    )

    # Add take profit short-term fields
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_short", sa.Numeric(20, 8), nullable=True),
    )
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_short_order_id", sa.String(100), nullable=True),
    )

    # Add take profit mid-term fields
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_mid", sa.Numeric(20, 8), nullable=True),
    )
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_mid_order_id", sa.String(100), nullable=True),
    )

    # Add take profit long-term fields
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_long", sa.Numeric(20, 8), nullable=True),
    )
    op.add_column(
        "futures_positions",
        sa.Column("take_profit_long_order_id", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    """Remove exit plan fields from futures_positions table."""
    op.drop_column("futures_positions", "take_profit_long_order_id")
    op.drop_column("futures_positions", "take_profit_long")
    op.drop_column("futures_positions", "take_profit_mid_order_id")
    op.drop_column("futures_positions", "take_profit_mid")
    op.drop_column("futures_positions", "take_profit_short_order_id")
    op.drop_column("futures_positions", "take_profit_short")
    op.drop_column("futures_positions", "stop_loss_order_id")
    op.drop_column("futures_positions", "stop_loss_price")
