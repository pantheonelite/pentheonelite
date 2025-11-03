#!/bin/bash
set -e

# This script runs in /docker-entrypoint-initdb.d/ after initdb completes
# It copies our custom pg_hba.conf into place

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
PGDATA_DIR="${PGDATA}/pgdata"
CUSTOM_HBA="/tmp/custom_pg_hba.conf"
TARGET_HBA="${PGDATA_DIR}/pg_hba.conf"

if [ -f "$CUSTOM_HBA" ] && [ -d "$PGDATA_DIR" ]; then
    echo "Installing custom pg_hba.conf after database initialization..."
    cp "$CUSTOM_HBA" "$TARGET_HBA"
    chown postgres:postgres "$TARGET_HBA"
    chmod 0640 "$TARGET_HBA"
    echo "Custom pg_hba.conf installed successfully"
else
    echo "Warning: Custom pg_hba.conf not found at $CUSTOM_HBA or pgdata directory not ready"
fi

