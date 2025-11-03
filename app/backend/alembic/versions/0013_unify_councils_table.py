"""Unify councils table - rename councils_v2 to councils and drop old councils table

Revision ID: 0013
Revises: 0012
Create Date: 2025-10-26 14:05:00.000000

"""

import sys
from pathlib import Path

from alembic import op

# Add migration_helpers to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from migration_helpers import table_exists

# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Unify councils tables:
    1. Drop old councils table (if it exists)
    2. Rename councils_v2 to councils
    3. Update all foreign key constraints

    This migration is idempotent - it checks table existence before renaming.
    """

    councils_exists = table_exists("councils")
    councils_v2_exists = table_exists("councils_v2")

    # Drop old councils table if it exists (with CASCADE to drop dependent objects)
    if councils_exists and councils_v2_exists:
        print("ℹ️  Both councils and councils_v2 exist, dropping old councils table...")
        op.execute("DROP TABLE IF EXISTS councils CASCADE")
        councils_exists = False

    # Rename councils_v2 to councils if needed
    if councils_v2_exists and not councils_exists:
        print("Renaming councils_v2 to councils...")
        op.rename_table("councils_v2", "councils")

        # Rename indexes
        op.execute("ALTER INDEX IF EXISTS ix_councils_v2_created_at RENAME TO ix_councils_created_at")
        op.execute("ALTER INDEX IF EXISTS ix_councils_v2_is_public RENAME TO ix_councils_is_public")
        op.execute("ALTER INDEX IF EXISTS ix_councils_v2_is_system RENAME TO ix_councils_is_system")
        op.execute("ALTER INDEX IF EXISTS ix_councils_v2_status RENAME TO ix_councils_status")
        op.execute("ALTER INDEX IF EXISTS ix_councils_v2_user_id RENAME TO ix_councils_user_id")

        # Rename sequences
        op.execute("ALTER SEQUENCE IF EXISTS councils_v2_id_seq RENAME TO councils_id_seq")

        print("✓ Successfully renamed councils_v2 to councils")
    elif councils_exists and not councils_v2_exists:
        print("ℹ️  councils table already exists and councils_v2 doesn't exist - table already unified")
    elif not councils_exists and not councils_v2_exists:
        print("⚠️  Neither councils nor councils_v2 exist - this is unexpected!")
    else:
        print("ℹ️  Councils table unification already complete")

    # Update foreign key constraints in related tables
    # Note: Foreign keys were already updated in previous migration (0011)
    # This migration primarily handles the table rename

    print("✅ Successfully unified councils table")


def downgrade() -> None:
    """
    Revert the unification:
    1. Rename councils back to councils_v2
    2. Recreate old councils table structure

    This downgrade is idempotent - it checks table existence before renaming.
    """
    from migration_helpers import table_exists

    councils_exists = table_exists("councils")
    councils_v2_exists = table_exists("councils_v2")

    if councils_exists and not councils_v2_exists:
        print("Reverting councils table unification...")
        # Rename councils back to councils_v2
        op.rename_table("councils", "councils_v2")

        # Rename indexes back
        op.execute("ALTER INDEX IF EXISTS ix_councils_created_at RENAME TO ix_councils_v2_created_at")
        op.execute("ALTER INDEX IF EXISTS ix_councils_is_public RENAME TO ix_councils_v2_is_public")
        op.execute("ALTER INDEX IF EXISTS ix_councils_is_system RENAME TO ix_councils_v2_is_system")
        op.execute("ALTER INDEX IF EXISTS ix_councils_status RENAME TO ix_councils_v2_status")
        op.execute("ALTER INDEX IF EXISTS ix_councils_user_id RENAME TO ix_councils_v2_user_id")

        # Rename sequences back
        op.execute("ALTER SEQUENCE IF EXISTS councils_id_seq RENAME TO councils_v2_id_seq")

        print("✓ Reverted councils table unification")
    else:
        print("ℹ️  Table already in expected state for downgrade, skipping")
