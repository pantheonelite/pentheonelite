"""Refactor market_orders for spot trading and add portfolio fields to councils

Revision ID: 0015
Revises: 0014
Create Date: 2025-10-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to market_orders
    op.add_column('market_orders', sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column('market_orders', sa.Column('position_size_pct', sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column('market_orders', sa.Column('is_paper_trade', sa.Boolean(), nullable=False, server_default='true'))

    # Update existing side values from "long"/"short" to "buy"/"sell"
    # Note: This is a one-way migration - we assume long=buy, short=sell
    op.execute("""
        UPDATE market_orders
        SET side = CASE
            WHEN side = 'long' THEN 'buy'
            WHEN side = 'short' THEN 'sell'
            ELSE side
        END
    """)

    # Add new columns to councils for portfolio management
    op.add_column('councils', sa.Column('available_capital', sa.Numeric(precision=20, scale=2), nullable=True))
    op.add_column('councils', sa.Column('portfolio_holdings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Initialize available_capital from current_capital or initial_capital
    op.execute("""
        UPDATE councils
        SET available_capital = COALESCE(current_capital, initial_capital),
            portfolio_holdings = '{}'::jsonb
        WHERE available_capital IS NULL
    """)


def downgrade() -> None:
    # Remove columns from councils
    op.drop_column('councils', 'portfolio_holdings')
    op.drop_column('councils', 'available_capital')

    # Revert side values (best effort)
    op.execute("""
        UPDATE market_orders
        SET side = CASE
            WHEN side = 'buy' THEN 'long'
            WHEN side = 'sell' THEN 'short'
            ELSE side
        END
    """)

    # Remove columns from market_orders
    op.drop_column('market_orders', 'is_paper_trade')
    op.drop_column('market_orders', 'position_size_pct')
    op.drop_column('market_orders', 'confidence')
