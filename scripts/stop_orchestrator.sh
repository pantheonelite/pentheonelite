#!/bin/bash
# Stop the council orchestrator daemon

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# PID file location
PID_FILE="orchestrator.pid"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "Orchestrator is not running (no PID file found)"
    exit 1
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Orchestrator is not running (process $PID not found)"
    rm "$PID_FILE"
    exit 1
fi

# Send SIGTERM for graceful shutdown
echo "Stopping orchestrator (PID $PID)..."
kill -TERM "$PID"

# Wait for process to stop (max 30 seconds)
WAIT_TIME=0
while ps -p "$PID" > /dev/null 2>&1; do
    sleep 1
    WAIT_TIME=$((WAIT_TIME + 1))

    if [ $WAIT_TIME -eq 10 ]; then
        echo "Waiting for graceful shutdown..."
    fi

    if [ $WAIT_TIME -eq 30 ]; then
        echo "Orchestrator did not stop gracefully, forcing shutdown..."
        kill -KILL "$PID"
        sleep 1
        break
    fi
done

# Remove PID file
rm "$PID_FILE"

echo "Orchestrator stopped"
