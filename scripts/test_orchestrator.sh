#!/bin/bash
# Test orchestrator with validation before running a cycle

set -e  # Exit on error

COUNCIL_ID=${1:-49}
LOG_LEVEL=${2:-INFO}

echo "========================================================================"
echo "  🧪 ORCHESTRATOR VALIDATION & TEST"
echo "========================================================================"
echo "  Council ID: $COUNCIL_ID"
echo "  Log Level: $LOG_LEVEL"
echo "========================================================================"
echo ""

# Change to project root
cd "$(dirname "$0")/.." || exit

# Run test
uv run python scripts/test_orchestrator_run.py \
  --council-id "$COUNCIL_ID" \
  --log-level "$LOG_LEVEL"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo ""
  echo "========================================================================"
  echo "  ✅ TEST PASSED - Ready to run orchestrator!"
  echo "========================================================================"
  echo ""
  echo "  To run the orchestrator:"
  echo "  uv run python scripts/run_orchestrator.py --councils $COUNCIL_ID --log-level DEBUG"
  echo ""
else
  echo ""
  echo "========================================================================"
  echo "  ❌ TEST FAILED - Check errors above"
  echo "========================================================================"
  echo ""
fi

exit $EXIT_CODE
