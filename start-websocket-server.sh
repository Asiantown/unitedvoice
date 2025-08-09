#!/bin/bash

# Start WebSocket Server for United Voice Agent
echo "🚀 Starting United Voice Agent WebSocket Server..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo "GROQ_API_KEY=your_groq_api_key_here"
    echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the WebSocket server
echo "Starting WebSocket server on http://localhost:8000"
echo "Press Ctrl+C to stop"
python websocket_main.py