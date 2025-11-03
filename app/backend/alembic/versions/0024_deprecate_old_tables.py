"""Deprecate old tables.

Revision ID: 0024
Revises: 0023
Create Date: 2025-11-01 00:05:00.000000

Renames old portfolio_holdings and market_orders tables with _deprecated suffix.
No data migration - clean reset.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename old tables to mark as deprecated."""
    # Rename old tables
    op.rename_table("portfolio_holdings", "portfolio_holdings_deprecated")
    op.rename_table("market_orders", "market_orders_deprecated")

    # Add comments to indicate deprecation
    op.execute(
        """
        COMMENT ON TABLE portfolio_holdings_deprecated IS
        'DEPRECATED: Replaced by spot_holdings and futures_positions tables. Do not use for new data.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE market_orders_deprecated IS
        'DEPRECATED: Replaced by orders table. Do not use for new data.'
        """
    )


def downgrade() -> None:
    """Restore original table names."""
    op.rename_table("portfolio_holdings_deprecated", "portfolio_holdings")
    op.rename_table("market_orders_deprecated", "market_orders")
