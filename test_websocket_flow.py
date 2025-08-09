#!/usr/bin/env python3
"""
Comprehensive WebSocket Flow Test
Tests the complete conversation flow to ensure fixes are working properly
"""

import asyncio
import json
import base64
import logging
import time
import socketio
from datetime import datetime
from typing import Dict, Any, List
import wave
import numpy as np
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketFlowTester:
    """Comprehensive WebSocket flow tester"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000"):
        self.server_url = server_url
        self.sio = None
        self.connected = False
        self.messages_received: List[Dict[str, Any]] = []
        self.errors_received: List[Dict[str, Any]] = []
        self.status_updates: List[Dict[str, Any]] = []
        self.test_results: Dict[str, Any] = {}
        
    def create_test_audio(self, duration: float = 2.0, sample_rate: int = 16000) -> bytes:
        """Create a test audio file with a simple sine wave"""
        # Generate a sine wave (440 Hz - A4 note)
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_signal = np.sin(2 * np.pi * 440 * t) * 0.5
        
        # Convert to 16-bit PCM
        audio_signal = (audio_signal * 32767).astype(np.int16)
        
        # Create WAV file in memory
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_signal.tobytes())
            
            # Read the file content
            temp_file.seek(0)
            with open(temp_file.name, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_file.name)
            
        return audio_data
    
    async def setup_client(self):
        """Setup Socket.IO client with event handlers"""
        self.sio = socketio.AsyncClient()
        
        @self.sio.event
        async def connect():
            logger.info("✅ Connected to WebSocket server")
            self.connected = True
        
        @self.sio.event
        async def disconnect():
            logger.info("❌ Disconnected from WebSocket server")
            self.connected = False
        
        @self.sio.event
        async def connected(data):
            logger.info(f"🔗 Connection confirmed: {data}")
            self.messages_received.append({
                'type': 'connected',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.sio.event
        async def transcription(data):
            logger.info(f"📝 Transcription received: {data}")
            self.messages_received.append({
                'type': 'transcription',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.sio.event
        async def agent_response(data):
            logger.info(f"🤖 Agent response received: {data.get('text', '')[:100]}...")
            self.messages_received.append({
                'type': 'agent_response',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.sio.event
        async def status_update(data):
            logger.info(f"📊 Status update: {data}")
            self.status_updates.append({
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.sio.event
        async def error(data):
            logger.error(f"❌ Error received: {data}")
            self.errors_received.append({
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.sio.event
        async def health_response(data):
            logger.info(f"🏥 Health response: {data}")
            self.messages_received.append({
                'type': 'health_response',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def connect_to_server(self) -> bool:
        """Connect to the WebSocket server"""
        try:
            await self.sio.connect(self.server_url)
            
            # Wait for connection confirmation
            await asyncio.sleep(2)
            
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test 1: Basic connection without auto-greeting"""
        logger.info("🧪 Test 1: Testing basic connection (no auto-greeting)")
        
        start_time = time.time()
        
        # Clear previous messages
        self.messages_received.clear()
        self.errors_received.clear()
        
        # Connect
        connected = await self.connect_to_server()
        
        if not connected:
            return {
                'test': 'connection',
                'status': 'FAILED',
                'reason': 'Could not connect to server',
                'duration': time.time() - start_time
            }
        
        # Wait for any automatic messages
        await asyncio.sleep(3)
        
        # Check if we received any automatic greetings
        auto_greetings = [msg for msg in self.messages_received if msg['type'] == 'agent_response']
        
        result = {
            'test': 'connection',
            'status': 'PASSED' if len(auto_greetings) == 0 else 'FAILED',
            'reason': 'No automatic greeting sent' if len(auto_greetings) == 0 else f'Received {len(auto_greetings)} automatic greeting(s)',
            'duration': time.time() - start_time,
            'connected': connected,
            'messages_received': len(self.messages_received),
            'auto_greetings': len(auto_greetings)
        }
        
        logger.info(f"✅ Connection test result: {result['status']} - {result['reason']}")
        return result
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test 2: Health check endpoint"""
        logger.info("🧪 Test 2: Testing health check")
        
        start_time = time.time()
        
        # Clear previous messages
        health_responses = []
        
        # Send health check
        await self.sio.emit('health_check')
        
        # Wait for response
        await asyncio.sleep(2)
        
        # Find health responses
        health_responses = [msg for msg in self.messages_received if msg['type'] == 'health_response']
        
        result = {
            'test': 'health_check',
            'status': 'PASSED' if len(health_responses) > 0 else 'FAILED',
            'reason': 'Health check responded' if len(health_responses) > 0 else 'No health check response',
            'duration': time.time() - start_time,
            'responses': len(health_responses)
        }
        
        if health_responses:
            result['health_data'] = health_responses[0]['data']
        
        logger.info(f"✅ Health check test result: {result['status']} - {result['reason']}")
        return result
    
    async def test_user_initiated_conversation(self) -> Dict[str, Any]:
        """Test 3: User-initiated conversation flow"""
        logger.info("🧪 Test 3: Testing user-initiated conversation")
        
        start_time = time.time()
        
        # Clear previous messages
        initial_count = len(self.messages_received)
        
        # Create test audio data
        audio_data = self.create_test_audio(duration=2.0)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Send audio data (simulating user saying "Hello")
        await self.sio.emit('audio_data', {
            'audio': audio_base64,
            'format': 'wav',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info("🎤 Sent test audio data")
        
        # Wait for processing
        await asyncio.sleep(10)  # Give enough time for transcription and response
        
        # Analyze responses
        new_messages = self.messages_received[initial_count:]
        transcriptions = [msg for msg in new_messages if msg['type'] == 'transcription']
        agent_responses = [msg for msg in new_messages if msg['type'] == 'agent_response']
        
        # Check for duplicates
        duplicate_transcriptions = len(transcriptions) > 1
        duplicate_responses = len(agent_responses) > 1
        
        result = {
            'test': 'user_conversation',
            'status': 'PASSED',
            'reason': 'Conversation flow completed',
            'duration': time.time() - start_time,
            'transcriptions_received': len(transcriptions),
            'agent_responses_received': len(agent_responses),
            'duplicate_transcriptions': duplicate_transcriptions,
            'duplicate_responses': duplicate_responses,
            'status_updates_received': len(self.status_updates),
            'errors_received': len(self.errors_received)
        }
        
        # Update status based on issues found
        issues = []
        if duplicate_transcriptions:
            issues.append(f"Duplicate transcriptions ({len(transcriptions)})")
        if duplicate_responses:
            issues.append(f"Duplicate responses ({len(agent_responses)})")
        if len(self.errors_received) > 0:
            issues.append(f"Errors received ({len(self.errors_received)})")
        
        if issues:
            result['status'] = 'FAILED' if len(issues) > 1 else 'WARNING'
            result['reason'] = f"Issues found: {', '.join(issues)}"
        
        # Add sample data for debugging
        if transcriptions:
            result['sample_transcription'] = transcriptions[0]['data']
        if agent_responses:
            result['sample_response'] = {
                'text': agent_responses[0]['data'].get('text', '')[:100],
                'has_audio': 'audio' in agent_responses[0]['data']
            }
        
        logger.info(f"✅ Conversation test result: {result['status']} - {result['reason']}")
        return result
    
    async def test_duplicate_prevention(self) -> Dict[str, Any]:
        """Test 4: Duplicate message prevention"""
        logger.info("🧪 Test 4: Testing duplicate prevention")
        
        start_time = time.time()
        initial_count = len(self.messages_received)
        
        # Create test audio data
        audio_data = self.create_test_audio(duration=1.5)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Send the same audio data multiple times quickly
        for i in range(3):
            await self.sio.emit('audio_data', {
                'audio': audio_base64,
                'format': 'wav',
                'timestamp': datetime.utcnow().isoformat()
            })
            await asyncio.sleep(0.5)  # Short delay between sends
        
        logger.info("🎤 Sent duplicate test audio data")
        
        # Wait for processing
        await asyncio.sleep(8)
        
        # Analyze responses for duplicates
        new_messages = self.messages_received[initial_count:]
        transcriptions = [msg for msg in new_messages if msg['type'] == 'transcription']
        agent_responses = [msg for msg in new_messages if msg['type'] == 'agent_response']
        
        result = {
            'test': 'duplicate_prevention',
            'duration': time.time() - start_time,
            'transcriptions_received': len(transcriptions),
            'agent_responses_received': len(agent_responses),
            'audio_sends': 3
        }
        
        # Ideal scenario: duplicate prevention should limit responses
        if len(transcriptions) <= 1 and len(agent_responses) <= 1:
            result['status'] = 'PASSED'
            result['reason'] = 'Duplicate prevention working correctly'
        elif len(transcriptions) <= 2 and len(agent_responses) <= 2:
            result['status'] = 'WARNING'
            result['reason'] = 'Some duplicates may have passed through'
        else:
            result['status'] = 'FAILED'
            result['reason'] = f'Too many responses for duplicate input (T:{len(transcriptions)}, R:{len(agent_responses)})'
        
        logger.info(f"✅ Duplicate prevention test result: {result['status']} - {result['reason']}")
        return result
    
    async def disconnect_from_server(self):
        """Disconnect from the server"""
        if self.sio and self.connected:
            await self.sio.disconnect()
            logger.info("🔌 Disconnected from server")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting WebSocket Flow Tests")
        
        overall_start = time.time()
        
        await self.setup_client()
        
        # Test 1: Connection (no auto-greeting)
        test1_result = await self.test_connection()
        
        if test1_result['status'] == 'FAILED':
            return {
                'overall_status': 'FAILED',
                'overall_reason': 'Could not establish connection',
                'tests': [test1_result],
                'duration': time.time() - overall_start
            }
        
        # Test 2: Health check
        test2_result = await self.test_health_check()
        
        # Test 3: User conversation
        test3_result = await self.test_user_initiated_conversation()
        
        # Test 4: Duplicate prevention
        test4_result = await self.test_duplicate_prevention()
        
        await self.disconnect_from_server()
        
        # Compile overall results
        all_tests = [test1_result, test2_result, test3_result, test4_result]
        
        failed_tests = [t for t in all_tests if t['status'] == 'FAILED']
        warning_tests = [t for t in all_tests if t['status'] == 'WARNING']
        
        overall_status = 'PASSED'
        overall_reason = 'All tests passed'
        
        if failed_tests:
            overall_status = 'FAILED'
            overall_reason = f'{len(failed_tests)} test(s) failed'
        elif warning_tests:
            overall_status = 'WARNING'
            overall_reason = f'{len(warning_tests)} test(s) have warnings'
        
        return {
            'overall_status': overall_status,
            'overall_reason': overall_reason,
            'tests': all_tests,
            'total_messages_received': len(self.messages_received),
            'total_errors_received': len(self.errors_received),
            'total_status_updates': len(self.status_updates),
            'duration': time.time() - overall_start,
            'test_summary': {
                'passed': len([t for t in all_tests if t['status'] == 'PASSED']),
                'warnings': len(warning_tests),
                'failed': len(failed_tests),
                'total': len(all_tests)
            }
        }


async def main():
    """Main function to run the tests"""
    print("🧪 United Voice Agent - WebSocket Flow Test")
    print("=" * 50)
    
    # Create tester instance
    tester = WebSocketFlowTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print results
        print(f"\n📊 Overall Status: {results['overall_status']}")
        print(f"🔍 Reason: {results['overall_reason']}")
        print(f"⏱️  Total Duration: {results['duration']:.2f}s")
        print(f"📈 Test Summary: {results['test_summary']['passed']}/{results['test_summary']['total']} passed")
        
        if results['test_summary']['warnings'] > 0:
            print(f"⚠️  Warnings: {results['test_summary']['warnings']}")
        if results['test_summary']['failed'] > 0:
            print(f"❌ Failed: {results['test_summary']['failed']}")
        
        print(f"\n📝 Total Messages: {results['total_messages_received']}")
        print(f"❌ Total Errors: {results['total_errors_received']}")
        print(f"📊 Status Updates: {results['total_status_updates']}")
        
        print("\n" + "=" * 50)
        print("📋 DETAILED TEST RESULTS")
        print("=" * 50)
        
        for i, test in enumerate(results['tests'], 1):
            print(f"\n{i}. {test['test'].upper()}")
            print(f"   Status: {test['status']}")
            print(f"   Duration: {test['duration']:.2f}s")
            print(f"   Reason: {test['reason']}")
            
            # Add specific details for each test
            if test['test'] == 'connection':
                print(f"   Connected: {test['connected']}")
                print(f"   Auto-greetings: {test['auto_greetings']}")
            elif test['test'] == 'health_check':
                print(f"   Responses: {test['responses']}")
                if 'health_data' in test:
                    print(f"   Active Sessions: {test['health_data'].get('active_sessions', 'N/A')}")
            elif test['test'] == 'user_conversation':
                print(f"   Transcriptions: {test['transcriptions_received']}")
                print(f"   Agent Responses: {test['agent_responses_received']}")
                print(f"   Duplicate Trans: {test['duplicate_transcriptions']}")
                print(f"   Duplicate Resp: {test['duplicate_responses']}")
                if 'sample_response' in test:
                    print(f"   Has Audio: {test['sample_response']['has_audio']}")
            elif test['test'] == 'duplicate_prevention':
                print(f"   Audio Sends: {test['audio_sends']}")
                print(f"   Transcriptions: {test['transcriptions_received']}")
                print(f"   Responses: {test['agent_responses_received']}")
        
        # Save results to file
        results_file = f"/Users/ryanyin/united-voice-agent/websocket_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return results['overall_status'] == 'PASSED'
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return False


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import socketio
        import numpy as np
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install with: pip install python-socketio numpy")
        exit(1)
    
    # Run tests
    success = asyncio.run(main())
    exit(0 if success else 1)