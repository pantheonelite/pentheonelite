"""add_wallet_name_column

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-01-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add name column to council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        # Get existing columns
        existing_columns = {col["name"] for col in inspector.get_columns("council_wallets")}
        
        if "name" not in existing_columns:
            # Add name column as nullable
            op.add_column(
                "council_wallets",
                sa.Column(
                    "name",
                    sa.String(length=200),
                    nullable=True,
                ),
            )
            print("✓ Added name column to council_wallets table")
        else:
            print("ℹ️  Column 'name' already exists in 'council_wallets' table, skipping")
    else:
        print("ℹ️  Table 'council_wallets' does not exist, skipping")


def downgrade() -> None:
    """Remove name column from council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("council_wallets")}
        
        if "name" in existing_columns:
            op.drop_column("council_wallets", "name")
            print("✓ Removed name column from council_wallets table")
        else:
            print("ℹ️  Column 'name' does not exist in 'council_wallets' table, skipping")

