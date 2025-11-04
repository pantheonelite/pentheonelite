"""merge_heads_0026_and_e5f6a7b8c9d0

Revision ID: 0027
Revises: 0026, e5f6a7b8c9d0
Create Date: 2025-11-04 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0027"
down_revision: tuple[str, ...] | None = ("0026", "e5f6a7b8c9d0")
branch_labels: list[str] | None = None
depends_on: list[str] | None = None


def upgrade() -> None:
    """No-op merge migration to unify divergent heads."""
    # This merge revision intentionally contains no schema changes.
    # It only reconciles the history so future migrations have a single head.
    pass


def downgrade() -> None:
    """No-op downgrade for merge revision."""
    pass


