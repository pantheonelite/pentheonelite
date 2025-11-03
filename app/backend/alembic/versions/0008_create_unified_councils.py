"""Create unified councils table.

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-25

This migration creates a new unified 'councils_v2' table that merges
the functionality of 'hedge_fund_flows' and 'councils' tables.

Strategy:
1. Create new councils_v2 table (additive, safe)
2. Create new council_runs_v2 table
3. Keep old tables for backward compatibility during transition
4. Later migration will handle data migration and cleanup
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create unified councils structure."""

    # Create new unified councils_v2 table
    op.create_table(
        "councils_v2",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        # Ownership & Visibility
        sa.Column("user_id", sa.Integer(), nullable=True),  # NULL for system councils (no FK until users table exists)
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default="false"),
        # Basic Info
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("strategy", sa.String(length=100), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        # Configuration (from hedge_fund_flows)
        sa.Column("agents", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("connections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("workflow_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("visual_layout", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Trading Settings
        sa.Column("initial_capital", sa.Numeric(precision=20, scale=2), nullable=False, server_default="100000"),
        sa.Column("risk_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Performance Tracking (from councils)
        sa.Column("current_capital", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_pnl", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("win_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=True, server_default="0"),
        # Status
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        # Analytics
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fork_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forked_from_id", sa.Integer(), nullable=True),
        # Additional metadata
        sa.Column("meta_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        # Note: user_id FK will be added after users table is created (in auth migration)
        # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(["forked_from_id"], ["councils_v2.id"], ondelete="SET NULL"),
    )

    # Create indexes for performance
    op.create_index("idx_councils_v2_user_id", "councils_v2", ["user_id"])
    op.create_index("idx_councils_v2_is_system", "councils_v2", ["is_system"])
    op.create_index("idx_councils_v2_is_public", "councils_v2", ["is_public"])
    op.create_index("idx_councils_v2_status", "councils_v2", ["status"])
    op.create_index("idx_councils_v2_forked_from_id", "councils_v2", ["forked_from_id"])

    # Create unique constraint on user_id + name (allows NULL user_id for system councils)
    op.create_index(
        "idx_councils_v2_user_name_unique",
        "councils_v2",
        ["user_id", "name"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )

    # Create new council_runs_v2 table (replaces hedge_fund_flow_runs)
    op.create_table(
        "council_runs_v2",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        # References
        sa.Column("council_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        # Execution Config
        sa.Column("trading_mode", sa.String(length=50), nullable=False, server_default="backtest"),
        sa.Column("symbols", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("schedule", sa.String(length=50), nullable=True),
        sa.Column("duration", sa.String(length=50), nullable=True),
        # Status
        sa.Column("status", sa.String(length=50), nullable=False, server_default="IDLE"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Results
        sa.Column("request_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("initial_portfolio", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("final_portfolio", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("performance_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Metadata
        sa.Column("run_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_id"], ["councils_v2.id"], ondelete="CASCADE"),
        # Note: user_id FK will be added after users table is created (in auth migration)
        # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index("idx_council_runs_v2_council_id", "council_runs_v2", ["council_id"])
    op.create_index("idx_council_runs_v2_user_id", "council_runs_v2", ["user_id"])
    op.create_index("idx_council_runs_v2_status", "council_runs_v2", ["status"])
    op.create_index("idx_council_runs_v2_trading_mode", "council_runs_v2", ["trading_mode"])

    # Create council_run_cycles_v2 table (replaces hedge_fund_flow_run_cycles)
    op.create_table(
        "council_run_cycles_v2",
        # Primary Key
        sa.Column("id", sa.Integer(), nullable=False),
        # References
        sa.Column("council_run_id", sa.Integer(), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        # Timing
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Data
        sa.Column("analyst_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trading_decisions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("executed_trades", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("portfolio_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("performance_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("market_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Status
        sa.Column("status", sa.String(length=50), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trigger_reason", sa.String(length=100), nullable=True),
        # Metrics
        sa.Column("llm_calls_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("api_calls_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("estimated_cost", sa.String(length=20), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["council_run_id"], ["council_runs_v2.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("idx_council_run_cycles_v2_run_id", "council_run_cycles_v2", ["council_run_id"])
    op.create_index("idx_council_run_cycles_v2_status", "council_run_cycles_v2", ["status"])

    # Update agent_debates to optionally reference new tables
    op.add_column("agent_debates", sa.Column("council_run_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_agent_debates_council_run_id",
        "agent_debates",
        "council_runs_v2",
        ["council_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_agent_debates_council_run_id", "agent_debates", ["council_run_id"])

    # Update market_orders to optionally reference new tables
    op.add_column("market_orders", sa.Column("council_run_id", sa.Integer(), nullable=True))
    op.add_column("market_orders", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_market_orders_council_run_id",
        "market_orders",
        "council_runs_v2",
        ["council_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Note: user_id FK will be added after users table is created (in auth migration)
    # op.create_foreign_key(
    #     'fk_market_orders_user_id',
    #     'market_orders',
    #     'users',
    #     ['user_id'],
    #     ['id'],
    #     ondelete='CASCADE'
    # )
    op.create_index("idx_market_orders_council_run_id", "market_orders", ["council_run_id"])
    op.create_index("idx_market_orders_user_id", "market_orders", ["user_id"])


def downgrade() -> None:
    """Drop unified councils structure."""

    # Drop indexes first
    op.drop_index("idx_market_orders_user_id", "market_orders")
    op.drop_index("idx_market_orders_council_run_id", "market_orders")
    op.drop_index("idx_agent_debates_council_run_id", "agent_debates")

    # Drop foreign keys
    op.drop_constraint("fk_market_orders_user_id", "market_orders", type_="foreignkey")
    op.drop_constraint("fk_market_orders_council_run_id", "market_orders", type_="foreignkey")
    op.drop_constraint("fk_agent_debates_council_run_id", "agent_debates", type_="foreignkey")

    # Drop columns
    op.drop_column("market_orders", "user_id")
    op.drop_column("market_orders", "council_run_id")
    op.drop_column("agent_debates", "council_run_id")

    # Drop indexes for new tables
    op.drop_index("idx_council_run_cycles_v2_status", "council_run_cycles_v2")
    op.drop_index("idx_council_run_cycles_v2_run_id", "council_run_cycles_v2")
    op.drop_index("idx_council_runs_v2_trading_mode", "council_runs_v2")
    op.drop_index("idx_council_runs_v2_status", "council_runs_v2")
    op.drop_index("idx_council_runs_v2_user_id", "council_runs_v2")
    op.drop_index("idx_council_runs_v2_council_id", "council_runs_v2")
    op.drop_index("idx_councils_v2_forked_from_id", "councils_v2")
    op.drop_index("idx_councils_v2_status", "councils_v2")
    op.drop_index("idx_councils_v2_is_public", "councils_v2")
    op.drop_index("idx_councils_v2_is_system", "councils_v2")
    op.drop_index("idx_councils_v2_user_id", "councils_v2")
    op.drop_index("idx_councils_v2_user_name_unique", "councils_v2")

    # Drop tables
    op.drop_table("council_run_cycles_v2")
    op.drop_table("council_runs_v2")
    op.drop_table("councils_v2")
