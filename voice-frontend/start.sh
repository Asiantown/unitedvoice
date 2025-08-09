#!/bin/bash

# United Voice Agent - Frontend Startup Script
echo "🚀 Starting United Voice Agent Frontend..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -e "${YELLOW}Checking backend status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}⚠️  Backend is not running!${NC}"
    echo "Please start the backend first:"
    echo "  cd /Users/ryanyin/united-voice-agent"
    echo "  uv run python start_websocket_fixed.py"
    echo ""
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Kill any existing process on port 3000
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Port 3000 is in use, killing existing process...${NC}"
    kill -9 $(lsof -Pi :3000 -sTCP:LISTEN -t)
    sleep 1
fi

# Start the development server
echo -e "${GREEN}Starting frontend server...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${GREEN}Voice Interface:${NC} http://localhost:3000/voice"
echo -e "  ${GREEN}Premium Interface:${NC} http://localhost:3000/voice-premium"
echo -e "  ${GREEN}Test Suite:${NC} http://localhost:3000/test"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Hold SPACEBAR or click the mic button to talk!${NC}"
echo ""

# Open browser after a short delay
(sleep 3 && open http://localhost:3000/voice 2>/dev/null || xdg-open http://localhost:3000/voice 2>/dev/null || start http://localhost:3000/voice 2>/dev/null) &

# Start the server
npm run dev