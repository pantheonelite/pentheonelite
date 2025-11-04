"""Add portfolio_holdings table

Revision ID: 0014
Revises: 0013
Create Date: 2025-10-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolio_holdings table
    op.create_table(
        'portfolio_holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('council_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('average_cost', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['council_id'], ['councils.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('council_id', 'symbol', name='uq_council_symbol')
    )

    # Create indexes
    op.create_index('ix_portfolio_holdings_council_id', 'portfolio_holdings', ['council_id'])
    op.create_index('ix_portfolio_holdings_symbol', 'portfolio_holdings', ['symbol'])


def downgrade() -> None:
    op.drop_index('ix_portfolio_holdings_symbol', table_name='portfolio_holdings')
    op.drop_index('ix_portfolio_holdings_council_id', table_name='portfolio_holdings')
    op.drop_table('portfolio_holdings')
