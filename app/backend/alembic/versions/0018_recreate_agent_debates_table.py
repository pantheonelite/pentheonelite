"""recreate agent_debates table

Revision ID: 0018
Revises: 0017
Create Date: 2025-10-29

"""

import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Add migration_helpers to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from migration_helpers import (
    safe_add_column,
    safe_add_foreign_key,
    safe_create_index,
    table_exists,
)

# revision identifiers, used by Alembic.
revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Recreate the agent_debates table that was removed in migration 0012.

    This table is still needed to store debate/discussion messages between agents.

    This migration is idempotent - it checks if the table exists and only
    creates missing columns/indexes if needed.
    """
    # Check if table already exists
    if table_exists("agent_debates"):
        print("ℹ️  agent_debates table already exists, ensuring schema is correct...")

        # Ensure all columns exist
        safe_add_column(
            "agent_debates",
            "id",
            sa.Integer(),
            nullable=False,
        )
        safe_add_column(
            "agent_debates",
            "council_id",
            sa.Integer(),
            nullable=False,
        )
        safe_add_column(
            "agent_debates",
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        )
        safe_add_column(
            "agent_debates",
            "agent_name",
            sa.String(length=200),
            nullable=False,
        )
        safe_add_column(
            "agent_debates",
            "message",
            sa.Text(),
            nullable=False,
        )
        safe_add_column(
            "agent_debates",
            "message_type",
            sa.String(length=50),
            server_default="analysis",
            nullable=False,
        )
        safe_add_column(
            "agent_debates",
            "sentiment",
            sa.String(length=20),
            nullable=True,
        )
        safe_add_column(
            "agent_debates",
            "market_symbol",
            sa.String(length=20),
            nullable=True,
        )
        safe_add_column(
            "agent_debates",
            "confidence",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        )
        safe_add_column(
            "agent_debates",
            "debate_round",
            sa.Integer(),
            nullable=True,
        )
        safe_add_column(
            "agent_debates",
            "meta_data",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        )

        # Ensure foreign key exists
        safe_add_foreign_key(
            "fk_agent_debates_council_id",
            "agent_debates",
            "councils",
            ["council_id"],
            ["id"],
            ondelete="CASCADE",
        )

        # Ensure indexes exist
        safe_create_index(
            op.f("ix_agent_debates_id"),
            "agent_debates",
            ["id"],
            unique=False,
        )
        safe_create_index(
            op.f("ix_agent_debates_council_id"),
            "agent_debates",
            ["council_id"],
            unique=False,
        )
        safe_create_index(
            op.f("ix_agent_debates_created_at"),
            "agent_debates",
            ["created_at"],
            unique=False,
        )
        safe_create_index(
            op.f("ix_agent_debates_market_symbol"),
            "agent_debates",
            ["market_symbol"],
            unique=False,
        )

        print("✓ agent_debates table schema verified and updated")
    else:
        # Create table from scratch
        print("Creating agent_debates table from scratch...")
        op.create_table(
            "agent_debates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("council_id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.Column("agent_name", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column(
                "message_type",
                sa.String(length=50),
                server_default="analysis",
                nullable=False,
            ),
            sa.Column("sentiment", sa.String(length=20), nullable=True),
            sa.Column("market_symbol", sa.String(length=20), nullable=True),
            sa.Column("confidence", sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column("debate_round", sa.Integer(), nullable=True),
            sa.Column("meta_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(
                ["council_id"],
                ["councils.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Create indexes
        op.create_index(op.f("ix_agent_debates_id"), "agent_debates", ["id"], unique=False)
        op.create_index(
            op.f("ix_agent_debates_council_id"),
            "agent_debates",
            ["council_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_agent_debates_created_at"),
            "agent_debates",
            ["created_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_agent_debates_market_symbol"),
            "agent_debates",
            ["market_symbol"],
            unique=False,
        )

        print("✓ Created agent_debates table")


def downgrade() -> None:
    """Remove the agent_debates table."""
    from migration_helpers import safe_drop_index, safe_drop_table

    safe_drop_index(op.f("ix_agent_debates_market_symbol"), table_name="agent_debates")
    safe_drop_index(op.f("ix_agent_debates_created_at"), table_name="agent_debates")
    safe_drop_index(op.f("ix_agent_debates_council_id"), table_name="agent_debates")
    safe_drop_index(op.f("ix_agent_debates_id"), table_name="agent_debates")
    safe_drop_table("agent_debates")
