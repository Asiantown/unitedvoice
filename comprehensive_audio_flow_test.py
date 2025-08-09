#!/usr/bin/env python3
"""
Comprehensive End-to-End Audio Flow Test
========================================

This script simulates the complete user flow from frontend to backend:
1. WebSocket connection establishment
2. Audio data transmission
3. Server processing verification
4. Response flow validation
"""

import asyncio
import websockets
import json
import base64
import time
import logging
import sys
from typing import Dict, Any, Optional
import wave
import io
import struct

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioFlowTester:
    def __init__(self, websocket_url: str = "ws://localhost:8000"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.test_results = []
        self.connection_confirmed = False
        self.audio_received = False
        self.response_received = False
        
    def log_test_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log a test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': time.time(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        if details:
            for key, value in details.items():
                logger.info(f"  {key}: {value}")

    def create_test_audio_data(self) -> str:
        """Create test audio data as base64 encoded WAV"""
        # Generate a simple 1-second sine wave at 440 Hz (A4 note)
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0
        
        # Generate samples
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            sample = int(32767 * 0.3 * (
                0.5 * (1 + math.cos(2 * 3.14159 * frequency * t))  # Soft sine wave
            ))
            samples.append(sample)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
        
        # Get the WAV data and encode to base64
        wav_data = wav_buffer.getvalue()
        base64_audio = base64.b64encode(wav_data).decode('utf-8')
        
        logger.info(f"Generated test audio: {len(wav_data)} bytes, {duration}s duration")
        return base64_audio

    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection establishment"""
        try:
            logger.info(f"🔌 Attempting WebSocket connection to {self.websocket_url}")
            
            # Connect with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.websocket_url),
                timeout=10.0
            )
            
            self.log_test_result(
                "WebSocket Connection",
                True,
                "Successfully established WebSocket connection",
                {"url": self.websocket_url, "state": str(self.websocket.state)}
            )
            return True
            
        except asyncio.TimeoutError:
            self.log_test_result(
                "WebSocket Connection",
                False,
                "Connection timeout after 10 seconds",
                {"url": self.websocket_url}
            )
            return False
        except Exception as e:
            self.log_test_result(
                "WebSocket Connection",
                False,
                f"Connection failed: {str(e)}",
                {"url": self.websocket_url, "error_type": type(e).__name__}
            )
            return False

    async def test_connection_confirmation(self) -> bool:
        """Test server connection confirmation"""
        if not self.websocket:
            self.log_test_result("Connection Confirmation", False, "No WebSocket connection")
            return False
            
        try:
            logger.info("📡 Waiting for server connection confirmation...")
            
            # Wait for connection confirmation message
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    logger.info(f"Received message: {data}")
                    
                    # Check for connection confirmation
                    if data.get('type') == 'connected' or 'connected' in str(data).lower():
                        self.connection_confirmed = True
                        self.log_test_result(
                            "Connection Confirmation",
                            True,
                            "Server confirmed connection",
                            {"message": data, "response_time": time.time() - start_time}
                        )
                        return True
                        
                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {message}")
                    continue
            
            self.log_test_result(
                "Connection Confirmation",
                False,
                f"No connection confirmation received within {timeout}s"
            )
            return False
            
        except Exception as e:
            self.log_test_result(
                "Connection Confirmation",
                False,
                f"Error waiting for confirmation: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False

    async def test_audio_transmission(self) -> bool:
        """Test sending audio data to server"""
        if not self.websocket:
            self.log_test_result("Audio Transmission", False, "No WebSocket connection")
            return False
            
        try:
            logger.info("🎵 Sending test audio data...")
            
            # Create test audio
            test_audio = self.create_test_audio_data()
            
            # Send audio data message
            audio_message = {
                'type': 'audio_data',
                'audio': test_audio,
                'format': 'wav',
                'timestamp': time.time(),
                'size': len(base64.b64decode(test_audio)),
                'test': True  # Mark as test data
            }
            
            await self.websocket.send(json.dumps(audio_message))
            
            self.log_test_result(
                "Audio Transmission",
                True,
                "Successfully sent audio data to server",
                {
                    "audio_size": len(base64.b64decode(test_audio)),
                    "format": "wav",
                    "timestamp": audio_message['timestamp']
                }
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Audio Transmission",
                False,
                f"Failed to send audio: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False

    async def test_server_processing(self) -> bool:
        """Test server processes audio and sends response"""
        if not self.websocket:
            self.log_test_result("Server Processing", False, "No WebSocket connection")
            return False
            
        try:
            logger.info("🔄 Waiting for server to process audio...")
            
            start_time = time.time()
            timeout = 30.0  # Give server time to process
            responses_received = []
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    responses_received.append(data)
                    
                    logger.info(f"Server response: {data.get('type', 'unknown')} - {str(data)[:100]}...")
                    
                    # Check for different types of responses
                    response_type = data.get('type', '')
                    
                    if response_type in ['transcription', 'agent_response', 'status_update']:
                        self.response_received = True
                        
                        # For transcription
                        if response_type == 'transcription':
                            self.log_test_result(
                                "Server Processing - Transcription",
                                True,
                                f"Received transcription: {data.get('text', 'N/A')}",
                                {"confidence": data.get('confidence'), "processing_time": time.time() - start_time}
                            )
                        
                        # For agent response
                        elif response_type == 'agent_response':
                            self.log_test_result(
                                "Server Processing - Agent Response",
                                True,
                                f"Received agent response: {data.get('text', 'N/A')[:50]}...",
                                {
                                    "has_audio": bool(data.get('audio')),
                                    "audio_format": data.get('audio_format'),
                                    "processing_time": time.time() - start_time
                                }
                            )
                            return True  # Success - got full response
                        
                        # For status updates
                        elif response_type == 'status_update':
                            self.log_test_result(
                                "Server Processing - Status Update",
                                True,
                                f"Status: {data.get('status', 'unknown')}",
                                {"status": data.get('status'), "processing_time": time.time() - start_time}
                            )
                    
                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Received non-JSON message: {message}")
                    continue
            
            # Analyze what we got
            if responses_received:
                self.log_test_result(
                    "Server Processing",
                    bool(self.response_received),
                    f"Received {len(responses_received)} responses, expected processing complete: {self.response_received}",
                    {"total_responses": len(responses_received), "response_types": [r.get('type') for r in responses_received]}
                )
                return self.response_received
            else:
                self.log_test_result(
                    "Server Processing",
                    False,
                    f"No server responses received within {timeout}s"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Server Processing",
                False,
                f"Error during server processing test: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False

    async def test_health_check(self) -> bool:
        """Test server health check"""
        if not self.websocket:
            self.log_test_result("Health Check", False, "No WebSocket connection")
            return False
            
        try:
            logger.info("🏥 Testing server health check...")
            
            # Send health check
            await self.websocket.send(json.dumps({'type': 'health_check'}))
            
            # Wait for response
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'health_check_response' or 'health' in str(data).lower():
                        self.log_test_result(
                            "Health Check",
                            True,
                            "Server health check passed",
                            {"response": data, "response_time": time.time() - start_time}
                        )
                        return True
                        
                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError:
                    continue
            
            self.log_test_result(
                "Health Check",
                False,
                f"No health check response within {timeout}s"
            )
            return False
            
        except Exception as e:
            self.log_test_result(
                "Health Check",
                False,
                f"Health check failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀 Starting comprehensive audio flow test...")
        
        test_start_time = time.time()
        
        try:
            # Test 1: WebSocket Connection
            if not await self.test_websocket_connection():
                return self.generate_test_report(test_start_time)
            
            # Test 2: Connection Confirmation
            await self.test_connection_confirmation()
            
            # Test 3: Health Check
            await self.test_health_check()
            
            # Test 4: Audio Transmission
            if not await self.test_audio_transmission():
                return self.generate_test_report(test_start_time)
            
            # Test 5: Server Processing
            await self.test_server_processing()
            
            return self.generate_test_report(test_start_time)
            
        except Exception as e:
            self.log_test_result(
                "Comprehensive Test",
                False,
                f"Test suite failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return self.generate_test_report(test_start_time)
        
        finally:
            # Clean up
            if self.websocket:
                await self.websocket.close()

    def generate_test_report(self, start_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_time = time.time() - start_time
        
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        report = {
            'summary': {
                'total_tests': len(self.test_results),
                'passed': len(passed_tests),
                'failed': len(failed_tests),
                'success_rate': len(passed_tests) / len(self.test_results) if self.test_results else 0,
                'total_time': total_time,
                'timestamp': time.time()
            },
            'connection_state': {
                'websocket_connected': bool(self.websocket and not self.websocket.closed),
                'connection_confirmed': self.connection_confirmed,
                'audio_received': self.audio_received,
                'response_received': self.response_received
            },
            'test_results': self.test_results,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests
        }
        
        return report

# Add missing import
import math

async def main():
    """Main test runner"""
    print("=" * 60)
    print("COMPREHENSIVE AUDIO FLOW TEST")
    print("=" * 60)
    
    # Test configuration
    websocket_url = "ws://localhost:8000"
    
    # Run tests
    tester = AudioFlowTester(websocket_url)
    report = await tester.run_comprehensive_test()
    
    # Print final report
    print("\n" + "=" * 60)
    print("FINAL TEST REPORT")
    print("=" * 60)
    
    summary = report['summary']
    print(f"📊 Tests Run: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1%}")
    print(f"⏱️  Total Time: {summary['total_time']:.2f}s")
    
    connection_state = report['connection_state']
    print(f"\n🔗 Connection States:")
    print(f"   WebSocket Connected: {connection_state['websocket_connected']}")
    print(f"   Connection Confirmed: {connection_state['connection_confirmed']}")
    print(f"   Audio Received by Server: {connection_state['audio_received']}")
    print(f"   Response Received: {connection_state['response_received']}")
    
    if report['failed_tests']:
        print(f"\n❌ Failed Tests:")
        for test in report['failed_tests']:
            print(f"   - {test['test']}: {test['message']}")
    
    print("\n" + "=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())