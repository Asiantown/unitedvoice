#!/bin/bash
# Railway deployment script with environment variable verification
# This script helps ensure proper Railway deployment with correct env vars

echo "🚂 Railway Deployment with Environment Variable Check"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_status "❌ Railway CLI not found. Installing..." $RED
    echo "Please install Railway CLI:"
    echo "npm install -g @railway/cli"
    echo "or"
    echo "curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

print_status "✅ Railway CLI found" $GREEN

# Login check
if ! railway whoami &> /dev/null; then
    print_status "⚠️  Not logged in to Railway. Please login:" $YELLOW
    echo "railway login"
    exit 1
fi

print_status "✅ Logged in to Railway" $GREEN

# Check if we're in a Railway project
if ! railway status &> /dev/null; then
    print_status "⚠️  Not in a Railway project directory." $YELLOW
    echo "Please run 'railway link' to connect to your project."
    exit 1
fi

# Get project info
PROJECT_INFO=$(railway status 2>/dev/null | grep -E "(Project|Service|Environment)")
print_status "📋 Project Information:" $BLUE
echo "$PROJECT_INFO"

# Check current environment variables
print_status "🔍 Checking current environment variables..." $BLUE

# Function to check if a variable is set in Railway
check_railway_var() {
    local var_name=$1
    local description=$2
    
    # Get the variable value (this won't work locally, but we can try)
    local var_value=$(railway variables get $var_name 2>/dev/null || echo "")
    
    if [ -n "$var_value" ] && [ "$var_value" != "Variable not found" ]; then
        # Mask the value for security
        local masked_value="${var_value:0:4}...${var_value: -4}"
        print_status "  ✅ $var_name: SET ($masked_value)" $GREEN
        
        # Additional validation for GROQ key
        if [ "$var_name" == "GROQ_API_KEY" ]; then
            if [[ $var_value == gsk_* ]]; then
                print_status "    ✅ Format looks correct (starts with gsk_)" $GREEN
            else
                print_status "    ⚠️  WARNING: Should start with 'gsk_'" $YELLOW
            fi
        fi
        
        return 0
    else
        print_status "  ❌ $var_name: NOT SET ($description)" $RED
        return 1
    fi
}

# Check required environment variables
print_status "🔧 Environment Variables Status:" $BLUE
required_vars=("GROQ_API_KEY:Groq API for LLM/STT" "ELEVENLABS_API_KEY:ElevenLabs for TTS" "SERPAPI_API_KEY:SerpAPI for flights")

missing_vars=0
for var_info in "${required_vars[@]}"; do
    IFS=":" read -r var_name description <<< "$var_info"
    if ! check_railway_var "$var_name" "$description"; then
        ((missing_vars++))
    fi
done

# If variables are missing, provide instructions
if [ $missing_vars -gt 0 ]; then
    print_status "⚠️  $missing_vars environment variable(s) missing!" $YELLOW
    echo
    print_status "📝 To set missing variables:" $BLUE
    echo "1. Use Railway dashboard: https://railway.app/dashboard"
    echo "2. Or use CLI commands:"
    echo
    for var_info in "${required_vars[@]}"; do
        IFS=":" read -r var_name description <<< "$var_info"
        echo "   railway variables set $var_name=your_actual_key_here"
    done
    echo
    print_status "Would you like to continue deployment anyway? (y/N): " $YELLOW
    read -r continue_deploy
    if [[ ! $continue_deploy =~ ^[Yy]$ ]]; then
        print_status "❌ Deployment cancelled. Please set environment variables first." $RED
        exit 1
    fi
fi

# Deploy the application
print_status "🚀 Starting deployment..." $BLUE
railway up --detach

if [ $? -eq 0 ]; then
    print_status "✅ Deployment started successfully!" $GREEN
    
    # Wait a moment for deployment to start
    sleep 5
    
    print_status "📊 Checking deployment status..." $BLUE
    railway status
    
    print_status "📋 Recent logs:" $BLUE
    railway logs --tail 20
    
    print_status "🌐 Getting service URL..." $BLUE
    SERVICE_URL=$(railway domain 2>/dev/null || echo "No domain configured")
    if [ "$SERVICE_URL" != "No domain configured" ]; then
        print_status "🔗 Service URL: $SERVICE_URL" $GREEN
    else
        print_status "⚠️  No custom domain configured. Using Railway-generated URL." $YELLOW
    fi
    
    print_status "✅ Deployment completed!" $GREEN
    echo
    print_status "📝 Next steps:" $BLUE
    echo "1. Monitor logs: railway logs -f"
    echo "2. Check app status: railway status"
    echo "3. Test environment variables in the deployed app"
    echo "4. If issues persist, run the debug script on Railway"
    
else
    print_status "❌ Deployment failed!" $RED
    echo "Check the logs for details:"
    railway logs --tail 50
    exit 1
fi

# Offer to run environment check
echo
print_status "Would you like to run an environment variable check on the deployed app? (y/N): " $YELLOW
read -r run_check
if [[ $run_check =~ ^[Yy]$ ]]; then
    print_status "🔍 Running environment check on deployed app..." $BLUE
    railway run python railway_startup_check.py
fi