#!/usr/bin/env python3
"""
Main WebSocket server entry point for United Voice Agent
Run this file to start the WebSocket server for frontend integration
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.services.websocket_server import create_websocket_app

def main():
    """Main function to run the WebSocket server"""
    print("🚀 Starting United Voice Agent WebSocket Server...")
    print("="*60)
    print("Server will be available at:")
    print("  • WebSocket: ws://localhost:8000")
    print("  • Socket.IO: http://localhost:8000")
    print("="*60)
    
    # Create the ASGI app
    app = create_websocket_app()
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",  # Allow connections from frontend
        port=8000,
        log_level="info",
        reload=True,
        reload_dirs=[str(src_dir)]
    )

if __name__ == "__main__":
    main()