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
    import logging
    from src.services.websocket_server import create_websocket_app
    from src.services.websocket_config import get_websocket_config
    
    # Set up logging
    logger = logging.getLogger(__name__)
    
    # Get configuration
    config = get_websocket_config()
    
    if config.environment == "production":
        logger.info("🚀 Starting United Voice Agent WebSocket Server...")
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Host: {config.host}:{config.port}")
        logger.info(f"SSL Enabled: {config.ssl_enabled}")
        logger.info(f"CORS Origins: {len(config.cors_allowed_origins)} configured")
    else:
        print("🚀 Starting United Voice Agent WebSocket Server...")
        print("="*60)
        print(f"Environment: {config.environment}")
        print(f"Host: {config.host}:{config.port}")
        print(f"SSL Enabled: {config.ssl_enabled}")
        print(f"CORS Origins: {len(config.cors_allowed_origins)} configured")
        print(f"  • WebSocket: ws://localhost:{config.port}")
        print(f"  • Socket.IO: http://localhost:{config.port}")
        print("="*60)
    
    # Create app and get uvicorn configuration
    app = create_websocket_app()
    uvicorn_config = config.get_uvicorn_config()
    
    # Run server
    uvicorn.run(app, **uvicorn_config)