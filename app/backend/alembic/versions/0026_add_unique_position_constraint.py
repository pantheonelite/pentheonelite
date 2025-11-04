"""Add unique constraint for open positions.

Revision ID: 0026
Revises: 0025
Create Date: 2025-11-02 00:00:01.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraint to prevent duplicate open positions."""
    # First, consolidate duplicate OPEN positions
    # This SQL will merge duplicates by keeping the first (oldest) position
    # and updating its position_amt to sum of all duplicates
    op.execute("""
        WITH duplicates AS (
            SELECT
                council_id,
                symbol,
                position_side,
                platform,
                COUNT(*) as dup_count,
                MIN(id) as keep_id,
                SUM(position_amt) as total_amt,
                -- Weighted average entry price
                SUM(position_amt * entry_price) / SUM(position_amt) as avg_entry
            FROM futures_positions
            WHERE status = 'OPEN'
            GROUP BY council_id, symbol, position_side, platform
            HAVING COUNT(*) > 1
        )
        UPDATE futures_positions fp
        SET
            position_amt = d.total_amt,
            entry_price = d.avg_entry,
            notional = d.total_amt * mark_price,
            updated_at = NOW()
        FROM duplicates d
        WHERE fp.id = d.keep_id;
    """)

    # Delete the duplicate positions (keeping only the consolidated one)
    op.execute("""
        WITH duplicates AS (
            SELECT
                council_id,
                symbol,
                position_side,
                platform,
                MIN(id) as keep_id
            FROM futures_positions
            WHERE status = 'OPEN'
            GROUP BY council_id, symbol, position_side, platform
            HAVING COUNT(*) > 1
        )
        DELETE FROM futures_positions fp
        USING duplicates d
        WHERE fp.council_id = d.council_id
          AND fp.symbol = d.symbol
          AND fp.position_side = d.position_side
          AND fp.platform = d.platform
          AND fp.status = 'OPEN'
          AND fp.id != d.keep_id;
    """)

    # Now create partial unique index for open positions
    # Ensures only one OPEN position per (council_id, symbol, position_side, platform)
    op.create_index(
        "idx_unique_open_position",
        "futures_positions",
        ["council_id", "symbol", "position_side", "platform"],
        unique=True,
        postgresql_where=sa.text("status = 'OPEN'"),
    )


def downgrade() -> None:
    """Remove unique constraint."""
    op.drop_index(
        "idx_unique_open_position",
        table_name="futures_positions",
        postgresql_where=sa.text("status = 'OPEN'"),
    )
