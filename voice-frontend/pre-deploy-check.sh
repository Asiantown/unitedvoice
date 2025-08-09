#!/bin/bash

# =============================================================================
# United Voice Agent Frontend - Pre-Deployment Checklist
# =============================================================================
# This script performs essential checks before deployment
# Run with: ./pre-deploy-check.sh
# =============================================================================

set -e

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
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_item() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

ERRORS=0
WARNINGS=0

log_info "Starting pre-deployment checklist..."
echo

# 1. Check if we're in the correct directory
check_item "Checking directory structure..."
if [[ -f "package.json" ]] && [[ -f "next.config.ts" ]] && [[ -d "src" ]]; then
    log_success "Directory structure is correct"
else
    log_error "Invalid directory structure"
    ((ERRORS++))
fi

# 2. Check for required files
check_item "Checking required files..."
REQUIRED_FILES=("vercel.json" ".env.production.example" "package.json" "next.config.ts")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        log_success "$file exists"
    else
        log_error "$file is missing"
        ((ERRORS++))
    fi
done

# 3. Check dependencies
check_item "Checking dependencies..."
if npm list --depth=0 > /dev/null 2>&1; then
    log_success "All dependencies are installed"
else
    log_error "Some dependencies are missing"
    log_info "Run: npm install"
    ((ERRORS++))
fi

# 4. Check build
check_item "Testing build process..."
if npm run build > /dev/null 2>&1; then
    log_success "Build process works"
    rm -rf .next  # Clean up
else
    log_error "Build process failed"
    log_info "Run: npm run build (to see detailed errors)"
    ((ERRORS++))
fi

# 5. Check environment variables
check_item "Checking environment configuration..."
if [[ -f ".env.local" ]]; then
    log_success ".env.local exists"
else
    log_warning ".env.local not found (optional for development)"
    ((WARNINGS++))
fi

if [[ -f ".env.production.example" ]]; then
    log_success ".env.production.example exists"
else
    log_error ".env.production.example is missing"
    ((ERRORS++))
fi

# 6. Check Vercel configuration
check_item "Checking Vercel configuration..."
if [[ -f "vercel.json" ]]; then
    if grep -q "next_public_ws_url" vercel.json; then
        log_success "Vercel environment variables configured"
    else
        log_warning "Vercel environment variables may need configuration"
        ((WARNINGS++))
    fi
else
    log_error "vercel.json is missing"
    ((ERRORS++))
fi

# 7. Check for common issues
check_item "Checking for common deployment issues..."

# Check for favicon conflicts
if [[ -f "src/app/favicon.ico" ]] && [[ -f "public/favicon.ico" ]]; then
    log_error "Favicon conflict detected (both src/app/favicon.ico and public/favicon.ico exist)"
    ((ERRORS++))
else
    log_success "No favicon conflicts"
fi

# Check TypeScript configuration
if [[ -f "tsconfig.json" ]]; then
    log_success "TypeScript configuration exists"
else
    log_warning "TypeScript configuration missing"
    ((WARNINGS++))
fi

# 8. Check for security
check_item "Checking security configuration..."
if grep -q "Content-Security-Policy" next.config.ts; then
    log_success "Content Security Policy configured"
else
    log_warning "Content Security Policy not found"
    ((WARNINGS++))
fi

# 9. Check Vercel CLI
check_item "Checking Vercel CLI..."
if command -v vercel &> /dev/null; then
    log_success "Vercel CLI is installed"
    if vercel whoami &> /dev/null; then
        log_success "Logged in to Vercel"
    else
        log_error "Not logged in to Vercel"
        log_info "Run: vercel login"
        ((ERRORS++))
    fi
else
    log_error "Vercel CLI is not installed"
    log_info "Install with: npm install -g vercel"
    ((ERRORS++))
fi

# Summary
echo
log_info "Pre-deployment checklist completed!"
echo

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    log_success "All checks passed! Ready for deployment 🚀"
    echo
    log_info "To deploy:"
    echo "  Preview:    ./deploy-vercel.sh --preview"
    echo "  Production: ./deploy-vercel.sh --production"
elif [[ $ERRORS -eq 0 ]]; then
    log_warning "$WARNINGS warning(s) found, but deployment should work"
    echo
    log_info "To deploy:"
    echo "  Preview:    ./deploy-vercel.sh --preview"
    echo "  Production: ./deploy-vercel.sh --production"
else
    log_error "$ERRORS error(s) found that must be fixed before deployment"
    [[ $WARNINGS -gt 0 ]] && log_warning "$WARNINGS warning(s) also found"
    echo
    log_info "Please fix the errors above before deploying"
    exit 1
fi