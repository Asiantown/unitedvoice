#!/bin/bash

# Deploy United Voice Agent Backend to Railway
# This script helps automate the Railway deployment process

set -e  # Exit on error

echo "🚀 United Voice Agent - Railway Deployment Helper"
echo "=================================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Railway CLI found"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

echo "✅ Git repository detected"

# Check if required files exist
required_files=("requirements.txt" "Procfile" "railway.json" "start_websocket.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required deployment files found"

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes. Committing them now..."
    git add .
    git commit -m "Prepare for Railway deployment"
    echo "✅ Changes committed"
fi

# Initialize Railway project if not already done
if [ ! -f ".railway/project.json" ]; then
    echo "🔧 Initializing Railway project..."
    railway init
    echo "✅ Railway project initialized"
else
    echo "✅ Railway project already initialized"
fi

echo ""
echo "📋 IMPORTANT: Set these environment variables in Railway dashboard:"
echo "=================================================="
echo "Required API Keys:"
echo "  • GROQ_API_KEY=your_groq_api_key_here"
echo "  • ELEVENLABS_API_KEY=your_elevenlabs_api_key_here"  
echo "  • SERPAPI_API_KEY=your_serpapi_api_key_here"
echo ""
echo "CORS Configuration:"
echo "  • CORS_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app"
echo ""
echo "Optional Environment Variables:"
echo "  • ENVIRONMENT=production"
echo "  • LOG_LEVEL=INFO"
echo "  • MAX_CONNECTIONS=1000"
echo "=================================================="
echo ""

read -p "Have you set the environment variables in Railway dashboard? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please set the environment variables first:"
    echo "1. Go to https://railway.app/dashboard"
    echo "2. Select your project"
    echo "3. Go to Variables tab"
    echo "4. Add the required environment variables"
    echo "5. Re-run this script"
    exit 1
fi

echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Wait for deployment to complete in Railway dashboard"
echo "2. Get your Railway URL from the dashboard"
echo "3. Test your deployment with: python verify_deployment.py <your-railway-url>"
echo "4. Use the Railway URL as NEXT_PUBLIC_WS_URL in your Vercel frontend"
echo ""
echo "🔗 Railway Dashboard: https://railway.app/dashboard"
echo ""