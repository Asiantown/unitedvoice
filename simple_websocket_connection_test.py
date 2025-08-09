#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
Debug and test basic connection to the WebSocket server
"""

import asyncio
import socketio
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection():
    """Test basic connection to WebSocket server"""
    
    print("🧪 Testing WebSocket Connection...")
    print("=" * 40)
    
    # Create Socket.IO client
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
    
    connection_success = False
    messages_received = []
    
    @sio.event
    async def connect():
        logger.info("✅ Connected to server!")
        nonlocal connection_success
        connection_success = True
    
    @sio.event
    async def disconnect():
        logger.info("❌ Disconnected from server")
    
    @sio.event
    async def connected(data):
        logger.info(f"🔗 Connection confirmed: {data}")
        messages_received.append(('connected', data))
    
    @sio.event
    async def agent_response(data):
        logger.info(f"🤖 Agent response: {data.get('text', 'No text')[:100]}")
        messages_received.append(('agent_response', data))
    
    @sio.event
    async def error(data):
        logger.error(f"❌ Server error: {data}")
        messages_received.append(('error', data))
    
    @sio.event
    async def health_response(data):
        logger.info(f"🏥 Health response: {data}")
        messages_received.append(('health_response', data))
    
    try:
        # Try to connect
        logger.info("Attempting to connect to http://127.0.0.1:8000...")
        await sio.connect("http://127.0.0.1:8000")
        
        # Wait for connection events
        await asyncio.sleep(3)
        
        if connection_success:
            print("✅ Connection successful!")
            print(f"📝 Messages received: {len(messages_received)}")
            
            # Test health check
            logger.info("Testing health check...")
            await sio.emit('health_check')
            await asyncio.sleep(2)
            
            print(f"📝 Total messages after health check: {len(messages_received)}")
            
            # Check for automatic greetings
            auto_responses = [msg for msg in messages_received if msg[0] == 'agent_response']
            if auto_responses:
                print(f"⚠️  Received {len(auto_responses)} automatic response(s)")
                for resp in auto_responses:
                    print(f"   - {resp[1].get('text', 'No text')[:100]}")
            else:
                print("✅ No automatic greetings sent (good!)")
            
            # Disconnect
            await sio.disconnect()
            print("✅ Test completed successfully")
            return True
            
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        print(f"❌ Connection test failed: {e}")
        return False

async def test_websocket_server_status():
    """Test if the WebSocket server is responsive"""
    import aiohttp
    
    print("🔍 Testing server endpoints...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test HTTP health endpoint
            try:
                async with session.get('http://127.0.0.1:8000/health') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ HTTP Health check: {data}")
                    else:
                        print(f"⚠️  HTTP Health status: {resp.status}")
            except Exception as e:
                print(f"❌ HTTP Health check failed: {e}")
            
            # Test Socket.IO handshake
            try:
                async with session.get('http://127.0.0.1:8000/socket.io/?transport=polling') as resp:
                    print(f"✅ Socket.IO handshake status: {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"   Response length: {len(text)} chars")
                    else:
                        print(f"   Response: {await resp.text()}")
            except Exception as e:
                print(f"❌ Socket.IO handshake failed: {e}")
                
    except Exception as e:
        print(f"❌ Server status test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 WebSocket Connection Test Suite")
    print("=" * 50)
    
    # Test server status first
    await test_websocket_server_status()
    print()
    
    # Test Socket.IO connection
    success = await test_connection()
    
    if success:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Tests failed!")
        return False

if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import socketio
        import aiohttp
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Install with: pip install python-socketio aiohttp")
        exit(1)
    
    success = asyncio.run(main())
    exit(0 if success else 1)