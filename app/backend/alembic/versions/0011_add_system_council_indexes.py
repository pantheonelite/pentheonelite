"""Add system council indexes and aster_order_id column.

Revision ID: 0011
Revises: 0010
Create Date: 2025-10-26 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for system councils and aster_order_id column."""
    # Add index on councils_v2 for fast filtering of system councils
    op.create_index(
        "ix_councils_v2_system_status",
        "councils_v2",
        ["is_system", "status"],
        unique=False,
    )

    # Add aster_order_id column to market_orders table if it exists
    # First check if the table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "market_orders" in inspector.get_table_names():
        # Check if column doesn't already exist
        columns = [col["name"] for col in inspector.get_columns("market_orders")]
        if "aster_order_id" not in columns:
            op.add_column(
                "market_orders",
                sa.Column("aster_order_id", sa.String(length=100), nullable=True),
            )
            # Add index on aster_order_id for lookups
            op.create_index(
                "ix_market_orders_aster_order_id",
                "market_orders",
                ["aster_order_id"],
                unique=False,
            )


def downgrade() -> None:
    """Remove indexes and aster_order_id column."""
    # Drop indexes
    op.drop_index("ix_councils_v2_system_status", table_name="councils_v2")

    # Drop aster_order_id column and index if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "market_orders" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("market_orders")]
        if "aster_order_id" in columns:
            op.drop_index("ix_market_orders_aster_order_id", table_name="market_orders")
            op.drop_column("market_orders", "aster_order_id")
