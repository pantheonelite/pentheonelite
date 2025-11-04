"""Add is_public to councils and system_prompt to council_agents.

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-25 14:00:00

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_public field to councils and system_prompt to council_agents."""
    # Add is_public to councils
    op.add_column(
        "councils",
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index(op.f("ix_councils_is_public"), "councils", ["is_public"], unique=False)

    # Add system_prompt to council_agents
    op.add_column(
        "council_agents",
        sa.Column("system_prompt", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove is_public from councils and system_prompt from council_agents."""
    # Remove system_prompt from council_agents
    op.drop_column("council_agents", "system_prompt")

    # Remove is_public from councils
    op.drop_index(op.f("ix_councils_is_public"), table_name="councils")
    op.drop_column("councils", "is_public")

