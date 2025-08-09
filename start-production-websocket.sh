#!/bin/bash

# Start United Voice Agent WebSocket Server in Production Mode
echo "🚀 Starting United Voice Agent WebSocket Server (Production Mode)..."

# Set production environment
export ENVIRONMENT=production

# Set the specific frontend URL that needs to connect
export FRONTEND_URL=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app

# Use Railway's PORT if available, otherwise default to 8000
export PORT=${PORT:-8000}

# Set additional CORS origins if needed (comma-separated)
export CORS_ORIGINS="https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app,https://united-voice-agent.vercel.app,https://web-production-204e.up.railway.app"

# Enable debug logging for troubleshooting
export LOG_LEVEL=INFO

# Ensure we have the required dependencies
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check for required environment files
if [ ! -f ".env.production" ]; then
    echo "⚠️  Production environment file (.env.production) not found!"
    echo "Creating it from template..."
    
    if [ -f ".env.production.template" ]; then
        cp .env.production.template .env.production
        echo "✅ Created .env.production from template"
        echo "Please edit .env.production with your actual API keys before deploying!"
    fi
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Verify configuration
echo "🔧 Configuration Check:"
echo "  Environment: $ENVIRONMENT"
echo "  Port: $PORT"
echo "  Frontend URL: $FRONTEND_URL"
echo "  CORS Origins: $CORS_ORIGINS"
echo ""

# Show which origins will be allowed
echo "🌐 Testing CORS configuration..."
python -c "
from src.services.websocket_config import get_websocket_config
config = get_websocket_config()
print('✅ CORS Origins that will be allowed:')
for origin in config.cors_allowed_origins:
    print(f'  • {origin}')
    if 'unitedvoice-bke1yxntg-asiantowns-projects.vercel.app' in origin:
        print('    ✅ Frontend URL is included!')
"

echo ""
echo "🎯 Starting server..."
echo "Press Ctrl+C to stop"
echo ""

# Start the WebSocket server
python websocket_main.py