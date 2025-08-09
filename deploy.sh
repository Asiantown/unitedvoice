#!/bin/bash

# United Voice Agent - Deployment Script
# This script helps deploy the application to various cloud platforms

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

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Function to check environment variables
check_env_vars() {
    print_status "Checking required environment variables..."
    
    required_vars=("GROQ_API_KEY" "ELEVENLABS_API_KEY" "SERPAPI_API_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_warning "Please set these variables or create a .env file"
        exit 1
    fi
    
    print_success "All required environment variables are set"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Check if test files exist
    if [[ -d "tests" ]]; then
        python -m pytest tests/ -v
    else
        print_warning "No tests directory found, skipping tests"
    fi
    
    # Run basic import tests
    python -c "from src.core.voice_agent import UnitedVoiceAgent; print('✓ Voice agent import successful')"
    python -c "from src.services.websocket_server import create_websocket_app; print('✓ WebSocket server import successful')"
    
    print_success "Basic tests passed"
}

# Function to build frontend
build_frontend() {
    print_status "Building frontend..."
    
    cd voice-frontend
    
    # Install dependencies
    npm install
    
    # Run build
    npm run build:prod
    
    print_success "Frontend built successfully"
    cd ..
}

# Function to deploy to Heroku
deploy_heroku() {
    print_status "Deploying to Heroku..."
    
    check_command "heroku"
    
    # Check if Heroku app exists
    if ! heroku apps:info &> /dev/null; then
        print_error "No Heroku app found. Please run 'heroku create <app-name>' first"
        exit 1
    fi
    
    # Set environment variables
    print_status "Setting Heroku environment variables..."
    heroku config:set ENVIRONMENT=production
    heroku config:set GROQ_API_KEY="$GROQ_API_KEY"
    heroku config:set ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY"
    heroku config:set SERPAPI_API_KEY="$SERPAPI_API_KEY"
    heroku config:set CORS_ORIGINS="$CORS_ORIGINS"
    heroku config:set SSL_ENABLED=false
    heroku config:set LOG_LEVEL=INFO
    
    # Deploy
    git push heroku main
    
    # Scale dynos
    heroku ps:scale web=1
    
    print_success "Deployed to Heroku successfully"
}

# Function to deploy to Railway
deploy_railway() {
    print_status "Deploying to Railway..."
    
    check_command "railway"
    
    # Login check
    if ! railway whoami &> /dev/null; then
        print_error "Not logged into Railway. Please run 'railway login' first"
        exit 1
    fi
    
    # Deploy
    railway up
    
    print_success "Deployed to Railway successfully"
}

# Function to deploy to Render
deploy_render() {
    print_status "Deploying to Render..."
    
    print_warning "Render deployment is managed through their web interface"
    print_status "Please:"
    print_status "1. Connect your GitHub repository to Render"
    print_status "2. Configure environment variables in the Render dashboard"
    print_status "3. Deploy will happen automatically on git push"
}

# Function to deploy frontend to Vercel
deploy_vercel_frontend() {
    print_status "Deploying frontend to Vercel..."
    
    check_command "vercel"
    
    cd voice-frontend
    
    # Build first
    npm run build:prod
    
    # Deploy
    vercel --prod
    
    print_success "Frontend deployed to Vercel successfully"
    cd ..
}

# Main deployment function
deploy() {
    local platform="$1"
    
    print_status "Starting deployment to $platform..."
    
    # Load environment variables if .env exists
    if [[ -f ".env" ]]; then
        print_status "Loading environment variables from .env..."
        export $(cat .env | xargs)
    fi
    
    # Run pre-deployment checks
    check_env_vars
    run_tests
    
    case "$platform" in
        "heroku")
            deploy_heroku
            ;;
        "railway")
            deploy_railway
            ;;
        "render")
            deploy_render
            ;;
        "vercel")
            deploy_vercel_frontend
            ;;
        "all")
            deploy_heroku
            deploy_vercel_frontend
            ;;
        *)
            print_error "Unknown platform: $platform"
            print_status "Available platforms: heroku, railway, render, vercel, all"
            exit 1
            ;;
    esac
    
    print_success "Deployment completed!"
}

# Function to setup development environment
setup_dev() {
    print_status "Setting up development environment..."
    
    # Create .env from template if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cp .env.production.template .env
        print_warning "Created .env file from template. Please fill in your API keys."
    fi
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd voice-frontend
    npm install
    cd ..
    
    print_success "Development environment setup complete"
    print_status "Next steps:"
    print_status "1. Edit .env file with your API keys"
    print_status "2. Run 'python start_websocket.py' to start the backend"
    print_status "3. Run 'npm run dev' in the voice-frontend directory to start the frontend"
}

# Function to show help
show_help() {
    echo "United Voice Agent - Deployment Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  deploy <platform>  Deploy to specified platform (heroku, railway, render, vercel, all)"
    echo "  setup-dev         Setup development environment"
    echo "  test             Run tests only"
    echo "  build            Build frontend only"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy heroku    # Deploy backend to Heroku"
    echo "  $0 deploy vercel    # Deploy frontend to Vercel"
    echo "  $0 deploy all       # Deploy to Heroku + Vercel"
    echo "  $0 setup-dev        # Setup development environment"
}

# Main script logic
case "${1:-}" in
    "deploy")
        if [[ -z "${2:-}" ]]; then
            print_error "Platform required for deploy command"
            show_help
            exit 1
        fi
        deploy "$2"
        ;;
    "setup-dev")
        setup_dev
        ;;
    "test")
        check_env_vars
        run_tests
        ;;
    "build")
        build_frontend
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac