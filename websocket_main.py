#!/usr/bin/env python3
"""
Main WebSocket server entry point for United Voice Agent
Run this file to start the WebSocket server for frontend integration
"""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
environment = os.getenv('ENVIRONMENT', 'development')
if environment == 'production':
    # Load production environment
    env_file = '.env.production'
    if Path(env_file).exists():
        load_dotenv(env_file)
        print(f"🔧 Loaded production environment from {env_file}")
    else:
        print(f"⚠️  Production environment file {env_file} not found, using system environment")
else:
    # Load default .env for development
    load_dotenv()

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.services.websocket_server import create_websocket_app

def main():
    """Main function to run the WebSocket server"""
    from src.services.websocket_config import get_websocket_config
    
    # Get configuration
    config = get_websocket_config()
    
    print("🚀 Starting United Voice Agent WebSocket Server...")
    print("="*60)
    print(f"Environment: {config.environment}")
    print(f"Server will be available at:")
    print(f"  • WebSocket: ws://{config.host}:{config.port}")
    print(f"  • Socket.IO: http://{config.host}:{config.port}")
    print(f"CORS Origins:")
    for origin in config.cors_allowed_origins:
        print(f"  • {origin}")
    print("="*60)
    
    # Create the ASGI app
    app = create_websocket_app()
    
    # Get uvicorn config from websocket config
    uvicorn_config = config.get_uvicorn_config()
    
    # Override reload for production
    if config.environment == "production":
        uvicorn_config['reload'] = False
    else:
        uvicorn_config['reload'] = True
        uvicorn_config['reload_dirs'] = [str(src_dir)]
    
    # Run the server
    uvicorn.run(app, **uvicorn_config)

if __name__ == "__main__":
    main()