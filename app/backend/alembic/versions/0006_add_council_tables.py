"""add council tables

Revision ID: 0006
Revises: 0005
Create Date: 2025-01-25 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create councils table
    op.create_table("councils",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("strategy", sa.String(length=100), nullable=True),
        sa.Column("initial_capital", sa.Numeric(precision=20, scale=2), server_default="100000", nullable=False),
        sa.Column("current_capital", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_pnl", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("win_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("total_trades", sa.Integer(), server_default="0", nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_councils_id"), "councils", ["id"], unique=False)
    op.create_index(op.f("ix_councils_name"), "councils", ["name"], unique=True)
    op.create_index(op.f("ix_councils_is_default"), "councils", ["is_default"], unique=False)

    # Create council_agents table
    op.create_table("council_agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("agent_name", sa.String(length=200), nullable=False),
        sa.Column("agent_type", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("traits", sa.JSON(), nullable=True),
        sa.Column("specialty", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_council_agents_id"), "council_agents", ["id"], unique=False)
    op.create_index(op.f("ix_council_agents_council_id"), "council_agents", ["council_id"], unique=False)

    # Create agent_debates table
    op.create_table("agent_debates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("agent_name", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=50), server_default="analysis", nullable=False),
        sa.Column("sentiment", sa.String(length=20), nullable=True),
        sa.Column("market_symbol", sa.String(length=20), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("debate_round", sa.Integer(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_agent_debates_id"), "agent_debates", ["id"], unique=False)
    op.create_index(op.f("ix_agent_debates_council_id"), "agent_debates", ["council_id"], unique=False)
    op.create_index(op.f("ix_agent_debates_created_at"), "agent_debates", ["created_at"], unique=False)
    op.create_index(op.f("ix_agent_debates_market_symbol"), "agent_debates", ["market_symbol"], unique=False)

    # Create market_orders table
    op.create_table("market_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("council_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("exit_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("take_profit", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("pnl_percentage", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["council_id"], ["councils.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_market_orders_id"), "market_orders", ["id"], unique=False)
    op.create_index(op.f("ix_market_orders_council_id"), "market_orders", ["council_id"], unique=False)
    op.create_index(op.f("ix_market_orders_created_at"), "market_orders", ["created_at"], unique=False)
    op.create_index(op.f("ix_market_orders_symbol"), "market_orders", ["symbol"], unique=False)
    op.create_index(op.f("ix_market_orders_status"), "market_orders", ["status"], unique=False)

    # Create council_performance table
    op.create_table("council_performance",
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
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_council_performance_id"), "council_performance", ["id"], unique=False)
    op.create_index(op.f("ix_council_performance_council_id"), "council_performance", ["council_id"], unique=False)
    op.create_index(op.f("ix_council_performance_timestamp"), "council_performance", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_council_performance_timestamp"), table_name="council_performance")
    op.drop_index(op.f("ix_council_performance_council_id"), table_name="council_performance")
    op.drop_index(op.f("ix_council_performance_id"), table_name="council_performance")
    op.drop_table("council_performance")

    op.drop_index(op.f("ix_market_orders_status"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_symbol"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_created_at"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_council_id"), table_name="market_orders")
    op.drop_index(op.f("ix_market_orders_id"), table_name="market_orders")
    op.drop_table("market_orders")

    op.drop_index(op.f("ix_agent_debates_market_symbol"), table_name="agent_debates")
    op.drop_index(op.f("ix_agent_debates_created_at"), table_name="agent_debates")
    op.drop_index(op.f("ix_agent_debates_council_id"), table_name="agent_debates")
    op.drop_index(op.f("ix_agent_debates_id"), table_name="agent_debates")
    op.drop_table("agent_debates")

    op.drop_index(op.f("ix_council_agents_council_id"), table_name="council_agents")
    op.drop_index(op.f("ix_council_agents_id"), table_name="council_agents")
    op.drop_table("council_agents")

    op.drop_index(op.f("ix_councils_is_default"), table_name="councils")
    op.drop_index(op.f("ix_councils_name"), table_name="councils")
    op.drop_index(op.f("ix_councils_id"), table_name="councils")
    op.drop_table("councils")
