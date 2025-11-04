"""add_trading_mode_column

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-01-27 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trading_mode and trading_type columns to councils table if they don't exist."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "councils" in existing_tables:
        # Get existing columns
        existing_columns = {col["name"] for col in inspector.get_columns("councils")}
        
        # Add trading_mode column if it doesn't exist
        if "trading_mode" not in existing_columns:
            op.add_column(
                "councils",
                sa.Column(
                    "trading_mode",
                    sa.String(length=10),
                    nullable=False,
                    server_default="paper",
                ),
            )
            print("✓ Added trading_mode column to councils table")
        else:
            print("ℹ️  Column 'trading_mode' already exists in 'councils' table, skipping")
        
        # Add trading_type column if it doesn't exist
        if "trading_type" not in existing_columns:
            op.add_column(
                "councils",
                sa.Column(
                    "trading_type",
                    sa.String(length=10),
                    nullable=False,
                    server_default="futures",
                ),
            )
            print("✓ Added trading_type column to councils table")
        else:
            print("ℹ️  Column 'trading_type' already exists in 'councils' table, skipping")
            
        # Check for other missing columns from migration 0023
        missing_columns = {
            "total_account_value": sa.Numeric(precision=20, scale=2),
            "available_balance": sa.Numeric(precision=20, scale=2),
            "used_balance": sa.Numeric(precision=20, scale=2),
            "total_margin_used": sa.Numeric(precision=20, scale=2),
            "total_unrealized_profit": sa.Numeric(precision=20, scale=2),
            "open_futures_count": sa.Integer(),
            "closed_futures_count": sa.Integer(),
            "active_spot_holdings": sa.Integer(),
            "total_realized_pnl": sa.Numeric(precision=20, scale=2),
            "net_pnl": sa.Numeric(precision=20, scale=2),
            "total_fees": sa.Numeric(precision=20, scale=2),
            "total_funding_fees": sa.Numeric(precision=20, scale=2),
            "average_leverage": sa.Numeric(precision=5, scale=2),
            "average_confidence": sa.Numeric(precision=5, scale=4),
            "biggest_win": sa.Numeric(precision=20, scale=2),
            "biggest_loss": sa.Numeric(precision=20, scale=2),
            "long_hold_pct": sa.Numeric(precision=5, scale=2),
            "short_hold_pct": sa.Numeric(precision=5, scale=2),
            "flat_hold_pct": sa.Numeric(precision=5, scale=2),
        }
        
        defaults = {
            "total_account_value": "0",
            "available_balance": "0",
            "used_balance": "0",
            "total_margin_used": "0",
            "total_unrealized_profit": "0",
            "open_futures_count": "0",
            "closed_futures_count": "0",
            "active_spot_holdings": "0",
            "total_realized_pnl": "0",
            "net_pnl": "0",
            "total_fees": "0",
            "total_funding_fees": "0",
            "average_leverage": "0",
            "average_confidence": "0",
            "biggest_win": "0",
            "biggest_loss": "0",
            "long_hold_pct": "0",
            "short_hold_pct": "0",
            "flat_hold_pct": "100",
        }
        
        for col_name, col_type in missing_columns.items():
            if col_name not in existing_columns:
                default_value = defaults.get(col_name, "0")
                op.add_column(
                    "councils",
                    sa.Column(
                        col_name,
                        col_type,
                        nullable=False,
                        server_default=default_value,
                    ),
                )
                print(f"✓ Added {col_name} column to councils table")
    else:
        print("ℹ️  Table 'councils' does not exist, skipping")


def downgrade() -> None:
    """Remove trading_mode and trading_type columns from councils table."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "councils" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("councils")}
        
        # Remove columns in reverse order
        columns_to_remove = [
            "flat_hold_pct",
            "short_hold_pct",
            "long_hold_pct",
            "biggest_loss",
            "biggest_win",
            "average_confidence",
            "average_leverage",
            "total_funding_fees",
            "total_fees",
            "net_pnl",
            "total_realized_pnl",
            "active_spot_holdings",
            "closed_futures_count",
            "open_futures_count",
            "total_unrealized_profit",
            "total_margin_used",
            "used_balance",
            "available_balance",
            "total_account_value",
            "trading_type",
            "trading_mode",
        ]
        
        for col_name in columns_to_remove:
            if col_name in existing_columns:
                op.drop_column("councils", col_name)
                print(f"✓ Removed {col_name} column from councils table")

