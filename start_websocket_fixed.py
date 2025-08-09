#!/usr/bin/env python3
"""Fixed WebSocket server starter"""

import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path('./src')))

# Import the app
from src.services.websocket_server import create_websocket_app

if __name__ == "__main__":
    print("Starting WebSocket server on port 8000...")
    app = create_websocket_app()
    
    # Run without reload to avoid issues
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # Disable reload to avoid issues
    )