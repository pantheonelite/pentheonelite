#!/bin/bash
# Start the council orchestrator daemon

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# PID file location
PID_FILE="orchestrator.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Orchestrator is already running with PID $PID"
        exit 1
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Parse command line arguments
COUNCILS=""
SCHEDULE_INTERVAL=""
NO_EVENT_TRIGGERS=""
LOG_LEVEL="DEBUG"

while [[ $# -gt 0 ]]; do
    case $1 in
        --councils)
            COUNCILS="--councils $2"
            shift 2
            ;;
        --schedule-interval)
            SCHEDULE_INTERVAL="--schedule-interval $2"
            shift 2
            ;;
        --no-event-triggers)
            NO_EVENT_TRIGGERS="--no-event-triggers"
            shift
            ;;
        --log-level)
            LOG_LEVEL="--log-level $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--councils ID1,ID2] [--schedule-interval SECONDS] [--no-event-triggers] [--log-level LEVEL]"
            echo ""
            echo "Examples:"
            echo "  $0                                          # Run all system councils (default: 4 hours)"
            echo "  $0 --councils 1,2                           # Run specific councils"
            echo "  $0 --schedule-interval 60                   # Run every 60 seconds (1 minute)"
            echo "  $0 --schedule-interval 3600                 # Run every 3600 seconds (1 hour)"
            echo "  $0 --schedule-interval 21600                # Run every 21600 seconds (6 hours)"
            echo "  $0 --councils 1 --schedule-interval 300     # Council 1 every 5 minutes"
            exit 1
            ;;
    esac
done

# Start orchestrator
echo "Starting council orchestrator daemon..."
echo "Working directory: $PROJECT_DIR"
# Use JSON format for log file (machine-parseable)
nohup uv run python scripts/run_orchestrator.py \
    $COUNCILS \
    $SCHEDULE_INTERVAL \
    $NO_EVENT_TRIGGERS \
    --log-level $LOG_LEVEL \
    --log-format console \
    > logs/orchestrator.log 2>&1 &

# Save PID
echo $! > "$PID_FILE"
PID=$(cat "$PID_FILE")

echo "Orchestrator started with PID $PID"
echo "Logs: tail -f logs/orchestrator.log"
echo "Stop: ./scripts/stop_orchestrator.sh"
