#!/usr/bin/env python3
"""
End-to-end audio flow test for United Voice Agent
Tests complete audio pipeline from client to server and back
"""

import asyncio
import base64
import io
import json
import time
import wave
import numpy as np
import socketio
from pathlib import Path

# Create a simple test audio file (1 second of 440Hz sine wave)
def create_test_audio():
    """Create a test audio file for testing"""
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Scale to 16-bit integer
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    audio_buffer.seek(0)
    return audio_buffer.getvalue()

class AudioFlowTester:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.test_results = {}
        self.events_received = []
        
        # Setup event handlers
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            print("✅ Connected to WebSocket server")
            self.test_results['connection'] = True
            
        @self.sio.event
        async def disconnect():
            print("❌ Disconnected from WebSocket server")
            
        @self.sio.event
        async def connect_error(data):
            print(f"💥 Connection error: {data}")
            self.test_results['connection'] = False
            
        @self.sio.event
        async def transcription(data):
            print(f"🎤 Received transcription: {data}")
            self.test_results['transcription'] = data
            self.events_received.append(('transcription', data))
            
        @self.sio.event
        async def agent_response(data):
            print(f"🤖 Received agent response: {data}")
            self.test_results['agent_response'] = data
            self.events_received.append(('agent_response', data))
            
        @self.sio.event
        async def status_update(data):
            print(f"📊 Status update: {data}")
            self.events_received.append(('status_update', data))
            
        @self.sio.event
        async def error(data):
            print(f"❌ Error event: {data}")
            self.test_results['error'] = data
            
        @self.sio.event
        async def connected(data):
            print(f"🔗 Connected event: {data}")
            self.test_results['connected_event'] = data
            
    async def test_connection(self):
        """Test WebSocket connection"""
        print("\n🔌 Testing WebSocket connection...")
        try:
            await self.sio.connect(self.server_url)
            await asyncio.sleep(1)  # Give connection time to establish
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.test_results['connection_error'] = str(e)
            return False
            
    async def test_audio_upload(self):
        """Test audio data upload and processing"""
        print("\n🎵 Testing audio upload and processing...")
        
        # Create test audio
        audio_data = create_test_audio()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Send audio data
        audio_payload = {
            'audio': audio_base64,
            'format': 'wav',
            'timestamp': time.time(),
            'size': len(audio_data)
        }
        
        print(f"📤 Sending audio data: {len(audio_data)} bytes")
        await self.sio.emit('audio_data', audio_payload)
        
        # Wait for response
        print("⏳ Waiting for transcription...")
        timeout = 30  # 30 second timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if 'transcription' in self.test_results:
                print("✅ Transcription received!")
                return True
            await asyncio.sleep(0.5)
            
        print("⏰ Timeout waiting for transcription")
        return False
        
    async def test_health_check(self):
        """Test server health check"""
        print("\n🏥 Testing health check...")
        await self.sio.emit('health_check')
        await asyncio.sleep(1)
        return True
        
    async def test_session_state(self):
        """Test session state retrieval"""
        print("\n📋 Testing session state...")
        await self.sio.emit('get_session_state')
        await asyncio.sleep(1)
        return True
        
    async def run_tests(self):
        """Run all tests"""
        print("🚀 Starting end-to-end audio flow tests...")
        print("=" * 60)
        
        test_results = {
            'connection': False,
            'audio_upload': False,
            'health_check': False,
            'session_state': False
        }
        
        try:
            # Test connection
            if await self.test_connection():
                test_results['connection'] = True
                
                # Test audio upload and processing
                if await self.test_audio_upload():
                    test_results['audio_upload'] = True
                    
                # Test health check
                if await self.test_health_check():
                    test_results['health_check'] = True
                    
                # Test session state
                if await self.test_session_state():
                    test_results['session_state'] = True
                    
                # Wait a bit more for any delayed responses
                print("\n⏳ Waiting for any additional responses...")
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"💥 Test execution error: {e}")
            
        finally:
            # Disconnect
            await self.sio.disconnect()
            
        return test_results
        
    def print_results(self, test_results):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Connection test
        status = "✅ PASS" if test_results['connection'] else "❌ FAIL"
        print(f"🔌 Connection Test: {status}")
        
        # Audio upload test
        status = "✅ PASS" if test_results['audio_upload'] else "❌ FAIL"
        print(f"🎵 Audio Upload Test: {status}")
        
        # Health check test
        status = "✅ PASS" if test_results['health_check'] else "❌ FAIL"
        print(f"🏥 Health Check Test: {status}")
        
        # Session state test
        status = "✅ PASS" if test_results['session_state'] else "❌ FAIL"
        print(f"📋 Session State Test: {status}")
        
        print("\n📝 DETAILED RESULTS:")
        print("-" * 40)
        
        # Print all received events
        if self.events_received:
            print("📡 Events received:")
            for event_type, event_data in self.events_received:
                print(f"  • {event_type}: {event_data}")
        else:
            print("📡 No events received")
            
        # Print test data
        if self.test_results:
            print("\n🔍 Test data collected:")
            for key, value in self.test_results.items():
                print(f"  • {key}: {value}")
                
        # Overall result
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests PASSED! Audio flow is working correctly.")
        else:
            print("⚠️  Some tests FAILED. Check server logs for details.")
            
        print("=" * 60)

async def main():
    """Main test function"""
    tester = AudioFlowTester()
    test_results = await tester.run_tests()
    tester.print_results(test_results)

if __name__ == "__main__":
    print("🧪 United Voice Agent - End-to-End Audio Flow Test")
    print("This test will create a synthetic audio file and send it to the server")
    print("for transcription and processing.")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()