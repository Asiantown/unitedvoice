#!/usr/bin/env python3
"""
Simple WebSocket test to verify Socket.IO connection
"""

import asyncio
import socketio
import json

async def simple_websocket_test():
    """Simple test of WebSocket connection"""
    print("🧪 Simple WebSocket Test")
    print("="*40)
    
    # Create client
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
    
    # Event handlers
    @sio.event
    async def connect():
        print("✅ Connected successfully!")
        
    @sio.event
    async def disconnect():
        print("❌ Disconnected")
        
    @sio.event
    async def connected(data):
        print(f"📋 Welcome message: {json.dumps(data, indent=2)}")
        
    @sio.event
    async def agent_response(data):
        text = data.get('text', '')
        has_audio = 'audio' in data
        print(f"🤖 Agent said: {text[:50]}...")
        print(f"🔊 Has audio: {has_audio}")
        
    @sio.event
    async def error(data):
        print(f"❌ Error: {data}")
    
    try:
        # Connect
        print("Connecting to ws://localhost:8000...")
        await sio.connect('http://localhost:8000')
        
        # Wait for initial greeting
        print("Waiting for greeting...")
        await asyncio.sleep(5)
        
        # Send health check
        print("Sending health check...")
        await sio.emit('health_check')
        await asyncio.sleep(2)
        
        print("✅ Test completed successfully!")
        
        # Disconnect
        await sio.disconnect()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_websocket_test())