#!/usr/bin/env python3
"""
Test script to verify WebSocket server connection
Run this after starting the WebSocket server
"""

import asyncio
import socketio
import sys
import time

async def test_websocket_connection():
    """Test WebSocket connection to the server"""
    print("🧪 Testing WebSocket Connection...")
    print("="*50)
    
    # Create Socket.IO client
    sio = socketio.AsyncClient()
    
    # Event handlers
    @sio.event
    async def connect():
        print("✅ Connected to WebSocket server")
        
    @sio.event
    async def disconnect():
        print("❌ Disconnected from WebSocket server")
    
    @sio.event
    async def connected(data):
        print(f"📋 Server welcome message: {data.get('message', 'N/A')}")
        print(f"📋 Session ID: {data.get('session_id', 'N/A')}")
    
    @sio.event
    async def agent_response(data):
        print(f"🤖 Agent Response: {data.get('text', 'N/A')}")
    
    @sio.event
    async def health_response(data):
        print(f"💚 Health Check: {data.get('status', 'N/A')}")
        print(f"📊 Active Sessions: {data.get('active_sessions', 'N/A')}")
    
    @sio.event
    async def error(data):
        print(f"❌ Error: {data.get('message', 'N/A')}")
    
    try:
        # Connect to server
        await sio.connect('http://localhost:8000')
        
        # Wait for initial greeting
        await asyncio.sleep(2)
        
        # Send health check
        print("\n🔍 Sending health check...")
        await sio.emit('health_check')
        
        # Wait for response
        await asyncio.sleep(2)
        
        # Test session state request
        print("\n📊 Requesting session state...")
        await sio.emit('get_session_state')
        
        # Wait for response
        await asyncio.sleep(2)
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the WebSocket server is running (./start-websocket-server.sh)")
        print("2. Check if port 8000 is available")
        print("3. Verify your .env file has the required API keys")
        return False
    
    finally:
        if sio.connected:
            await sio.disconnect()
    
    return True

async def test_http_api():
    """Test HTTP API endpoints"""
    print("\n🌐 Testing HTTP API...")
    print("="*50)
    
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get('http://localhost:8000/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health endpoint: {data.get('status', 'N/A')}")
                    print(f"📋 Services: {data.get('services', {})}")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
            
            # Test config endpoint
            async with session.get('http://localhost:8000/api/config') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Config endpoint: WebSocket available")
                    print(f"📋 Audio formats: {data.get('audio', {}).get('supported_formats', [])}")
                else:
                    print(f"❌ Config endpoint failed: {response.status}")
    
    except Exception as e:
        print(f"❌ HTTP API test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🚀 United Voice Agent - Connection Test")
    print("="*60)
    
    # Test HTTP API first
    http_success = await test_http_api()
    
    if http_success:
        # Test WebSocket connection
        ws_success = await test_websocket_connection()
        
        if ws_success:
            print("\n🎉 All tests passed! Your WebSocket integration is working correctly.")
            print("\nNext steps:")
            print("1. Start the frontend: cd frontend && ./start-frontend.sh")
            print("2. Open http://localhost:3000 in your browser")
            print("3. Test voice recording functionality")
        else:
            print("\n❌ WebSocket tests failed. Please check the server logs.")
    else:
        print("\n❌ HTTP API tests failed. Please check if the server is running.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)