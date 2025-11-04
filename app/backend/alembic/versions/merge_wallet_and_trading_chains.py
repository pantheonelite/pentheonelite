"""merge_wallet_and_trading_chains

Revision ID: d4e5f6a7b8c9
Revises: 0024, b2c3d4e5f6a7
Create Date: 2025-01-27 13:30:00.000000

Merge wallet chain and trading mode chain
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = ("0024", "c3d4e5f6a7b8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration chains - no-op."""
    # This is a merge migration, no schema changes needed
    # All actual schema changes are in the parent migrations
    pass


def downgrade() -> None:
    """Merge migration chains - no-op."""
    # This is a merge migration, no schema changes needed
    pass

