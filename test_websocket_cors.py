#!/usr/bin/env python3
"""
WebSocket CORS Connection Test
Tests the WebSocket connection from the exact frontend URL to ensure CORS is working correctly
"""

import asyncio
import json
import logging
import os
from datetime import datetime
import socketio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketCORSTest:
    def __init__(self, server_url: str, origin_url: str):
        self.server_url = server_url
        self.origin_url = origin_url
        self.sio = None
        self.connection_successful = False
        self.errors = []
        
    async def test_connection(self):
        """Test WebSocket connection with specified origin"""
        try:
            logger.info(f"Testing WebSocket connection...")
            logger.info(f"Server URL: {self.server_url}")
            logger.info(f"Origin: {self.origin_url}")
            
            # Create Socket.IO client with origin headers
            self.sio = socketio.AsyncClient(
                logger=True,
                engineio_logger=True
            )
            
            # Set up event handlers
            @self.sio.event
            async def connect():
                logger.info("✅ Successfully connected to WebSocket server!")
                self.connection_successful = True
                
                # Send a test message
                await self.sio.emit('health_check')
            
            @self.sio.event
            async def connect_error(data):
                error_msg = f"❌ Connection error: {data}"
                logger.error(error_msg)
                self.errors.append(error_msg)
            
            @self.sio.event
            async def disconnect():
                logger.info("🔌 Disconnected from server")
            
            @self.sio.event
            async def health_response(data):
                logger.info(f"📊 Health check response: {data}")
                # Disconnect after successful health check
                await self.sio.disconnect()
            
            # Attempt connection with origin header
            headers = {
                'Origin': self.origin_url,
                'User-Agent': 'UnitedVoiceAgent-Test/1.0'
            }
            
            logger.info(f"Connecting with headers: {headers}")
            
            try:
                await self.sio.connect(
                    self.server_url,
                    headers=headers,
                    transports=['polling', 'websocket'],  # Test both transports
                    wait_timeout=10
                )
                
                # Wait for connection and test
                await asyncio.sleep(2)
                
                if self.connection_successful:
                    logger.info("✅ Connection test PASSED")
                    return True
                else:
                    logger.error("❌ Connection test FAILED - no successful connection")
                    return False
                    
            except Exception as e:
                error_msg = f"Connection failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                self.errors.append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Test setup failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return False
        
        finally:
            if self.sio and self.sio.connected:
                await self.sio.disconnect()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("WEBSOCKET CORS CONNECTION TEST RESULTS")
        print("="*60)
        print(f"Server URL: {self.server_url}")
        print(f"Origin URL: {self.origin_url}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("-"*60)
        
        if self.connection_successful:
            print("✅ STATUS: PASSED")
            print("🎉 WebSocket connection successful!")
            print("✨ CORS configuration is working correctly")
            print("🚀 Frontend should be able to connect to the backend")
        else:
            print("❌ STATUS: FAILED")
            print("💥 WebSocket connection failed")
            print("🔧 CORS configuration needs adjustment")
            
            if self.errors:
                print("\n🐛 ERRORS ENCOUNTERED:")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
            
            print("\n💡 TROUBLESHOOTING TIPS:")
            print("   1. Check that the server is running")
            print("   2. Verify CORS_ORIGINS includes the exact frontend URL")
            print("   3. Ensure ENVIRONMENT=production in server config")
            print("   4. Check server logs for CORS rejection messages")
        
        print("="*60)

async def main():
    """Run the CORS connection test"""
    # Test configuration
    SERVER_URL = "https://web-production-204e.up.railway.app"
    FRONTEND_URL = "https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app"
    
    print("🧪 Starting WebSocket CORS Connection Test")
    print("="*60)
    
    # Test the specific frontend URL that's having issues
    test = WebSocketCORSTest(SERVER_URL, FRONTEND_URL)
    success = await test.test_connection()
    test.print_results()
    
    # Also test a few other scenarios
    print("\n🔄 Testing additional scenarios...")
    
    # Test without origin header (should work for development)
    print("\n📝 Testing connection without origin header:")
    test_no_origin = WebSocketCORSTest(SERVER_URL, "")
    await test_no_origin.test_connection()
    
    # Test with a different origin (should fail)
    print("\n📝 Testing connection with unauthorized origin:")
    test_bad_origin = WebSocketCORSTest(SERVER_URL, "https://unauthorized-domain.com")
    await test_bad_origin.test_connection()
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        exit(1)