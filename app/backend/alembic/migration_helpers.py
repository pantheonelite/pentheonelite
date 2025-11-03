"""
Migration helper utilities for idempotent database migrations.

This module provides utility functions to check database state and safely
apply schema changes, ensuring migrations work correctly across different
database states on multiple dev machines.
"""

import sqlalchemy as sa

from alembic import op


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Parameters
    ----------
    table_name : str
        Name of the table to check.

    Returns
    -------
    bool
        True if table exists, False otherwise.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.

    Parameters
    ----------
    table_name : str
        Name of the table.
    column_name : str
        Name of the column to check.

    Returns
    -------
    bool
        True if column exists, False otherwise.
    """
    if not table_exists(table_name):
        return False

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name: str, table_name: str | None = None) -> bool:
    """
    Check if an index exists.

    Parameters
    ----------
    index_name : str
        Name of the index to check.
    table_name : str | None
        Optional table name to narrow search.

    Returns
    -------
    bool
        True if index exists, False otherwise.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if table_name:
        if not table_exists(table_name):
            return False
        indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        return index_name in indexes

    # Check across all tables
    for tbl in inspector.get_table_names():
        indexes = [idx["name"] for idx in inspector.get_indexes(tbl)]
        if index_name in indexes:
            return True
    return False


def constraint_exists(constraint_name: str, table_name: str) -> bool:
    """
    Check if a constraint exists on a table.

    Parameters
    ----------
    constraint_name : str
        Name of the constraint to check.
    table_name : str
        Name of the table.

    Returns
    -------
    bool
        True if constraint exists, False otherwise.
    """
    if not table_exists(table_name):
        return False

    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check foreign keys
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        if fk.get("name") == constraint_name:
            return True

    # Check unique constraints
    uqs = inspector.get_unique_constraints(table_name)
    for uq in uqs:
        if uq.get("name") == constraint_name:
            return True

    # Check primary key
    pk = inspector.get_pk_constraint(table_name)
    if pk.get("name") == constraint_name:
        return True

    return False


def foreign_key_exists(table_name: str, column_name: str, ref_table: str) -> bool:
    """
    Check if a foreign key exists for a specific column.

    Parameters
    ----------
    table_name : str
        Name of the table with the foreign key.
    column_name : str
        Name of the column with the foreign key.
    ref_table : str
        Name of the referenced table.

    Returns
    -------
    bool
        True if foreign key exists, False otherwise.
    """
    if not table_exists(table_name):
        return False

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    fks = inspector.get_foreign_keys(table_name)

    for fk in fks:
        if column_name in fk.get("constrained_columns", []) and fk.get("referred_table") == ref_table:
            return True

    return False


def get_table_columns(table_name: str) -> list[dict]:
    """
    Get column definitions for a table.

    Parameters
    ----------
    table_name : str
        Name of the table.

    Returns
    -------
    list[dict]
        List of column definitions with name, type, nullable, default, etc.
    """
    if not table_exists(table_name):
        return []

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return inspector.get_columns(table_name)


def safe_create_table(
    table_name: str,
    *columns,
    **kwargs,
) -> bool:
    """
    Create a table only if it doesn't exist.

    Parameters
    ----------
    table_name : str
        Name of the table to create.
    *columns
        Column definitions.
    **kwargs
        Additional arguments for create_table.

    Returns
    -------
    bool
        True if table was created, False if it already existed.
    """
    if table_exists(table_name):
        print(f"ℹ️  Table '{table_name}' already exists, skipping creation")
        return False

    op.create_table(table_name, *columns, **kwargs)
    print(f"✓ Created table '{table_name}'")
    return True


def safe_add_column(
    table_name: str,
    column_name: str,
    column_type,
    **kwargs,
) -> bool:
    """
    Add a column to a table only if it doesn't exist.

    Parameters
    ----------
    table_name : str
        Name of the table.
    column_name : str
        Name of the column to add.
    column_type
        SQLAlchemy column type.
    **kwargs
        Additional column arguments (nullable, default, etc.).

    Returns
    -------
    bool
        True if column was added, False if it already existed.
    """
    if not table_exists(table_name):
        print(f"⚠️  Table '{table_name}' does not exist, cannot add column '{column_name}'")
        return False

    if column_exists(table_name, column_name):
        print(f"ℹ️  Column '{column_name}' already exists in '{table_name}', skipping")
        return False

    op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
    print(f"✓ Added column '{column_name}' to '{table_name}'")
    return True


def safe_create_index(
    index_name: str,
    table_name: str,
    columns: list[str],
    unique: bool = False,
    **kwargs,
) -> bool:
    """
    Create an index only if it doesn't exist.

    Parameters
    ----------
    index_name : str
        Name of the index.
    table_name : str
        Name of the table.
    columns : list[str]
        List of column names to index.
    unique : bool
        Whether the index should be unique.
    **kwargs
        Additional index arguments.

    Returns
    -------
    bool
        True if index was created, False if it already existed.
    """
    if not table_exists(table_name):
        print(f"⚠️  Table '{table_name}' does not exist, cannot create index '{index_name}'")
        return False

    if index_exists(index_name, table_name):
        print(f"ℹ️  Index '{index_name}' already exists on '{table_name}', skipping")
        return False

    op.create_index(index_name, table_name, columns, unique=unique, **kwargs)
    print(f"✓ Created index '{index_name}' on '{table_name}'")
    return True


def safe_drop_index(index_name: str, table_name: str | None = None) -> bool:
    """
    Drop an index only if it exists.

    Parameters
    ----------
    index_name : str
        Name of the index to drop.
    table_name : str | None
        Optional table name.

    Returns
    -------
    bool
        True if index was dropped, False if it didn't exist.
    """
    if not index_exists(index_name, table_name):
        print(f"ℹ️  Index '{index_name}' does not exist, skipping drop")
        return False

    op.drop_index(index_name, table_name=table_name)
    print(f"✓ Dropped index '{index_name}'")
    return True


def safe_add_foreign_key(
    constraint_name: str,
    source_table: str,
    referent_table: str,
    local_cols: list[str],
    remote_cols: list[str],
    ondelete: str | None = None,
    **kwargs,
) -> bool:
    """
    Add a foreign key constraint only if it doesn't exist.

    Parameters
    ----------
    constraint_name : str
        Name of the constraint.
    source_table : str
        Table with the foreign key.
    referent_table : str
        Referenced table.
    local_cols : list[str]
        Columns in source table.
    remote_cols : list[str]
        Columns in referenced table.
    ondelete : str | None
        ON DELETE action (CASCADE, SET NULL, etc.).
    **kwargs
        Additional constraint arguments.

    Returns
    -------
    bool
        True if constraint was added, False if it already existed.
    """
    if not table_exists(source_table):
        print(f"⚠️  Table '{source_table}' does not exist, cannot add foreign key")
        return False

    if not table_exists(referent_table):
        print(f"⚠️  Referenced table '{referent_table}' does not exist, cannot add foreign key")
        return False

    # Check if foreign key already exists
    if foreign_key_exists(source_table, local_cols[0], referent_table):
        print(f"ℹ️  Foreign key from '{source_table}.{local_cols[0]}' to '{referent_table}' already exists, skipping")
        return False

    op.create_foreign_key(
        constraint_name,
        source_table,
        referent_table,
        local_cols,
        remote_cols,
        ondelete=ondelete,
        **kwargs,
    )
    print(f"✓ Created foreign key '{constraint_name}' from '{source_table}' to '{referent_table}'")
    return True


def safe_drop_constraint(
    constraint_name: str,
    table_name: str,
    type_: str | None = None,
) -> bool:
    """
    Drop a constraint only if it exists.

    Parameters
    ----------
    constraint_name : str
        Name of the constraint to drop.
    table_name : str
        Name of the table.
    type_ : str | None
        Type of constraint (foreignkey, unique, primary, check).

    Returns
    -------
    bool
        True if constraint was dropped, False if it didn't exist.
    """
    if not table_exists(table_name):
        print(f"ℹ️  Table '{table_name}' does not exist, skipping constraint drop")
        return False

    if not constraint_exists(constraint_name, table_name):
        print(f"ℹ️  Constraint '{constraint_name}' does not exist on '{table_name}', skipping drop")
        return False

    op.drop_constraint(constraint_name, table_name, type_=type_)
    print(f"✓ Dropped constraint '{constraint_name}' from '{table_name}'")
    return True


def safe_drop_table(table_name: str) -> bool:
    """
    Drop a table only if it exists.

    Parameters
    ----------
    table_name : str
        Name of the table to drop.

    Returns
    -------
    bool
        True if table was dropped, False if it didn't exist.
    """
    if not table_exists(table_name):
        print(f"ℹ️  Table '{table_name}' does not exist, skipping drop")
        return False

    op.drop_table(table_name)
    print(f"✓ Dropped table '{table_name}'")
    return True


def safe_drop_column(table_name: str, column_name: str) -> bool:
    """
    Drop a column only if it exists.

    Parameters
    ----------
    table_name : str
        Name of the table.
    column_name : str
        Name of the column to drop.

    Returns
    -------
    bool
        True if column was dropped, False if it didn't exist.
    """
    if not table_exists(table_name):
        print(f"ℹ️  Table '{table_name}' does not exist, skipping column drop")
        return False

    if not column_exists(table_name, column_name):
        print(f"ℹ️  Column '{column_name}' does not exist in '{table_name}', skipping drop")
        return False

    op.drop_column(table_name, column_name)
    print(f"✓ Dropped column '{column_name}' from '{table_name}'")
    return True
