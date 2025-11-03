#!/bin/bash
# Script to load crypto council mock data into the database

set -e  # Exit on error

echo "========================================================================"
echo "  📊 LOADING CRYPTO COUNCIL MOCK DATA"
echo "========================================================================"
echo ""

# Check if --replace flag is passed
REPLACE_FLAG=""
if [ "$1" == "--replace" ]; then
    REPLACE_FLAG="--replace"
    echo "  Mode: Replace existing data"
else
    echo "  Mode: Skip if data exists"
fi

echo ""
echo "  Running mock data loader..."
echo ""

# Run the mock data loader
cd "$(dirname "$0")/.." || exit
uv run python app/backend/src/cli/load_mock_data.py $REPLACE_FLAG

echo ""
echo "========================================================================"
echo "  ✅ DONE"
echo "========================================================================"
