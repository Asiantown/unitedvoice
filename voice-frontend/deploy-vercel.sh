#!/bin/bash

# =============================================================================
# United Voice Agent Frontend - Vercel Deployment Script
# =============================================================================
# This script automates the deployment process to Vercel
# Run with: ./deploy-vercel.sh [--production|--preview]
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [[ ! -f "package.json" ]] || [[ ! -f "next.config.ts" ]]; then
    log_error "Please run this script from the voice-frontend directory"
    exit 1
fi

# Parse arguments
DEPLOYMENT_TYPE="preview"
if [[ "$1" == "--production" ]]; then
    DEPLOYMENT_TYPE="production"
elif [[ "$1" == "--preview" ]]; then
    DEPLOYMENT_TYPE="preview"
elif [[ -n "$1" ]]; then
    log_error "Invalid argument: $1"
    echo "Usage: $0 [--production|--preview]"
    exit 1
fi

log_info "Starting deployment process..."
log_info "Deployment type: $DEPLOYMENT_TYPE"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    log_error "Vercel CLI is not installed"
    log_info "Please install it with: npm install -g vercel"
    exit 1
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    log_error "You are not logged in to Vercel"
    log_info "Please run: vercel login"
    exit 1
fi

# Clean previous builds
log_info "Cleaning previous builds..."
npm run clean

# Install dependencies
log_info "Installing dependencies..."
npm install

# Run tests (if any)
log_info "Running tests..."
npm run test

# Build the project
log_info "Building project..."
npm run build

log_success "Build completed successfully!"

# Deploy to Vercel
log_info "Deploying to Vercel..."

if [[ "$DEPLOYMENT_TYPE" == "production" ]]; then
    log_warning "Deploying to PRODUCTION!"
    read -p "Are you sure you want to deploy to production? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    vercel --prod
else
    log_info "Deploying preview..."
    vercel
fi

log_success "Deployment completed!"

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls | head -2 | tail -1 | awk '{print $2}')
if [[ -n "$DEPLOYMENT_URL" ]]; then
    log_success "Your application is available at: https://$DEPLOYMENT_URL"
else
    log_info "Run 'vercel ls' to see your deployment URL"
fi

log_info "Deployment script completed!"