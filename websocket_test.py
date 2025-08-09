#!/usr/bin/env python3
"""
WebSocket server test with proper error handling
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Main function to start the WebSocket server"""
    try:
        print("🚀 Starting United Voice Agent WebSocket Server...")
        print("=" * 60)
        
        # Import the websocket server
        from src.services.websocket_server import create_websocket_app
        
        # Create the app
        app = create_websocket_app()
        
        print("Server will be available at:")
        print("  • HTTP: http://localhost:8000")
        print("  • Socket.IO: http://localhost:8000/socket.io/")
        print("=" * 60)
        print("Starting server...")
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()