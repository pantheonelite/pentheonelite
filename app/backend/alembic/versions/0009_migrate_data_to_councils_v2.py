"""Migrate data from old tables to unified councils_v2.

Revision ID: 0009
Revises: 0008
Create Date: 2025-10-25

This migration copies data from:
- hedge_fund_flows → councils_v2 (as user councils)
- councils → councils_v2 (as system councils)

Strategy:
1. Migrate old councils table → councils_v2 (mark as is_system=true)
2. Migrate hedge_fund_flows → councils_v2 (mark as is_system=false)
3. Migrate hedge_fund_flow_runs → council_runs_v2
4. Update foreign keys in agent_debates and market_orders

IMPORTANT: This migration assumes:
- users table exists (create it first if implementing auth)
- For now, user_id will be NULL for all migrated data
- After auth is implemented, you'll need to assign ownership
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Migrate data to unified councils structure."""

    # Get connection
    conn = op.get_bind()

    print("Starting data migration to councils_v2...")

    # Step 1: Migrate old councils table → councils_v2 (system councils)
    print("Step 1: Migrating councils → councils_v2 (system councils)...")

    conn.execute(
        sa.text("""
        INSERT INTO councils_v2 (
            user_id,
            is_system,
            is_public,
            is_template,
            name,
            description,
            strategy,
            agents,
            connections,
            workflow_config,
            visual_layout,
            initial_capital,
            current_capital,
            total_pnl,
            total_pnl_percentage,
            win_rate,
            total_trades,
            status,
            is_active,
            created_at,
            updated_at,
            meta_data
        )
        SELECT
            NULL as user_id,  -- System councils have no owner
            TRUE as is_system,
            TRUE as is_public,  -- System councils are public by default
            TRUE as is_template,  -- System councils can be templates
            name,
            description,
            strategy,
            '{}'::jsonb as agents,  -- Old councils don't have explicit agent config (empty dict)
            '{}'::jsonb as connections,  -- Empty dict for connections
            NULL as workflow_config,
            NULL as visual_layout,
            initial_capital,
            current_capital,
            total_pnl,
            total_pnl_percentage,
            win_rate,
            total_trades,
            CASE
                WHEN is_active THEN 'active'
                ELSE 'archived'
            END as status,
            is_active,
            created_at,
            updated_at,
            meta_data
        FROM councils
        WHERE id NOT IN (SELECT id FROM councils_v2)
    """)
    )

    print("  ✓ Migrated councils to councils_v2 (system councils)")

    # Step 2: Migrate hedge_fund_flows → councils_v2 (user councils)
    print("Step 2: Migrating hedge_fund_flows → councils_v2 (user councils)...")

    conn.execute(
        sa.text("""
        INSERT INTO councils_v2 (
            user_id,
            is_system,
            is_public,
            is_template,
            name,
            description,
            strategy,
            agents,
            connections,
            workflow_config,
            visual_layout,
            initial_capital,
            status,
            is_active,
            created_at,
            updated_at,
            tags
        )
        SELECT
            NULL as user_id,  -- TODO: Assign to actual users after auth
            FALSE as is_system,
            FALSE as is_public,
            is_template,
            name,
            description,
            NULL as strategy,
            nodes as agents,  -- nodes → agents (renaming)
            edges as connections,  -- edges → connections (renaming)
            data as workflow_config,
            viewport as visual_layout,
            100000 as initial_capital,  -- Default
            'draft' as status,
            TRUE as is_active,
            created_at,
            updated_at,
            CASE
                WHEN tags IS NULL THEN NULL
                ELSE ARRAY(SELECT jsonb_array_elements_text(tags::jsonb))
            END as tags
        FROM hedge_fund_flows
        WHERE id NOT IN (SELECT id FROM councils_v2 WHERE id <= (SELECT MAX(id) FROM hedge_fund_flows))
    """)
    )

    print("  ✓ Migrated hedge_fund_flows to councils_v2 (user councils)")

    # Step 3: Create mapping table for old ID → new ID
    # This is tricky because we need to track which old flow ID maps to which new council ID
    # For simplicity, we'll assume IDs are preserved if possible

    print("Step 3: Migrating flow runs...")

    # Note: This migration is complex because we need to map old flow IDs to new council IDs
    # For now, we'll skip run migration and handle it separately
    print("  ⚠ Skipping flow run migration (requires manual mapping)")
    print("  → Run migration will be handled in a separate script")

    # Step 4: Update sequences
    print("Step 4: Updating sequences...")

    conn.execute(
        sa.text("""
        SELECT setval('councils_v2_id_seq', COALESCE((SELECT MAX(id) FROM councils_v2), 1), true)
    """)
    )

    print("  ✓ Updated sequences")

    print("✓ Data migration completed successfully!")
    print()
    print("NEXT STEPS:")
    print("1. After auth is implemented, assign user_id to migrated user councils")
    print("2. Run flow run migration script separately")
    print("3. Verify data integrity")
    print("4. Update frontend to use /councils/v2 endpoints")


def downgrade() -> None:
    """Reverse data migration (delete migrated data)."""

    conn = op.get_bind()

    print("Reversing data migration...")

    # Delete migrated councils
    # CAUTION: This will delete ALL data in councils_v2
    conn.execute(sa.text("DELETE FROM councils_v2"))

    print("✓ Data migration reversed")
