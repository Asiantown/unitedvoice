#!/usr/bin/env python3
"""
Comprehensive end-to-end test for United Voice Agent
Tests the complete voice agent system including:
1. WebSocket connection
2. Audio recording simulation
3. Transcription 
4. Agent response
5. TTS generation
"""

import asyncio
import socketio
import base64
import json
import sys
import time
import aiofiles
import aiohttp
import numpy as np
import wave
import tempfile
import os
from pathlib import Path

class ComprehensiveVoiceAgentTest:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.test_results = {}
        self.session_id = None
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            print("✅ Connected to WebSocket server")
            self.test_results['websocket_connection'] = True
        
        @self.sio.event
        async def disconnect():
            print("❌ Disconnected from WebSocket server")
        
        @self.sio.event
        async def connected(data):
            self.session_id = data.get('session_id')
            print(f"📋 Server welcome: {data.get('message', 'N/A')}")
            print(f"📋 Session ID: {self.session_id}")
            self.test_results['session_initialization'] = True
        
        @self.sio.event
        async def agent_response(data):
            response_text = data.get('text', '')
            print(f"🤖 Agent Response: {response_text[:100]}...")
            
            # Check for audio
            if 'audio' in data:
                print(f"🔊 Audio received: {len(data['audio'])} bytes (base64)")
                self.test_results['tts_audio_received'] = True
            else:
                print("🔇 No audio in response")
                self.test_results['tts_audio_received'] = False
            
            self.test_results['agent_response'] = response_text
            self.test_results['agent_response_received'] = True
        
        @self.sio.event
        async def transcription(data):
            transcription_text = data.get('text', '')
            confidence = data.get('confidence', 0)
            print(f"📝 Transcription: '{transcription_text}' (confidence: {confidence:.2f})")
            self.test_results['transcription'] = transcription_text
            self.test_results['transcription_confidence'] = confidence
            self.test_results['transcription_received'] = True
        
        @self.sio.event
        async def status_update(data):
            status = data.get('status', 'unknown')
            message = data.get('message', '')
            print(f"📊 Status: {status} - {message}")
        
        @self.sio.event
        async def error(data):
            error_message = data.get('message', 'Unknown error')
            print(f"❌ Server Error: {error_message}")
            self.test_results['error'] = error_message
        
        @self.sio.event
        async def health_response(data):
            print(f"💚 Health: {data.get('status', 'N/A')}")
            print(f"📊 Active Sessions: {data.get('active_sessions', 'N/A')}")
            self.test_results['health_check'] = data
    
    def create_test_audio(self, text="I want to book a flight from San Francisco to New York", 
                         duration=3, sample_rate=16000):
        """Create a test WAV audio file with silence (simulates voice input)"""
        try:
            # Create silent audio (in real scenario, this would be actual voice)
            frames = int(duration * sample_rate)
            audio_data = np.zeros(frames, dtype=np.int16)
            
            # Add a bit of noise to simulate voice activity
            noise = np.random.normal(0, 100, frames).astype(np.int16)
            audio_data = audio_data + noise
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            with wave.open(temp_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Read file and encode as base64
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            print(f"📢 Created test audio: {len(audio_bytes)} bytes, {duration}s duration")
            
            return audio_base64, "wav"
            
        except Exception as e:
            print(f"❌ Failed to create test audio: {e}")
            return None, None
    
    async def test_http_endpoints(self):
        """Test HTTP API endpoints"""
        print("\n🌐 Testing HTTP API Endpoints...")
        print("="*50)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get('http://localhost:8000/health') as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health endpoint: {data['status']}")
                        services = data.get('services', {})
                        for service, status in services.items():
                            icon = "✅" if status == "available" else "❌"
                            print(f"  {icon} {service}: {status}")
                        self.test_results['http_health'] = data
                    else:
                        print(f"❌ Health endpoint failed: {response.status}")
                        return False
                
                # Test config endpoint
                async with session.get('http://localhost:8000/api/config') as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Config endpoint working")
                        audio_formats = data.get('audio', {}).get('supported_formats', [])
                        print(f"📋 Supported audio formats: {', '.join(audio_formats)}")
                        self.test_results['http_config'] = data
                    else:
                        print(f"❌ Config endpoint failed: {response.status}")
                        return False
                
                return True
                
        except Exception as e:
            print(f"❌ HTTP API test failed: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        print("\n🔌 Testing WebSocket Connection...")
        print("="*50)
        
        try:
            # Connect to server
            await self.sio.connect('http://localhost:8000')
            await asyncio.sleep(2)  # Wait for connection events
            
            # Send health check
            print("\n🔍 Sending health check...")
            await self.sio.emit('health_check')
            await asyncio.sleep(1)
            
            return self.test_results.get('websocket_connection', False)
            
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_audio_transcription_flow(self):
        """Test complete audio transcription and agent response flow"""
        print("\n🎤 Testing Audio Transcription Flow...")
        print("="*50)
        
        try:
            # Create test audio
            test_phrases = [
                "Hi, I want to book a flight from San Francisco to New York",
                "I need to travel next Friday",
                "I prefer morning flights"
            ]
            
            for i, phrase in enumerate(test_phrases, 1):
                print(f"\n--- Test {i}: '{phrase}' ---")
                
                # Create test audio for this phrase
                audio_base64, audio_format = self.create_test_audio(phrase)
                if not audio_base64:
                    print(f"❌ Failed to create audio for test {i}")
                    continue
                
                # Reset test flags
                self.test_results['transcription_received'] = False
                self.test_results['agent_response_received'] = False
                
                # Send audio data
                audio_data = {
                    'audio': audio_base64,
                    'format': audio_format,
                    'timestamp': time.time()
                }
                
                print(f"📤 Sending audio data ({len(audio_base64)} bytes)")
                await self.sio.emit('audio_data', audio_data)
                
                # Wait for transcription and response
                max_wait = 30  # Maximum wait time in seconds
                wait_time = 0
                
                while wait_time < max_wait:
                    await asyncio.sleep(1)
                    wait_time += 1
                    
                    # Check if we got both transcription and agent response
                    if (self.test_results.get('transcription_received') and 
                        self.test_results.get('agent_response_received')):
                        print(f"✅ Test {i} completed successfully!")
                        break
                    
                    if wait_time % 5 == 0:
                        print(f"⏳ Waiting... ({wait_time}s/{max_wait}s)")
                
                if wait_time >= max_wait:
                    print(f"⏰ Test {i} timed out after {max_wait}s")
                
                # Small delay between tests
                await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Audio transcription flow test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_conversation_state(self):
        """Test conversation state management"""
        print("\n📊 Testing Conversation State...")
        print("="*50)
        
        try:
            # Get session state
            await self.sio.emit('get_session_state')
            await asyncio.sleep(2)
            
            # Reset conversation
            await self.sio.emit('reset_conversation')
            await asyncio.sleep(2)
            
            print("✅ Conversation state tests completed")
            return True
            
        except Exception as e:
            print(f"❌ Conversation state test failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up connections"""
        if self.sio.connected:
            await self.sio.disconnect()
    
    def print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*60)
        
        # HTTP API Tests
        print("\n🌐 HTTP API Tests:")
        health_status = self.test_results.get('http_health', {}).get('status', 'unknown')
        print(f"  Health endpoint: {'✅' if health_status == 'healthy' else '❌'} {health_status}")
        
        services = self.test_results.get('http_health', {}).get('services', {})
        for service, status in services.items():
            icon = "✅" if status == "available" else "❌"
            print(f"  {service}: {icon} {status}")
        
        # WebSocket Tests
        print("\n🔌 WebSocket Tests:")
        ws_conn = self.test_results.get('websocket_connection', False)
        print(f"  Connection: {'✅' if ws_conn else '❌'}")
        
        session_init = self.test_results.get('session_initialization', False)
        print(f"  Session init: {'✅' if session_init else '❌'}")
        
        # Audio/Transcription Tests
        print("\n🎤 Audio Processing Tests:")
        transcription = self.test_results.get('transcription_received', False)
        print(f"  Transcription: {'✅' if transcription else '❌'}")
        
        if transcription:
            trans_text = self.test_results.get('transcription', 'N/A')
            confidence = self.test_results.get('transcription_confidence', 0)
            print(f"    Last transcription: '{trans_text}' (confidence: {confidence:.2f})")
        
        # Agent Response Tests
        print("\n🤖 Agent Response Tests:")
        agent_resp = self.test_results.get('agent_response_received', False)
        print(f"  Response received: {'✅' if agent_resp else '❌'}")
        
        if agent_resp:
            resp_text = self.test_results.get('agent_response', 'N/A')
            print(f"    Last response: '{resp_text[:100]}...'")
        
        # TTS Tests
        tts_audio = self.test_results.get('tts_audio_received', False)
        print(f"  TTS audio: {'✅' if tts_audio else '❌'}")
        
        # Error Report
        if 'error' in self.test_results:
            print(f"\n❌ Errors encountered:")
            print(f"  {self.test_results['error']}")
        
        # Overall Status
        critical_tests = [
            'websocket_connection',
            'session_initialization', 
            'transcription_received',
            'agent_response_received'
        ]
        
        passed_critical = sum(1 for test in critical_tests if self.test_results.get(test, False))
        
        print(f"\n🎯 OVERALL STATUS:")
        if passed_critical == len(critical_tests):
            print("✅ ALL CRITICAL TESTS PASSED - System is working perfectly!")
        else:
            print(f"⚠️  {passed_critical}/{len(critical_tests)} critical tests passed")
        
        # Recommendations
        print(f"\n📝 Next Steps:")
        if passed_critical == len(critical_tests):
            print("1. ✅ Backend is fully functional")
            print("2. 🚀 Start the frontend: cd frontend && npm start")
            print("3. 🌐 Open http://localhost:3000 in your browser")
            print("4. 🎙️  Test with real voice input")
        else:
            print("1. ❌ Fix backend issues before testing frontend")
            print("2. 📋 Check server logs for detailed error information")
            print("3. 🔧 Verify API keys in .env file")

async def main():
    """Main test function"""
    print("🚀 UNITED VOICE AGENT - COMPREHENSIVE END-TO-END TEST")
    print("="*60)
    
    tester = ComprehensiveVoiceAgentTest()
    
    try:
        # Test HTTP endpoints first
        http_success = await tester.test_http_endpoints()
        
        if not http_success:
            print("\n❌ HTTP API tests failed. Cannot continue with WebSocket tests.")
            return
        
        # Test WebSocket connection
        ws_success = await tester.test_websocket_connection()
        
        if not ws_success:
            print("\n❌ WebSocket connection failed. Cannot continue with audio tests.")
            return
        
        # Test audio transcription flow
        await tester.test_audio_transcription_flow()
        
        # Test conversation state
        await tester.test_conversation_state()
        
        # Wait a bit for any final responses
        await asyncio.sleep(3)
        
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await tester.cleanup()
        
        # Print comprehensive summary
        tester.print_test_summary()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)