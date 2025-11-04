"""make_wallet_council_id_nullable

Revision ID: a1b2c3d4e5f6
Revises: 06dfdd78c85d
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "06dfdd78c85d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make council_id nullable in council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        # Get existing columns to check current nullable status
        existing_columns = {col["name"]: col for col in inspector.get_columns("council_wallets")}
        
        if "council_id" in existing_columns:
            # Check if council_id is currently nullable
            council_id_col = existing_columns["council_id"]
            if not council_id_col["nullable"]:
                # Drop the unique constraint on council_id first (if exists)
                # Check for unique constraint
                unique_constraints = [
                    const["name"] for const in inspector.get_unique_constraints("council_wallets")
                ]
                
                # Drop unique constraint if it exists
                if "uq_council_wallets_council_id" in unique_constraints:
                    op.drop_constraint("uq_council_wallets_council_id", "council_wallets", type_="unique")
                
                # Drop the unique index
                try:
                    op.drop_index("ix_council_wallets_council_id", table_name="council_wallets")
                except Exception:
                    pass  # Index might not exist
                
                # Alter column to make it nullable
                op.alter_column(
                    "council_wallets",
                    "council_id",
                    existing_type=sa.Integer(),
                    nullable=True,
                )
                
                # Recreate index (non-unique now since council_id can be NULL)
                # PostgreSQL allows multiple NULL values, so we make it non-unique
                op.create_index(
                    op.f("ix_council_wallets_council_id"),
                    "council_wallets",
                    ["council_id"],
                    unique=False,
                )
                
                print("✓ Made council_id nullable in council_wallets table")
            else:
                print("ℹ️  council_id is already nullable, skipping")
        else:
            print("ℹ️  Column 'council_id' not found in 'council_wallets' table")
    else:
        print("ℹ️  Table 'council_wallets' does not exist, skipping")


def downgrade() -> None:
    """Revert council_id to non-nullable in council_wallets table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        existing_columns = {col["name"]: col for col in inspector.get_columns("council_wallets")}
        
        if "council_id" in existing_columns:
            council_id_col = existing_columns["council_id"]
            
            if council_id_col["nullable"]:
                # First, set all NULL council_id values to a default (or delete those rows)
                # For safety, we'll check if there are any NULL values
                result = conn.execute(
                    sa.text("SELECT COUNT(*) FROM council_wallets WHERE council_id IS NULL")
                )
                null_count = result.scalar()
                
                if null_count > 0:
                    # Delete wallets with NULL council_id (or you could set a default)
                    op.execute(sa.text("DELETE FROM council_wallets WHERE council_id IS NULL"))
                
                # Drop the index
                op.drop_index("ix_council_wallets_council_id", table_name="council_wallets")
                
                # Alter column to make it non-nullable
                op.alter_column(
                    "council_wallets",
                    "council_id",
                    existing_type=sa.Integer(),
                    nullable=False,
                )
                
                # Recreate unique constraint and index
                op.create_unique_constraint(
                    "uq_council_wallets_council_id",
                    "council_wallets",
                    ["council_id"],
                )
                op.create_index(
                    op.f("ix_council_wallets_council_id"),
                    "council_wallets",
                    ["council_id"],
                    unique=True,
                )
                
                print("✓ Reverted council_id to non-nullable in council_wallets table")
            else:
                print("ℹ️  council_id is already non-nullable, skipping")

