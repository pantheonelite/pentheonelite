#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Vibe Trading Backend...${NC}"

# Wait for PostgreSQL to be ready with retries
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
RETRY_DELAY=2

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}" > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}PostgreSQL not ready yet. Attempt $RETRY_COUNT/$MAX_RETRIES. Retrying in ${RETRY_DELAY}s...${NC}"
    sleep $RETRY_DELAY

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}Failed to connect to PostgreSQL after $MAX_RETRIES attempts${NC}"
        exit 1
    fi
done

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
RETRY_COUNT=0
REDIS_HOST=$(echo ${REDIS_URL:-redis://redis:6379} | sed -n 's|redis://\([^:]*\).*|\1|p')

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if redis-cli -h "$REDIS_HOST" ping > /dev/null 2>&1; then
        echo -e "${GREEN}Redis is ready!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}Redis not ready yet. Attempt $RETRY_COUNT/$MAX_RETRIES. Retrying in ${RETRY_DELAY}s...${NC}"
    sleep $RETRY_DELAY

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}Failed to connect to Redis after $MAX_RETRIES attempts${NC}"
        exit 1
    fi
done

# Run database migrations with retry logic
echo -e "${YELLOW}Running database migrations...${NC}"
cd app/backend

RETRY_COUNT=0
MAX_MIGRATION_RETRIES=5
MIGRATION_DELAY=5

while [ $RETRY_COUNT -lt $MAX_MIGRATION_RETRIES ]; do
    if uv run alembic upgrade head; then
        echo -e "${GREEN}Database migrations completed successfully!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_MIGRATION_RETRIES ]; then
        echo -e "${YELLOW}Migration failed. Attempt $RETRY_COUNT/$MAX_MIGRATION_RETRIES. Retrying in ${MIGRATION_DELAY}s...${NC}"
        sleep $MIGRATION_DELAY
    else
        echo -e "${RED}Failed to run migrations after $MAX_MIGRATION_RETRIES attempts${NC}"
        exit 1
    fi
done

cd ../..

# Start the FastAPI server
echo -e "${GREEN}Starting FastAPI server...${NC}"
exec uv run uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
