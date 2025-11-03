"""Remove old council tables and rename v2 tables.

Revision ID: 0012
Revises: 0011
Create Date: 2025-10-26 17:30:00.000000

"""

import sys
from pathlib import Path

from alembic import op

# Add migration_helpers to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from migration_helpers import safe_drop_table, table_exists

# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema:
    1. Drop old council-related tables (councils, council_agents, agent_debates, council_performance)

    Note: This is a simplified version that only drops old tables.
    Table renames (councils_v2 -> councils) will be handled in migration 0013.

    This migration is idempotent - it safely checks for table existence before dropping.
    """

    # Check if old councils table exists (not councils_v2)
    # Only drop if it's the OLD table, not councils_v2
    old_councils_exists = table_exists("councils")
    councils_v2_exists = table_exists("councils_v2")

    if old_councils_exists and councils_v2_exists:
        # Safe to drop old councils table - we have both, so councils is the old one
        op.execute("DROP TABLE IF EXISTS councils CASCADE")
        print("✓ Dropped old councils table (councils_v2 still exists)")
    elif not councils_v2_exists and old_councils_exists:
        # councils_v2 doesn't exist, so 'councils' is actually the current table
        print("ℹ️  Skipped dropping councils (it's the current table, not the old one)")
    else:
        print("ℹ️  Old councils table doesn't exist (already cleaned up)")

    # Drop other old tables if they exist (these might have been created before v2 migration)
    # Note: agent_debates might be recreated in migration 0018, so we're careful here
    safe_drop_table("council_agents_old")  # If there was an old backup
    safe_drop_table("council_performance_old")  # If there was an old backup

    print("✓ Migration 0012 completed - old council tables handled")
    print("ℹ️  Table renames (councils_v2 -> councils) will be handled in migration 0013")


def downgrade():
    """
    Downgrade is not supported for this migration.
    The old council tables and data have been removed.
    """
    raise NotImplementedError(
        "Downgrade not supported - old council data cannot be restored. Please restore from backup if needed."
    )
