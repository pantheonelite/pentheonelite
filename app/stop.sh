#!/bin/bash

# Stop all Vibe Trading services
# This script kills all backend and frontend processes

echo "🛑 Stopping Vibe Trading services..."

# Kill uvicorn/backend processes
if pgrep -f "uvicorn.*app.backend.main" > /dev/null; then
    echo "  Killing backend processes..."
    pkill -9 -f "uvicorn.*app.backend.main" 2>/dev/null || true
fi

# Kill vite/frontend processes
if pgrep -f "vite" > /dev/null; then
    echo "  Killing frontend processes..."
    pkill -9 -f "vite" 2>/dev/null || true
fi

# Kill uv processes
if pgrep -f "uv run" > /dev/null; then
    echo "  Killing uv processes..."
    pkill -9 -f "uv run" 2>/dev/null || true
fi

# Kill by port
for port in 8000 5173 5174; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  Killing process on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

sleep 1

# Verify all stopped
still_running=false
if pgrep -f "uvicorn.*app.backend.main" > /dev/null; then
    echo "⚠️  Warning: Backend still running"
    still_running=true
fi
if pgrep -f "vite" > /dev/null; then
    echo "⚠️  Warning: Frontend still running"
    still_running=true
fi

if [ "$still_running" = false ]; then
    echo "✅ All services stopped successfully!"
else
    echo "❌ Some processes may still be running. Check with: ps aux | grep -E 'uvicorn|vite'"
fi
