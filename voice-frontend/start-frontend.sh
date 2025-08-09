#!/bin/bash

# United Voice Agent Frontend Startup Script
# This script checks for backend availability and starts the Next.js development server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_PORT="3000"
MAX_BACKEND_WAIT_TIME=30  # seconds
BACKEND_CHECK_INTERVAL=2  # seconds

echo -e "${BLUE}🚀 United Voice Agent Frontend Startup${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check backend health
check_backend() {
    local url=$1
    if curl -s --max-time 3 "$url/health" >/dev/null 2>&1; then
        return 0  # Backend is responding
    else
        return 1  # Backend is not responding
    fi
}

# Function to wait for backend
wait_for_backend() {
    local url=$1
    local max_wait=$2
    local interval=$3
    local elapsed=0
    
    log_step "Waiting for backend server at $url..."
    
    while [ $elapsed -lt $max_wait ]; do
        if check_backend "$url"; then
            log_success "Backend server is responding!"
            return 0
        fi
        
        echo -ne "\r${YELLOW}⏳ Waiting for backend... ${elapsed}s/${max_wait}s${NC}"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo ""  # New line after the progress indicator
    return 1  # Timeout
}

# Function to check Node.js and npm
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version)
        log_success "Node.js found: $node_version"
    else
        log_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check npm
    if command -v npm >/dev/null 2>&1; then
        local npm_version=$(npm --version)
        log_success "npm found: $npm_version"
    else
        log_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check if package.json exists
    if [ -f "package.json" ]; then
        log_success "package.json found"
    else
        log_error "package.json not found. Are you in the frontend directory?"
        exit 1
    fi
}

# Function to install dependencies if needed
check_dependencies() {
    log_step "Checking dependencies..."
    
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        log_warning "Dependencies not installed or outdated"
        log_step "Installing dependencies with npm install..."
        
        if npm install; then
            log_success "Dependencies installed successfully"
        else
            log_error "Failed to install dependencies"
            exit 1
        fi
    else
        log_success "Dependencies are up to date"
    fi
}

# Function to start the development server
start_dev_server() {
    local port=$1
    
    log_step "Starting Next.js development server on port $port..."
    
    # Check if port is already in use
    if check_port $port; then
        log_warning "Port $port is already in use"
        
        # Try to find the process using the port
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            log_info "Process using port $port: PID $pid"
            
            echo -n "Do you want to kill the existing process and continue? (y/N): "
            read -r response
            
            if [[ "$response" =~ ^[Yy]$ ]]; then
                log_step "Terminating existing process..."
                kill $pid
                sleep 2
                
                if ! check_port $port; then
                    log_success "Port $port is now free"
                else
                    log_error "Failed to free port $port"
                    exit 1
                fi
            else
                log_info "Startup cancelled by user"
                exit 0
            fi
        fi
    fi
    
    # Set environment variables
    export NODE_ENV=development
    export NEXT_TELEMETRY_DISABLED=1
    
    log_success "Starting development server..."
    log_info "Frontend will be available at: http://localhost:$port"
    log_info "Voice interface: http://localhost:$port/voice"
    log_info "Test page: http://localhost:$port/test"
    echo ""
    log_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the Next.js development server
    npm run dev -- --port $port
}

# Function to open browser
open_browser() {
    local url="http://localhost:$FRONTEND_PORT"
    local test_url="http://localhost:$FRONTEND_PORT/test"
    
    log_step "Opening browser..."
    
    # Detect OS and open browser accordingly
    case "$(uname -s)" in
        Darwin)  # macOS
            open "$test_url" 2>/dev/null || log_warning "Could not open browser automatically"
            ;;
        Linux)   # Linux
            xdg-open "$test_url" 2>/dev/null || log_warning "Could not open browser automatically"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)  # Windows
            start "$test_url" 2>/dev/null || log_warning "Could not open browser automatically"
            ;;
        *)
            log_warning "Unknown OS, cannot open browser automatically"
            ;;
    esac
    
    if command -v open >/dev/null 2>&1 || command -v xdg-open >/dev/null 2>&1 || command -v start >/dev/null 2>&1; then
        log_success "Browser should open automatically"
        log_info "If not, manually visit: $test_url"
    else
        log_info "Please manually visit: $test_url"
    fi
}

# Main execution
main() {
    echo -e "${CYAN}Starting United Voice Agent Frontend...${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Check and install dependencies
    check_dependencies
    
    # Backend connectivity check
    log_step "Checking backend connectivity..."
    
    if check_backend "$BACKEND_URL"; then
        log_success "Backend server is already running and responding!"
    else
        log_warning "Backend server is not responding at $BACKEND_URL"
        
        echo -n "Do you want to start the frontend anyway? The voice features may not work until the backend is running. (y/N): "
        read -r response
        
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Please start the backend server first:"
            log_info "  1. Navigate to the backend directory"
            log_info "  2. Run: python websocket_main.py"
            log_info "  3. Wait for it to start on port 8000"
            log_info "  4. Then run this script again"
            echo ""
            log_info "Or run with --skip-backend-check to bypass this check"
            exit 0
        fi
        
        log_warning "Starting frontend without backend connectivity"
    fi
    
    echo ""
    log_success "All checks passed! Starting development server..."
    echo ""
    
    # Schedule browser opening after a delay (in background)
    (
        sleep 3
        open_browser
    ) &
    
    # Start the development server (this will block)
    start_dev_server $FRONTEND_PORT
}

# Handle command line arguments
if [ "$1" = "--skip-backend-check" ]; then
    log_info "Skipping backend connectivity check"
    SKIP_BACKEND_CHECK=true
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo -e "${BLUE}United Voice Agent Frontend Startup Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-backend-check    Skip the backend connectivity check"
    echo "  --help, -h              Show this help message"
    echo ""
    echo "This script will:"
    echo "  1. Check Node.js and npm prerequisites"
    echo "  2. Install dependencies if needed"
    echo "  3. Check backend connectivity (optional)"
    echo "  4. Start the Next.js development server"
    echo "  5. Open the test page in your browser"
    echo ""
    echo "Backend URL: $BACKEND_URL"
    echo "Frontend Port: $FRONTEND_PORT"
    echo "Test Page: http://localhost:$FRONTEND_PORT/test"
    echo ""
    exit 0
fi

# Trap to handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}👋 Shutting down frontend server...${NC}"; exit 0' INT TERM

# Run main function
main

# If we reach here, the server has stopped
log_info "Frontend server has stopped"