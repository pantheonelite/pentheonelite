"""Add consensus decisions table

Revision ID: 0016
Revises: 0015
Create Date: 2025-10-28 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create consensus_decisions table to track all council consensus decisions.

    This table stores every consensus decision made by a council, including:
    - BUY decisions (with trades)
    - SELL decisions (with trades)
    - HOLD decisions (no trade, but decision still recorded)
    """
    op.create_table(
        "consensus_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "council_id",
            sa.Integer(),
            sa.ForeignKey("councils.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "council_run_id",
            sa.Integer(),
            sa.ForeignKey("council_runs_v2.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "council_run_cycle_id",
            sa.Integer(),
            sa.ForeignKey("council_run_cycles_v2.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        # Consensus decision
        sa.Column("decision", sa.String(20), nullable=False, index=True),  # BUY, SELL, HOLD
        sa.Column("symbol", sa.String(20), nullable=False, index=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),  # Average agent confidence
        # Vote breakdown
        sa.Column("votes_buy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("votes_sell", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("votes_hold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_votes", sa.Integer(), nullable=False),
        # Agent votes (JSON mapping agent_name -> vote)
        sa.Column("agent_votes", postgresql.JSONB, nullable=True),
        # Reasoning
        sa.Column("reasoning", sa.Text(), nullable=True),
        # Market conditions at time of decision
        sa.Column("market_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("market_conditions", postgresql.JSONB, nullable=True),
        # Execution results (if trade was executed)
        sa.Column("was_executed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "market_order_id", sa.Integer(), sa.ForeignKey("market_orders.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("execution_reason", sa.String(100), nullable=True),  # e.g., "low_confidence", "insufficient_capital"
        # Metadata
        sa.Column("meta_data", postgresql.JSONB, nullable=True),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_consensus_decisions_council_id_created_at", "consensus_decisions", ["council_id", "created_at"]
    )
    op.create_index("ix_consensus_decisions_decision_created_at", "consensus_decisions", ["decision", "created_at"])


def downgrade() -> None:
    """Drop consensus_decisions table."""
    op.drop_index("ix_consensus_decisions_decision_created_at", table_name="consensus_decisions")
    op.drop_index("ix_consensus_decisions_council_id_created_at", table_name="consensus_decisions")
    op.drop_table("consensus_decisions")
