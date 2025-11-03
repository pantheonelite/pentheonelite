"""Add is_paper_trading field to councils.

Revision ID: 0017
Revises: 0016
Create Date: 2025-01-28 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_paper_trading field to councils table."""
    # Add is_paper_trading column with default True (all existing councils are paper trading)
    op.add_column(
        "councils",
        sa.Column(
            "is_paper_trading",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )

    # Add index for faster filtering
    op.create_index(
        "ix_councils_is_paper_trading",
        "councils",
        ["is_paper_trading"],
    )


def downgrade() -> None:
    """Remove is_paper_trading field from councils table."""
    op.drop_index("ix_councils_is_paper_trading", table_name="councils")
    op.drop_column("councils", "is_paper_trading")
