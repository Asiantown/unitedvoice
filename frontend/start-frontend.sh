#!/bin/bash

# Start Next.js Frontend for United Voice Agent
echo "🚀 Starting United Voice Agent Frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Check for .env.local file
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local from .env.example..."
    cp .env.example .env.local
fi

# Start the development server
echo "Starting frontend development server on http://localhost:3000"
echo "Press Ctrl+C to stop"
npm run dev