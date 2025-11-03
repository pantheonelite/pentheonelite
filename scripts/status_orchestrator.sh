#!/bin/bash
# Check the status of the council orchestrator daemon

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# PID file location
PID_FILE="orchestrator.pid"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "Status: NOT RUNNING (no PID file)"
    exit 1
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    echo "Status: RUNNING"
    echo "PID: $PID"
    echo "Command: $(ps -p $PID -o command=)"
    echo "Uptime: $(ps -p $PID -o etime=)"
    echo ""
    echo "Recent logs:"
    tail -n 20 logs/orchestrator.log
else
    echo "Status: NOT RUNNING (process $PID not found)"
    echo "Removing stale PID file"
    rm "$PID_FILE"
    exit 1
fi
