#!/usr/bin/env python3
"""
Python WebSocket Test Script for United Voice Agent
Tests WebSocket connection using both native WebSockets and Socket.IO
"""

import asyncio
import json
import base64
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import websockets
import socketio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
SERVER_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000"
TEST_TIMEOUT = 30


class WebSocketTester:
    """Comprehensive WebSocket testing class"""
    
    def __init__(self):
        self.test_results = []
        self.sio = None
        self.connected = False
        self.events_received = {}
        
    def log_result(self, test_name: str, status: str, message: str, data: Any = None):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'status': status,
            'message': message,
            'data': data
        }
        self.test_results.append(result)
        
        status_emoji = {
            'SUCCESS': '✅',
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        
        print(f"{status_emoji.get(status, '📝')} {test_name}: {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")

    async def test_socket_io_connection(self):
        """Test Socket.IO connection"""
        print("\n🔌 Testing Socket.IO Connection...")
        
        try:
            # Create Socket.IO client
            self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
            
            # Set up event handlers
            @self.sio.event
            async def connect():
                self.connected = True
                self.log_result("socket_io_connect", "SUCCESS", "Connected to Socket.IO server", {
                    'sid': self.sio.sid
                })
            
            @self.sio.event
            async def disconnect():
                self.connected = False
                self.log_result("socket_io_disconnect", "INFO", "Disconnected from Socket.IO server")
            
            @self.sio.event
            async def connected(data):
                self.events_received['connected'] = data
                self.log_result("connected_event", "SUCCESS", "Received 'connected' event", data)
            
            @self.sio.event
            async def agent_response(data):
                self.events_received['agent_response'] = data
                self.log_result("agent_response_event", "SUCCESS", "Received 'agent_response' event", {
                    'has_text': bool(data.get('text')),
                    'has_audio': bool(data.get('audio')),
                    'intent': data.get('intent'),
                    'text_preview': data.get('text', '')[:100] + '...' if data.get('text') else None
                })
            
            @self.sio.event
            async def transcription(data):
                self.events_received['transcription'] = data
                self.log_result("transcription_event", "SUCCESS", "Received 'transcription' event", data)
            
            @self.sio.event
            async def status_update(data):
                self.events_received['status_update'] = data
                self.log_result("status_update_event", "INFO", "Received 'status_update' event", data)
            
            @self.sio.event
            async def error(data):
                self.events_received['error'] = data
                self.log_result("error_event", "WARNING", "Received 'error' event", data)
            
            @self.sio.event
            async def health_response(data):
                self.events_received['health_response'] = data
                self.log_result("health_response_event", "SUCCESS", "Received 'health_response' event", data)
            
            @self.sio.event
            async def session_state(data):
                self.events_received['session_state'] = data
                self.log_result("session_state_event", "SUCCESS", "Received 'session_state' event", data)
            
            # Connect to server
            await asyncio.wait_for(self.sio.connect(SERVER_URL), timeout=10)
            
            # Wait for initial events
            await asyncio.sleep(2)
            
            return True
            
        except asyncio.TimeoutError:
            self.log_result("socket_io_connect", "ERROR", "Connection timeout after 10 seconds")
            return False
        except Exception as e:
            self.log_result("socket_io_connect", "ERROR", f"Connection failed: {str(e)}")
            return False

    async def test_event_handling(self):
        """Test event handling capabilities"""
        print("\n📡 Testing Event Handling...")
        
        if not self.connected:
            self.log_result("event_handling", "ERROR", "Not connected to server")
            return False
        
        try:
            # Test health check
            await self.sio.emit('health_check')
            await asyncio.sleep(1)
            
            # Test session state request
            await self.sio.emit('get_session_state')
            await asyncio.sleep(1)
            
            # Check which events we received
            expected_events = ['connected', 'agent_response']
            received_events = list(self.events_received.keys())
            
            self.log_result("event_handling", "SUCCESS", f"Events received: {received_events}")
            
            missing_events = set(expected_events) - set(received_events)
            if missing_events:
                self.log_result("event_handling", "WARNING", f"Missing expected events: {missing_events}")
            
            return True
            
        except Exception as e:
            self.log_result("event_handling", "ERROR", f"Event handling failed: {str(e)}")
            return False

    async def test_audio_data_exchange(self):
        """Test sending audio data"""
        print("\n🎵 Testing Audio Data Exchange...")
        
        if not self.connected:
            self.log_result("audio_exchange", "ERROR", "Not connected to server")
            return False
        
        try:
            # Create mock audio data
            mock_audio_bytes = b"mock audio data for testing"
            mock_audio_base64 = base64.b64encode(mock_audio_bytes).decode('utf-8')
            
            audio_data = {
                'audio': mock_audio_base64,
                'format': 'webm',
                'timestamp': datetime.now().isoformat()
            }
            
            # Send audio data
            await self.sio.emit('audio_data', audio_data)
            self.log_result("audio_send", "SUCCESS", "Sent mock audio data", {
                'format': audio_data['format'],
                'size_bytes': len(mock_audio_bytes)
            })
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Check if we got transcription or error
            if 'transcription' in self.events_received:
                self.log_result("audio_response", "SUCCESS", "Received transcription response")
            elif 'error' in self.events_received:
                error_data = self.events_received['error']
                self.log_result("audio_response", "WARNING", "Received error response (expected for mock data)", error_data)
            else:
                self.log_result("audio_response", "WARNING", "No response to audio data")
            
            return True
            
        except Exception as e:
            self.log_result("audio_exchange", "ERROR", f"Audio exchange failed: {str(e)}")
            return False

    async def test_error_conditions(self):
        """Test error handling"""
        print("\n⚠️ Testing Error Conditions...")
        
        if not self.connected:
            self.log_result("error_conditions", "ERROR", "Not connected to server")
            return False
        
        try:
            # Test invalid audio data
            invalid_audio_data = {
                'invalid_field': 'invalid_value',
                'format': 'unknown'
            }
            
            await self.sio.emit('audio_data', invalid_audio_data)
            await asyncio.sleep(2)
            
            # Check if error was handled properly
            if 'error' in self.events_received:
                self.log_result("error_handling", "SUCCESS", "Server properly handled invalid data")
            else:
                self.log_result("error_handling", "WARNING", "No error response for invalid data")
            
            return True
            
        except Exception as e:
            self.log_result("error_conditions", "ERROR", f"Error condition testing failed: {str(e)}")
            return False

    async def test_conversation_reset(self):
        """Test conversation reset functionality"""
        print("\n🔄 Testing Conversation Reset...")
        
        if not self.connected:
            self.log_result("conversation_reset", "ERROR", "Not connected to server")
            return False
        
        try:
            # Clear previous events
            self.events_received.clear()
            
            # Send reset command
            await self.sio.emit('reset_conversation')
            await asyncio.sleep(2)
            
            # Check if we received reset confirmation and new greeting
            if 'agent_response' in self.events_received:
                self.log_result("conversation_reset", "SUCCESS", "Received new greeting after reset")
            else:
                self.log_result("conversation_reset", "WARNING", "No greeting received after reset")
            
            return True
            
        except Exception as e:
            self.log_result("conversation_reset", "ERROR", f"Conversation reset failed: {str(e)}")
            return False

    async def test_native_websocket(self):
        """Test native WebSocket connection (fallback test)"""
        print("\n🔗 Testing Native WebSocket Connection...")
        
        try:
            # Try to connect using native WebSockets
            websocket_url = f"{WEBSOCKET_URL}/socket.io/?EIO=4&transport=websocket"
            
            async with websockets.connect(websocket_url, timeout=5) as websocket:
                self.log_result("native_websocket", "SUCCESS", "Native WebSocket connection successful")
                
                # Try to send a message
                await websocket.send("40") # Socket.IO connect message
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                self.log_result("native_websocket_message", "SUCCESS", "Received response via native WebSocket", {
                    'response': response
                })
                
                return True
                
        except Exception as e:
            self.log_result("native_websocket", "ERROR", f"Native WebSocket connection failed: {str(e)}")
            return False

    async def test_http_endpoints(self):
        """Test HTTP endpoints for WebSocket server health"""
        print("\n🌐 Testing HTTP Endpoints...")
        
        endpoints = [
            ('/health', 'Health check endpoint'),
            ('/api/config', 'Configuration endpoint'),
            ('/socket.io/', 'Socket.IO endpoint info')
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    url = f"{SERVER_URL}{endpoint}"
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.log_result("http_endpoint", "SUCCESS", f"{description} - Status {response.status}", {
                                'endpoint': endpoint,
                                'data': data
                            })
                        else:
                            self.log_result("http_endpoint", "WARNING", f"{description} - Status {response.status}")
                            
                except Exception as e:
                    self.log_result("http_endpoint", "ERROR", f"{description} failed: {str(e)}")

    async def cleanup(self):
        """Clean up connections"""
        if self.sio and self.connected:
            await self.sio.disconnect()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 PYTHON WEBSOCKET TEST REPORT")
        print("=" * 60)
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['status'] == 'SUCCESS'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARNING'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Errors: {error_tests} ❌")
        print(f"Warnings: {warning_tests} ⚠️")
        
        # Connection summary
        connection_successful = any(r['test_name'] == 'socket_io_connect' and r['status'] == 'SUCCESS' 
                                  for r in self.test_results)
        events_received = len(self.events_received)
        
        print(f"\nConnection Status: {'CONNECTED ✅' if connection_successful else 'FAILED ❌'}")
        print(f"Events Received: {events_received}")
        print(f"Event Types: {list(self.events_received.keys())}")
        
        # Save detailed report
        report_path = '/Users/ryanyin/united-voice-agent/websocket_test_python_results.json'
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'error_tests': error_tests,
                'warning_tests': warning_tests,
                'connection_successful': connection_successful,
                'events_received': events_received,
                'event_types': list(self.events_received.keys())
            },
            'events_received': self.events_received,
            'detailed_results': self.test_results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Overall assessment
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        overall_success = connection_successful and error_tests == 0 and success_rate > 0.7
        
        print(f"\n🎯 Overall Assessment: {'PASS ✅' if overall_success else 'NEEDS ATTENTION ⚠️'}")
        print(f"Success Rate: {success_rate:.1%}")
        
        if not overall_success:
            print("\n🔧 Issues to investigate:")
            if not connection_successful:
                print("  • WebSocket connection failed")
            if error_tests > 0:
                print(f"  • {error_tests} tests reported errors")
            if success_rate <= 0.7:
                print(f"  • Low success rate ({success_rate:.1%})")

    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting Python WebSocket Test Suite...")
        print("=" * 60)
        
        try:
            # Test 1: Socket.IO Connection
            await self.test_socket_io_connection()
            
            if self.connected:
                # Test 2: Event Handling
                await self.test_event_handling()
                
                # Test 3: Audio Data Exchange
                await self.test_audio_data_exchange()
                
                # Test 4: Error Conditions
                await self.test_error_conditions()
                
                # Test 5: Conversation Reset
                await self.test_conversation_reset()
            
            # Test 6: HTTP Endpoints
            await self.test_http_endpoints()
            
            # Test 7: Native WebSocket (fallback)
            await self.test_native_websocket()
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
        finally:
            await self.cleanup()
            self.generate_report()


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['websockets', 'socketio', 'aiohttp']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)} python-socketio[asyncio_client]")
        return False
    
    return True


if __name__ == "__main__":
    if not check_dependencies():
        exit(1)
    
    tester = WebSocketTester()
    asyncio.run(tester.run_all_tests())