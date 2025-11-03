"""add_council_performance_table

Revision ID: 023e9897fd38
Revises: 0018
Create Date: 2025-10-29 10:15:27.759910

"""

import sys
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Add migration_helpers to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from migration_helpers import (
    column_exists,
    foreign_key_exists,
    safe_create_index,
    safe_drop_column,
    safe_drop_constraint,
    safe_drop_index,
    table_exists,
)

# revision identifiers, used by Alembic.
revision: str = "023e9897fd38"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Upgrade schema.

    This migration is idempotent - it checks for existing objects before creating/modifying.
    """
    # Create council_agents table if it doesn't exist
    if not table_exists("council_agents"):
        print("Creating council_agents table...")
        op.create_table(
            "council_agents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("council_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("agent_name", sa.String(length=200), nullable=False),
            sa.Column("agent_type", sa.String(length=100), nullable=False),
            sa.Column("role", sa.String(length=100), nullable=True),
            sa.Column("traits", sa.JSON(), nullable=True),
            sa.Column("specialty", sa.String(length=200), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("meta_data", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        print("✓ Created council_agents table")
    else:
        print("ℹ️  council_agents table already exists")

    safe_create_index(op.f("ix_council_agents_council_id"), "council_agents", ["council_id"], unique=False)
    safe_create_index(op.f("ix_council_agents_id"), "council_agents", ["id"], unique=False)

    # Create council_performance table if it doesn't exist
    if not table_exists("council_performance"):
        print("Creating council_performance table...")
        op.create_table(
            "council_performance",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("council_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("total_value", sa.Numeric(precision=20, scale=2), nullable=False),
            sa.Column("pnl", sa.Numeric(precision=20, scale=2), nullable=False),
            sa.Column("pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=False),
            sa.Column("win_rate", sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column("total_trades", sa.Integer(), server_default="0", nullable=False),
            sa.Column("open_positions", sa.Integer(), server_default="0", nullable=False),
            sa.Column("meta_data", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        print("✓ Created council_performance table")
    else:
        print("ℹ️  council_performance table already exists")

    safe_create_index(op.f("ix_council_performance_council_id"), "council_performance", ["council_id"], unique=False)
    safe_create_index(op.f("ix_council_performance_id"), "council_performance", ["id"], unique=False)
    safe_create_index(op.f("ix_council_performance_timestamp"), "council_performance", ["timestamp"], unique=False)

    # API keys constraint and index changes
    safe_drop_constraint(op.f("api_keys_provider_key"), "api_keys", type_="unique")
    safe_drop_index(op.f("ix_api_keys_provider"), table_name="api_keys")
    safe_create_index(op.f("ix_api_keys_provider"), "api_keys", ["provider"], unique=True)

    # Consensus decisions index changes
    safe_drop_index(op.f("ix_consensus_decisions_council_id_created_at"), table_name="consensus_decisions")
    safe_drop_index(op.f("ix_consensus_decisions_decision_created_at"), table_name="consensus_decisions")
    # Council run cycles changes
    if table_exists("council_run_cycles_v2"):
        op.alter_column(
            "council_run_cycles_v2",
            "created_at",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            existing_server_default=sa.text("now()"),
        )
        safe_drop_index(op.f("idx_council_run_cycles_v2_run_id"), table_name="council_run_cycles_v2")
        safe_drop_index(op.f("idx_council_run_cycles_v2_status"), table_name="council_run_cycles_v2")
        safe_create_index(
            op.f("ix_council_run_cycles_v2_council_run_id"), "council_run_cycles_v2", ["council_run_id"], unique=False
        )
        safe_create_index(op.f("ix_council_run_cycles_v2_id"), "council_run_cycles_v2", ["id"], unique=False)
        safe_create_index(op.f("ix_council_run_cycles_v2_status"), "council_run_cycles_v2", ["status"], unique=False)
    # Council runs changes
    if table_exists("council_runs_v2"):
        op.alter_column(
            "council_runs_v2",
            "created_at",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            existing_server_default=sa.text("now()"),
        )
        safe_drop_index(op.f("idx_council_runs_v2_council_id"), table_name="council_runs_v2")
        safe_drop_index(op.f("idx_council_runs_v2_status"), table_name="council_runs_v2")
        safe_drop_index(op.f("idx_council_runs_v2_trading_mode"), table_name="council_runs_v2")
        safe_drop_index(op.f("idx_council_runs_v2_user_id"), table_name="council_runs_v2")
        safe_create_index(op.f("ix_council_runs_v2_council_id"), "council_runs_v2", ["council_id"], unique=False)
        safe_create_index(op.f("ix_council_runs_v2_id"), "council_runs_v2", ["id"], unique=False)
        safe_create_index(op.f("ix_council_runs_v2_status"), "council_runs_v2", ["status"], unique=False)
        safe_create_index(op.f("ix_council_runs_v2_trading_mode"), "council_runs_v2", ["trading_mode"], unique=False)
        safe_create_index(op.f("ix_council_runs_v2_user_id"), "council_runs_v2", ["user_id"], unique=False)
    # Councils table changes
    if table_exists("councils"):
        op.alter_column(
            "councils",
            "created_at",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            existing_server_default=sa.text("now()"),
        )
        # Drop old v2-style indexes
        safe_drop_index(op.f("idx_councils_v2_forked_from_id"), table_name="councils")
        safe_drop_index(op.f("idx_councils_v2_is_public"), table_name="councils")
        safe_drop_index(op.f("idx_councils_v2_is_system"), table_name="councils")
        safe_drop_index(op.f("idx_councils_v2_status"), table_name="councils")
        safe_drop_index(op.f("idx_councils_v2_user_id"), table_name="councils")
        safe_drop_index(op.f("idx_councils_v2_user_name_unique"), table_name="councils")
        safe_drop_index(op.f("ix_councils_v2_system_status"), table_name="councils")

        # Create new indexes
        safe_create_index(op.f("ix_councils_forked_from_id"), "councils", ["forked_from_id"], unique=False)
        safe_create_index(op.f("ix_councils_id"), "councils", ["id"], unique=False)
        safe_create_index(op.f("ix_councils_is_public"), "councils", ["is_public"], unique=False)
        safe_create_index(op.f("ix_councils_is_system"), "councils", ["is_system"], unique=False)
        safe_create_index(op.f("ix_councils_user_id"), "councils", ["user_id"], unique=False)
    # Hedge fund flow changes
    if table_exists("hedge_fund_flow_run_cycles"):
        safe_drop_index(op.f("ix_hedge_fund_flow_run_cycles_cycle_number"), table_name="hedge_fund_flow_run_cycles")
        safe_drop_index(op.f("ix_hedge_fund_flow_run_cycles_started_at"), table_name="hedge_fund_flow_run_cycles")
        safe_drop_index(op.f("ix_hedge_fund_flow_run_cycles_status"), table_name="hedge_fund_flow_run_cycles")

    if table_exists("hedge_fund_flow_run_cycles") and table_exists("hedge_fund_flow_runs"):
        # Add foreign key if it doesn't exist
        if not foreign_key_exists("hedge_fund_flow_run_cycles", "flow_run_id", "hedge_fund_flow_runs"):
            op.create_foreign_key(None, "hedge_fund_flow_run_cycles", "hedge_fund_flow_runs", ["flow_run_id"], ["id"])

    if table_exists("hedge_fund_flow_runs") and table_exists("hedge_fund_flows"):
        # Add foreign key if it doesn't exist
        if not foreign_key_exists("hedge_fund_flow_runs", "flow_id", "hedge_fund_flows"):
            op.create_foreign_key(None, "hedge_fund_flow_runs", "hedge_fund_flows", ["flow_id"], ["id"])

    if table_exists("hedge_fund_flows") and column_exists("hedge_fund_flows", "is_template"):
        op.alter_column("hedge_fund_flows", "is_template", existing_type=sa.BOOLEAN(), nullable=False)
    # Market orders refactoring
    if table_exists("market_orders"):
        safe_drop_index(op.f("idx_market_orders_council_run_id"), table_name="market_orders")
        safe_drop_index(op.f("idx_market_orders_user_id"), table_name="market_orders")
        safe_drop_index(op.f("ix_market_orders_aster_order_id"), table_name="market_orders")
        safe_drop_constraint(op.f("fk_market_orders_user_id"), "market_orders", type_="foreignkey")
        safe_drop_constraint(op.f("fk_market_orders_council_run_id"), "market_orders", type_="foreignkey")

        # Add new foreign key to councils
        if column_exists("market_orders", "council_id") and not foreign_key_exists(
            "market_orders", "council_id", "councils"
        ):
            op.create_foreign_key(None, "market_orders", "councils", ["council_id"], ["id"], ondelete="CASCADE")

        # Drop old columns
        safe_drop_column("market_orders", "council_run_id")
        safe_drop_column("market_orders", "aster_order_id")
        safe_drop_column("market_orders", "user_id")
    # Portfolio holdings changes
    if table_exists("portfolio_holdings"):
        if column_exists("portfolio_holdings", "created_at"):
            op.alter_column(
                "portfolio_holdings",
                "created_at",
                existing_type=postgresql.TIMESTAMP(timezone=True),
                nullable=True,
                existing_server_default=sa.text("now()"),
            )
        if column_exists("portfolio_holdings", "updated_at"):
            op.alter_column(
                "portfolio_holdings",
                "updated_at",
                existing_type=postgresql.TIMESTAMP(timezone=True),
                nullable=True,
                existing_server_default=sa.text("now()"),
            )
        safe_drop_constraint(op.f("uq_council_symbol"), "portfolio_holdings", type_="unique")
        safe_create_index(op.f("ix_portfolio_holdings_id"), "portfolio_holdings", ["id"], unique=False)
    # Users table index changes
    if table_exists("users"):
        safe_drop_index(op.f("idx_users_email"), table_name="users")
        safe_drop_index(op.f("idx_users_wallet_address"), table_name="users")
        safe_create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        safe_create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        safe_create_index(op.f("ix_users_wallet_address"), "users", ["wallet_address"], unique=True)

    print("✓ Migration 023e9897fd38 completed successfully")


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_users_wallet_address"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.create_index(op.f("idx_users_wallet_address"), "users", ["wallet_address"], unique=True)
    op.create_index(op.f("idx_users_email"), "users", ["email"], unique=True)
    op.drop_index(op.f("ix_portfolio_holdings_id"), table_name="portfolio_holdings")
    op.create_unique_constraint(
        op.f("uq_council_symbol"), "portfolio_holdings", ["council_id", "symbol"], postgresql_nulls_not_distinct=False
    )
    op.alter_column(
        "portfolio_holdings",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "portfolio_holdings",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.add_column("market_orders", sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column(
        "market_orders", sa.Column("aster_order_id", sa.VARCHAR(length=100), autoincrement=False, nullable=True)
    )
    op.add_column("market_orders", sa.Column("council_run_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, "market_orders", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_market_orders_council_run_id"),
        "market_orders",
        "council_runs_v2",
        ["council_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_market_orders_user_id"), "market_orders", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index(op.f("ix_market_orders_aster_order_id"), "market_orders", ["aster_order_id"], unique=False)
    op.create_index(op.f("idx_market_orders_user_id"), "market_orders", ["user_id"], unique=False)
    op.create_index(op.f("idx_market_orders_council_run_id"), "market_orders", ["council_run_id"], unique=False)
    op.alter_column("hedge_fund_flows", "is_template", existing_type=sa.BOOLEAN(), nullable=True)
    op.drop_constraint(None, "hedge_fund_flow_runs", type_="foreignkey")
    op.drop_constraint(None, "hedge_fund_flow_run_cycles", type_="foreignkey")
    op.create_index(
        op.f("ix_hedge_fund_flow_run_cycles_status"), "hedge_fund_flow_run_cycles", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_hedge_fund_flow_run_cycles_started_at"), "hedge_fund_flow_run_cycles", ["started_at"], unique=False
    )
    op.create_index(
        op.f("ix_hedge_fund_flow_run_cycles_cycle_number"),
        "hedge_fund_flow_run_cycles",
        ["cycle_number"],
        unique=False,
    )
    op.drop_index(op.f("ix_councils_user_id"), table_name="councils")
    op.drop_index(op.f("ix_councils_is_system"), table_name="councils")
    op.drop_index(op.f("ix_councils_is_public"), table_name="councils")
    op.drop_index(op.f("ix_councils_id"), table_name="councils")
    op.drop_index(op.f("ix_councils_forked_from_id"), table_name="councils")
    op.create_index(op.f("ix_councils_v2_system_status"), "councils", ["is_system", "status"], unique=False)
    op.create_index(
        op.f("idx_councils_v2_user_name_unique"),
        "councils",
        ["user_id", "name"],
        unique=True,
        postgresql_where="(user_id IS NOT NULL)",
    )
    op.create_index(op.f("idx_councils_v2_user_id"), "councils", ["user_id"], unique=False)
    op.create_index(op.f("idx_councils_v2_status"), "councils", ["status"], unique=False)
    op.create_index(op.f("idx_councils_v2_is_system"), "councils", ["is_system"], unique=False)
    op.create_index(op.f("idx_councils_v2_is_public"), "councils", ["is_public"], unique=False)
    op.create_index(op.f("idx_councils_v2_forked_from_id"), "councils", ["forked_from_id"], unique=False)
    op.alter_column(
        "councils",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.drop_index(op.f("ix_council_runs_v2_user_id"), table_name="council_runs_v2")
    op.drop_index(op.f("ix_council_runs_v2_trading_mode"), table_name="council_runs_v2")
    op.drop_index(op.f("ix_council_runs_v2_status"), table_name="council_runs_v2")
    op.drop_index(op.f("ix_council_runs_v2_id"), table_name="council_runs_v2")
    op.drop_index(op.f("ix_council_runs_v2_council_id"), table_name="council_runs_v2")
    op.create_index(op.f("idx_council_runs_v2_user_id"), "council_runs_v2", ["user_id"], unique=False)
    op.create_index(op.f("idx_council_runs_v2_trading_mode"), "council_runs_v2", ["trading_mode"], unique=False)
    op.create_index(op.f("idx_council_runs_v2_status"), "council_runs_v2", ["status"], unique=False)
    op.create_index(op.f("idx_council_runs_v2_council_id"), "council_runs_v2", ["council_id"], unique=False)
    op.alter_column(
        "council_runs_v2",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.drop_index(op.f("ix_council_run_cycles_v2_status"), table_name="council_run_cycles_v2")
    op.drop_index(op.f("ix_council_run_cycles_v2_id"), table_name="council_run_cycles_v2")
    op.drop_index(op.f("ix_council_run_cycles_v2_council_run_id"), table_name="council_run_cycles_v2")
    op.create_index(op.f("idx_council_run_cycles_v2_status"), "council_run_cycles_v2", ["status"], unique=False)
    op.create_index(
        op.f("idx_council_run_cycles_v2_run_id"), "council_run_cycles_v2", ["council_run_id"], unique=False
    )
    op.alter_column(
        "council_run_cycles_v2",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.create_index(
        op.f("ix_consensus_decisions_decision_created_at"),
        "consensus_decisions",
        ["decision", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consensus_decisions_council_id_created_at"),
        "consensus_decisions",
        ["council_id", "created_at"],
        unique=False,
    )
    op.drop_index(op.f("ix_api_keys_provider"), table_name="api_keys")
    op.create_index(op.f("ix_api_keys_provider"), "api_keys", ["provider"], unique=False)
    op.create_unique_constraint(
        op.f("api_keys_provider_key"), "api_keys", ["provider"], postgresql_nulls_not_distinct=False
    )
    op.drop_index(op.f("ix_council_performance_timestamp"), table_name="council_performance")
    op.drop_index(op.f("ix_council_performance_id"), table_name="council_performance")
    op.drop_index(op.f("ix_council_performance_council_id"), table_name="council_performance")
    op.drop_table("council_performance")
    op.drop_index(op.f("ix_council_agents_id"), table_name="council_agents")
    op.drop_index(op.f("ix_council_agents_council_id"), table_name="council_agents")
    op.drop_table("council_agents")
    # ### end Alembic commands ###
