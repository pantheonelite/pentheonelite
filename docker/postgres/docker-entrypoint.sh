#!/bin/sh
# Custom entrypoint wrapper for PostgreSQL that installs custom pg_hba.conf
# This script wraps the official PostgreSQL entrypoint

# Copy custom pg_hba.conf after PostgreSQL initialization completes
copy_pg_hba_conf() {
    pgdata="${PGDATA:-/var/lib/postgresql/data}"
    pgdata_dir="${pgdata}/pgdata"
    custom_hba="/tmp/custom_pg_hba.conf"
    target_hba="${pgdata_dir}/pg_hba.conf"

    # Check prerequisites
    if [ ! -f "$custom_hba" ]; then
        return 1
    fi

    if [ ! -d "$pgdata_dir" ]; then
        return 1
    fi

    # Copy the file if it doesn't exist or is different
    if [ ! -f "$target_hba" ] || ! cmp -s "$custom_hba" "$target_hba" 2>/dev/null; then
        echo "Installing custom pg_hba.conf to ${target_hba}..."
        if cp "$custom_hba" "$target_hba" 2>/dev/null; then
            chown postgres:postgres "$target_hba" 2>/dev/null || true
            chmod 0640 "$target_hba" 2>/dev/null || true
            echo "Custom pg_hba.conf installed successfully"
            return 0
        else
            return 1
        fi
    else
        # File already matches, nothing to do
        return 0
    fi
}

# Hook into PostgreSQL startup - copy pg_hba.conf after server starts
# We'll use a background process that waits for the server to be ready
# This runs in the background and won't affect the main PostgreSQL process
setup_pg_hba() {
    (
        # Wait for PostgreSQL data directory to be initialized
        # Start with a longer initial delay to let initdb complete if needed
        sleep 10
        max_attempts=60
        attempt=0

        while [ $attempt -lt $max_attempts ]; do
            if copy_pg_hba_conf; then
                echo "pg_hba.conf setup completed successfully"
                break
            fi
            attempt=$((attempt + 1))
            sleep 1
        done

        if [ $attempt -eq $max_attempts ]; then
            echo "Warning: Failed to setup pg_hba.conf after ${max_attempts} attempts (non-fatal)"
            echo "This warning can be ignored if PostgreSQL is running correctly"
        fi
    ) &
}

# Start the background process
setup_pg_hba

# Call the official PostgreSQL entrypoint script with all arguments
# This exec replaces the current process, so the background job above will continue
# If no arguments provided, the official entrypoint will use 'postgres' as default CMD
exec /usr/local/bin/docker-entrypoint.sh "$@"
