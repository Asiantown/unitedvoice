#!/usr/bin/env python3
"""
Production WebSocket server starter with environment-based configuration
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to Python path for proper imports
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn
    from src.services.websocket_server import create_websocket_app
    from src.services.websocket_config import get_websocket_config
    
    # Get configuration
    config = get_websocket_config()
    
    print("🚀 Starting United Voice Agent WebSocket Server...")
    print("="*60)
    print(f"Environment: {config.environment}")
    print(f"Host: {config.host}:{config.port}")
    print(f"SSL Enabled: {config.ssl_enabled}")
    print(f"CORS Origins: {len(config.cors_allowed_origins)} configured")
    
    if config.environment == "production":
        protocol = "wss" if config.ssl_enabled else "ws"
        print(f"  • WebSocket: {protocol}://your-domain.com")
        print(f"  • Socket.IO: https://your-domain.com")
    else:
        print(f"  • WebSocket: ws://localhost:{config.port}")
        print(f"  • Socket.IO: http://localhost:{config.port}")
    
    print("="*60)
    
    # Create app and get uvicorn configuration
    app = create_websocket_app()
    uvicorn_config = config.get_uvicorn_config()
    
    # Run server
    uvicorn.run(app, **uvicorn_config)