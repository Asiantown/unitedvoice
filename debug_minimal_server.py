#!/usr/bin/env python3
"""
Minimal WebSocket server to debug automatic greeting issue
"""

import asyncio
import socketio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection - minimal version"""
    logger.info(f"🔌 Client connected: {sid}")
    
    # Send connection confirmation (same as original)
    await sio.emit('connected', {
        'session_id': sid,
        'message': 'Connected to Debug Server',
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)
    
    logger.info(f"✅ Connection confirmation sent for {sid}")
    logger.info(f"🕐 Waiting to see if automatic greeting appears...")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"❌ Client disconnected: {sid}")

@sio.event
async def audio_data(sid, data):
    """Handle incoming audio data"""
    logger.info(f"🎤 Received audio_data from {sid}")
    logger.info(f"   Audio length: {len(data.get('audio', ''))}")
    
    # Send a test response to verify this handler works
    await sio.emit('agent_response', {
        'text': 'Test response from audio_data handler',
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)

if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    # Create FastAPI app
    app = FastAPI(title="Debug WebSocket Server")
    
    # Mount Socket.IO
    from socketio import ASGIApp
    socket_app = ASGIApp(sio, app)
    
    print("🚀 Starting Debug WebSocket Server on port 8001...")
    print("   Connect with: http://127.0.0.1:8001")
    print("   This server only sends connection confirmation.")
    print("   If automatic greeting appears, it's NOT from our code.")
    
    uvicorn.run(
        socket_app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )