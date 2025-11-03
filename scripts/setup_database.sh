#!/bin/bash

# Database Setup Script for AI Hedge Fund
# This script creates the database and runs Alembic migrations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
DB_PASSWORD=""
DB_NAME="hedge_fund"
DB_TEST_NAME="hedge_fund_test"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PostgreSQL is running
check_postgres() {
    print_status "Checking if PostgreSQL is running..."

    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
        print_error "PostgreSQL is not running or not accessible at $DB_HOST:$DB_PORT"
        print_status "Please start PostgreSQL and try again."
        print_status "On macOS with Homebrew: brew services start postgresql"
        print_status "On Ubuntu/Debian: sudo systemctl start postgresql"
        print_status "On Docker: docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres"
        exit 1
    fi

    print_success "PostgreSQL is running and accessible"
}

# Function to create database
create_database() {
    local db_name=$1
    print_status "Creating database: $db_name"

    # Check if database already exists
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        print_warning "Database '$db_name' already exists"
        read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Dropping database: $db_name"
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $db_name;"
            print_status "Creating database: $db_name"
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $db_name;"
        else
            print_status "Skipping database creation for $db_name"
        fi
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $db_name;"
    fi

    print_success "Database '$db_name' is ready"
}

# Function to run Alembic migrations
run_migrations() {
    print_status "Running Alembic migrations..."

    # Change to the backend directory where alembic.ini is located
    cd "$(dirname "$0")/../app/backend"

    # Check if alembic is available
    if ! command -v alembic &> /dev/null; then
        print_error "Alembic is not installed or not in PATH"
        print_status "Please install it with: uv add alembic"
        exit 1
    fi

    # Run migrations
    alembic upgrade head

    print_success "Database migrations completed successfully"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST        Database host (default: localhost)"
    echo "  -p, --port PORT        Database port (default: 5432)"
    echo "  -U, --user USER        Database user (default: postgres)"
    echo "  -W, --password PASS   Database password"
    echo "  -d, --database NAME    Database name (default: hedge_fund)"
    echo "  -t, --test-db NAME     Test database name (default: hedge_fund_test)"
    echo "  --test-only            Only create test database"
    echo "  --skip-migrations      Skip running Alembic migrations"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 -h localhost -U myuser -W mypass  # Custom connection"
    echo "  $0 --test-only                        # Only create test database"
    echo "  $0 --skip-migrations                 # Skip running migrations"
}

# Parse command line arguments
SKIP_MIGRATIONS=false
TEST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -U|--user)
            DB_USER="$2"
            shift 2
            ;;
        -W|--password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -t|--test-db)
            DB_TEST_NAME="$2"
            shift 2
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_status "Starting database setup for AI Hedge Fund..."

# Check PostgreSQL connection
check_postgres

# Create main database
if [ "$TEST_ONLY" = false ]; then
    create_database "$DB_NAME"
fi

# Create test database
create_database "$DB_TEST_NAME"

# Run migrations if not skipped
if [ "$SKIP_MIGRATIONS" = false ] && [ "$TEST_ONLY" = false ]; then
    run_migrations
fi

print_success "Database setup completed successfully!"
print_status "You can now start the application with:"
print_status "  uv run uvicorn main:app --reload --app-dir app/backend"
