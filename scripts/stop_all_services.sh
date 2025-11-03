#!/bin/bash
# Stop all backend services and orchestrators

echo "🛑 Stopping all backend services..."

# Stop uvicorn
echo "Stopping uvicorn..."
pkill -f "uvicorn.*app.backend.main"

# Stop orchestrators
echo "Stopping orchestrators..."
pkill -f "run_orchestrator.py"

# Wait a moment
sleep 2

# Check if anything is still running
REMAINING=$(ps aux | grep -E "(uvicorn|run_orchestrator)" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "⚠️  Some processes still running, force killing..."
    pkill -9 -f "uvicorn.*app.backend.main"
    pkill -9 -f "run_orchestrator.py"
    sleep 1
fi

# Final check
REMAINING=$(ps aux | grep -E "(uvicorn|run_orchestrator)" | grep -v grep | wc -l)

if [ $REMAINING -eq 0 ]; then
    echo "✅ All services stopped"
else
    echo "❌ Some processes still running:"
    ps aux | grep -E "(uvicorn|run_orchestrator)" | grep -v grep
fi
