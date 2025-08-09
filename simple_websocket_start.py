#!/usr/bin/env python3
"""
Simple WebSocket server for production deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))
os.environ['PYTHONPATH'] = str(Path(__file__).parent.absolute())

# Load environment
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    import uvicorn
    
    # Import with full path
    from src.services.websocket_server import create_websocket_app
    
    app = create_websocket_app()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting WebSocket server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )