"""Create minimal users table for local testing.

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-25 21:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create minimal users table for local testing."""
    print("Creating minimal users table for local testing...")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("wallet_address", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_wallet_address", "users", ["wallet_address"], unique=True)

    print("  ✓ Created users table")

    # Insert a default test user
    op.execute(
        """
        INSERT INTO users (id, email, username, wallet_address, created_at)
        VALUES (1, 'test@crypto-pantheon.local', 'Test User', '0x0000000000000000000000000000000000000000', now())
        """
    )

    print("  ✓ Created default test user (id=1, email=test@crypto-pantheon.local)")

    # Now add the foreign key constraints that we skipped in migration 0008
    print("Adding foreign key constraints to councils_v2 tables...")

    op.create_foreign_key("fk_councils_v2_user_id", "councils_v2", "users", ["user_id"], ["id"], ondelete="CASCADE")
    print("  ✓ Added FK: councils_v2.user_id → users.id")

    op.create_foreign_key(
        "fk_council_runs_v2_user_id", "council_runs_v2", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    print("  ✓ Added FK: council_runs_v2.user_id → users.id")

    op.create_foreign_key(
        "fk_market_orders_user_id", "market_orders", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    print("  ✓ Added FK: market_orders.user_id → users.id")

    print("✓ Minimal users table created successfully!")


def downgrade() -> None:
    """Drop foreign key constraints and users table."""
    # Drop foreign key constraints first
    op.drop_constraint("fk_market_orders_user_id", "market_orders", type_="foreignkey")
    op.drop_constraint("fk_council_runs_v2_user_id", "council_runs_v2", type_="foreignkey")
    op.drop_constraint("fk_councils_v2_user_id", "councils_v2", type_="foreignkey")

    # Drop users table
    op.drop_index("idx_users_wallet_address", "users")
    op.drop_index("idx_users_email", "users")
    op.drop_table("users")
