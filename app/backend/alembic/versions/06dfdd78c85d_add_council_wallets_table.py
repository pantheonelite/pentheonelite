"""add_council_wallets_table

Revision ID: 06dfdd78c85d
Revises: 023e9897fd38
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "06dfdd78c85d"
down_revision: Union[str, None] = "023e9897fd38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "council_wallets" not in existing_tables:
        op.create_table(
            "council_wallets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("council_id", sa.Integer(), nullable=False),
            sa.Column("api_key", sa.Text(), nullable=False),
            sa.Column("secret_key", sa.Text(), nullable=False),
            sa.Column("ca", sa.String(length=200), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["council_id"],
                ["councils.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("council_id", name="uq_council_wallets_council_id"),
        )
        op.create_index(op.f("ix_council_wallets_id"), "council_wallets", ["id"], unique=False)
        op.create_index(op.f("ix_council_wallets_council_id"), "council_wallets", ["council_id"], unique=True)
    else:
        print("ℹ️  Table 'council_wallets' already exists, skipping creation")
    
    # Add wallet_id column to councils table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("councils")]
    
    if "wallet_id" not in existing_columns:
        op.add_column(
            "councils",
            sa.Column(
                "wallet_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        op.create_foreign_key(
            "fk_councils_wallet_id",
            "councils",
            "council_wallets",
            ["wallet_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(op.f("ix_councils_wallet_id"), "councils", ["wallet_id"], unique=False)
    else:
        print("ℹ️  Column 'wallet_id' already exists in 'councils' table, skipping creation")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop wallet_id column from councils table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("councils")]
    
    if "wallet_id" in existing_columns:
        op.drop_index(op.f("ix_councils_wallet_id"), table_name="councils")
        op.drop_constraint("fk_councils_wallet_id", "councils", type_="foreignkey")
        op.drop_column("councils", "wallet_id")
    
    # Check if table exists
    existing_tables = inspector.get_table_names()

    if "council_wallets" in existing_tables:
        op.drop_index(op.f("ix_council_wallets_council_id"), table_name="council_wallets")
        op.drop_index(op.f("ix_council_wallets_id"), table_name="council_wallets")
        op.drop_table("council_wallets")

