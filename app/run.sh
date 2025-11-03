#!/bin/bash

# AI Hedge Fund Web Application Setup and Runner
# This script makes it easy for non-technical users to run the full web application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to open browser
open_browser() {
    local url="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$url"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists xdg-open; then
            xdg-open "$url"
        elif command_exists firefox; then
            firefox "$url" &
        elif command_exists google-chrome; then
            google-chrome "$url" &
        elif command_exists chromium; then
            chromium "$url" &
        fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        # Windows
        start "$url"
    fi
}

# Function to check if we're in the right directory
check_directory() {
    if [[ ! -d "frontend" ]] || [[ ! -d "backend" ]]; then
        print_error "This script must be run from the app/ directory"
        print_error "Please navigate to the app/ directory and run: ./run.sh"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    local missing_deps=()

    # Check for Node.js
    if ! command_exists node; then
        missing_deps+=("Node.js (https://nodejs.org/)")
    fi

    # Check for npm
    if ! command_exists npm; then
        missing_deps+=("npm (comes with Node.js)")
    fi

    # Check for Python
    if ! command_exists python3; then
        missing_deps+=("Python 3 (https://python.org/)")
    fi

    # Check for uv - offer to install if missing
    if ! command_exists uv; then
        print_warning "uv is not installed."
        print_status "uv is required to manage Python dependencies for this project."
        echo ""
        read -p "Would you like to install uv automatically? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installing uv..."
            if python3 -m pip install uv; then
                print_success "uv installed successfully!"
                print_status "Refreshing environment..."
                # Try to refresh the PATH for this session
                export PATH="$HOME/.local/bin:$PATH"
                if ! command_exists uv; then
                    print_warning "uv may not be in PATH. You might need to restart your terminal."
                    print_warning "Alternatively, try: source ~/.bashrc or source ~/.zshrc"
                fi
            else
                print_error "Failed to install uv automatically."
                print_error "Please install uv by following https://docs.astral.sh/uv/getting-started/installation/"
                exit 1
            fi
        else
            missing_deps+=("uv (https://docs.astral.sh/uv/)")
        fi
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        print_error "Please install the missing dependencies and run this script again."
        exit 1
    fi

    print_success "All prerequisites are installed!"
}

# Function to setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."

    # Check if .env exists in the root directory
    if [[ ! -f "../.env" ]]; then
        if [[ -f "../.env.example" ]]; then
            print_warning "No .env file found. Creating from .env.example..."
            cp "../.env.example" "../.env"
            print_warning "Please edit the .env file in the root directory to add your API keys:"
            print_warning "  - OPENAI_API_KEY=your-openai-api-key"
            print_warning "  - GROQ_API_KEY=your-groq-api-key"
            print_warning "  - FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key"
            echo ""
        else
            print_error "No .env or .env.example file found in the root directory."
            print_error "Please create a .env file with your API keys."
            exit 1
        fi
    else
        print_success "Environment file (.env) found!"
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."

    # Database will be automatically created by the backend when it starts
    print_status "Database: SQLite (hedge_fund.db)"
    print_status "Location: Project root directory"
    print_status "Tables will be created automatically on first backend startup"

    # Check if database already exists
    if [[ -f "../hedge_fund.db" ]]; then
        print_success "Database file already exists!"
    else
        print_status "Database will be created when backend starts for the first time"
    fi
}

# Function to install backend dependencies
install_backend() {
    print_status "Installing backend dependencies..."

    local project_root
    project_root="$(cd .. && pwd)"

    if (cd "$project_root" && uv run python -c "import uvicorn; import fastapi" >/dev/null 2>&1); then
        print_success "Backend dependencies already installed!"
        return
    fi

    print_status "Syncing Python dependencies with uv..."
    if (cd "$project_root" && uv sync --all-groups --frozen); then
        if (cd "$project_root" && uv run python -c "import uvicorn; import fastapi" >/dev/null 2>&1); then
            print_success "Backend dependencies installed!"
        else
            print_error "Dependencies synced but imports still fail."
            print_error "Try running: uv sync --all-groups --frozen (from the project root)"
            exit 1
        fi
    else
        print_error "Failed to install backend dependencies properly"
        print_error "Try running: uv sync --all-groups --frozen (from the project root)"
        exit 1
    fi
}

# Function to install frontend dependencies
install_frontend() {
    print_status "Installing frontend dependencies..."

    cd frontend

    # Check if node_modules exists and has content
    if [[ -d "node_modules" ]] && [[ -n "$(ls -A node_modules 2>/dev/null)" ]]; then
        print_success "Frontend dependencies already installed!"
    else
        print_status "Installing Node.js dependencies..."
        npm install
        print_success "Frontend dependencies installed!"
    fi

    cd ..
}

# Function to start both services
start_services() {
    print_status "Starting the AI Hedge Fund web application..."
    print_status "This will start both the backend API and frontend web interface"
    print_status "Press Ctrl+C to stop both services"
    echo ""

    # Create logs directory in the app folder if it doesn't exist
    LOG_DIR="$(pwd)/logs"
    mkdir -p "$LOG_DIR"

    # Create timestamped log files
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKEND_LOG="$LOG_DIR/backend_${TIMESTAMP}.log"
    FRONTEND_LOG="$LOG_DIR/frontend_${TIMESTAMP}.log"

    # Function to cleanup on exit
    cleanup() {
        print_status "Shutting down services..."

        # Kill backend and all its child processes
        if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_status "Stopping backend (PID: $BACKEND_PID)..."
            # Kill the entire process group
            pkill -P "$BACKEND_PID" 2>/dev/null || true
            kill "$BACKEND_PID" 2>/dev/null || true
            # Wait a moment
            sleep 1
            # Force kill if still running
            kill -9 "$BACKEND_PID" 2>/dev/null || true
        fi

        # Kill frontend and all its child processes
        if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_status "Stopping frontend (PID: $FRONTEND_PID)..."
            # Kill the entire process group
            pkill -P "$FRONTEND_PID" 2>/dev/null || true
            kill "$FRONTEND_PID" 2>/dev/null || true
            # Wait a moment
            sleep 1
            # Force kill if still running
            kill -9 "$FRONTEND_PID" 2>/dev/null || true
        fi

        # Extra cleanup: kill any remaining processes by pattern
        pkill -f "uvicorn.*app.backend.main" 2>/dev/null || true
        pkill -f "vite.*vite.config" 2>/dev/null || true

        # Kill processes by port as last resort
        lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
        lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
        lsof -ti:5174 2>/dev/null | xargs kill -9 2>/dev/null || true

        # Log files are preserved in the logs directory
        print_status "Log files saved in: $LOG_DIR"

        print_success "Services stopped. Goodbye!"
        exit 0
    }

    # Set up signal handlers
    trap cleanup SIGINT SIGTERM

    # Pre-startup cleanup: kill any existing processes on our ports
    print_status "Checking for existing services on ports 8000, 5173, 5174..."
    if lsof -ti:8000 >/dev/null 2>&1; then
        print_warning "Port 8000 is in use. Killing existing process..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    if lsof -ti:5173 >/dev/null 2>&1; then
        print_warning "Port 5173 is in use. Killing existing process..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    if lsof -ti:5174 >/dev/null 2>&1; then
        print_warning "Port 5174 is in use. Killing existing process..."
        lsof -ti:5174 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi

    # Start backend
    print_status "Starting backend server... Logging to $BACKEND_LOG"
    # Run from the app directory (parent of backend) to ensure proper Python imports
    cd ..
    uv run uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    cd app

    # Wait a moment for backend to start
    sleep 3

    # Check if backend started successfully
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        print_error "Backend failed to start. Check the logs:"
        cat "$BACKEND_LOG"
        exit 1
    fi

    print_success "Backend server started (PID: $BACKEND_PID)"

    # Check database initialization
    print_status "Checking database initialization..."
    sleep 2  # Give backend time to initialize database

    if [[ -f "../hedge_fund.db" ]]; then
        print_success "Database initialized successfully!"
    else
        print_warning "Database file not found, but will be created on first API call"
    fi

    # Start frontend
    print_status "Starting frontend development server... Logging to $FRONTEND_LOG"
    cd frontend
    npm run dev > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    cd ..

    # Wait a moment for frontend to start
    sleep 5

    # Check if frontend started successfully
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        print_error "Frontend failed to start. Check the logs:"
        cat "$FRONTEND_LOG"
        cleanup
        exit 1
    fi

    print_success "Frontend development server started (PID: $FRONTEND_PID)"

    # Open browser after frontend is running
    print_status "Opening web browser..."
    sleep 2  # Give frontend a moment to fully start
    open_browser "http://localhost:5173"

    echo ""
    print_success "🚀 AI Hedge Fund web application is now running!"
    print_success "🌐 Browser should open automatically to http://localhost:5173"
    echo ""
    print_status "Frontend (Web Interface): http://localhost:5173"
    print_status "Backend (API): http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Database: SQLite (hedge_fund.db in project root)"
    echo ""
    print_status "📋 Logs are being saved to:"
    print_status "   Backend: $BACKEND_LOG"
    print_status "   Frontend: $FRONTEND_LOG"
    echo ""
    print_status "Press Ctrl+C to stop both services"
    echo ""

    # Wait for user interrupt
    while true; do
        # Check if processes are still running
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            break
        fi

        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            break
        fi

        sleep 1
    done

    cleanup
}

# Main execution
main() {
    echo ""
    print_status "🚀 AI Hedge Fund Web Application Setup"
    print_status "This script will install dependencies and start both frontend and backend services"
    echo ""

    check_directory
    check_prerequisites
    setup_environment
    setup_database
    install_backend
    install_frontend
    start_services
}

# Show help if requested
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "AI Hedge Fund Web Application Setup and Runner"
    echo ""
    echo "Usage: ./run.sh"
    echo ""
    echo "This script will:"
    echo "  1. Check for required dependencies (Node.js, npm, Python, uv)"
    echo "  2. Install backend dependencies using uv"
    echo "  3. Install frontend dependencies using npm"
    echo "  4. Start both the backend API server and frontend development server"
    echo "  5. Automatically initialize SQLite database on first run"
    echo ""
    echo "Requirements:"
    echo "  - Node.js and npm (https://nodejs.org/)"
    echo "  - Python 3 (https://python.org/)"
    echo "  - uv (https://docs.astral.sh/uv/)"
    echo ""
    echo "After running, you can access:"
    echo "  - Frontend: http://localhost:5173"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Database: SQLite file (hedge_fund.db) in project root"
    echo ""
    exit 0
fi

# Run main function
main
