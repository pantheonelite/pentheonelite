"""add_wallet_exchange_column

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add exchange column to council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        # Get existing columns
        existing_columns = {col["name"] for col in inspector.get_columns("council_wallets")}
        
        # Check if old "type" column exists and rename it, or add new "exchange" column
        if "type" in existing_columns and "exchange" not in existing_columns:
            # Rename "type" column to "exchange"
            op.alter_column("council_wallets", "type", new_column_name="exchange")
            print("✓ Renamed 'type' column to 'exchange' in council_wallets table")
        elif "exchange" not in existing_columns:
            # Add exchange column with default value "binance"
            op.add_column(
                "council_wallets",
                sa.Column(
                    "exchange",
                    sa.String(length=50),
                    nullable=False,
                    server_default="binance",
                ),
            )
            
            # Update existing rows to have exchange "binance" (already done by server_default, but explicit update for clarity)
            op.execute(
                sa.text("UPDATE council_wallets SET exchange = 'binance' WHERE exchange IS NULL OR exchange = ''")
            )
            
            print("✓ Added exchange column to council_wallets table")
        else:
            print("ℹ️  Column 'exchange' already exists in 'council_wallets' table, skipping")
    else:
        print("ℹ️  Table 'council_wallets' does not exist, skipping")


def downgrade() -> None:
    """Remove exchange column from council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("council_wallets")}
        
        if "exchange" in existing_columns:
            op.drop_column("council_wallets", "exchange")
            print("✓ Removed exchange column from council_wallets table")
        else:
            print("ℹ️  Column 'exchange' does not exist in 'council_wallets' table, skipping")

