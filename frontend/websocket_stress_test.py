#!/usr/bin/env python3
"""
WebSocket Stress Test for United Voice Agent Server
Tests server stability under various load conditions.
"""

import asyncio
import socketio
import time
import json
import random
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import base64
import wave
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketStressTester:
    def __init__(self, server_url='http://localhost:8000'):
        self.server_url = server_url
        self.results = {
            'connections': {'successful': 0, 'failed': 0},
            'messages': {'sent': 0, 'received': 0, 'errors': 0},
            'reconnections': {'successful': 0, 'failed': 0},
            'latencies': [],
            'errors': []
        }
        self.active_clients = []
        self.lock = threading.Lock()

    def generate_test_audio(self, duration_ms=1000, sample_rate=16000):
        """Generate test audio data as base64 encoded WAV"""
        # Generate a simple sine wave
        frequency = 440  # A4 note
        duration_seconds = duration_ms / 1000.0
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
        
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        import io
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_data = wav_buffer.getvalue()
        return base64.b64encode(wav_data).decode('utf-8')

    async def create_client_session(self, client_id):
        """Create a single client session for testing"""
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        
        # Track events for this client
        messages_received = 0
        connection_time = None
        
        @sio.event
        async def connect():
            nonlocal connection_time
            connection_time = time.time()
            logger.info(f"Client {client_id} connected")
            with self.lock:
                self.results['connections']['successful'] += 1
        
        @sio.event
        async def disconnect():
            logger.info(f"Client {client_id} disconnected")
        
        @sio.event
        async def conversation_response(data):
            nonlocal messages_received
            messages_received += 1
            if connection_time:
                latency = (time.time() - connection_time) * 1000
                with self.lock:
                    self.results['latencies'].append(latency)
                    self.results['messages']['received'] += 1
        
        @sio.event
        async def error_occurred(data):
            logger.error(f"Client {client_id} received error: {data}")
            with self.lock:
                self.results['errors'].append(f"Client {client_id}: {data}")
        
        try:
            await sio.connect(self.server_url)
            return sio, messages_received
        except Exception as e:
            logger.error(f"Client {client_id} connection failed: {e}")
            with self.lock:
                self.results['connections']['failed'] += 1
                self.results['errors'].append(f"Connection failed for client {client_id}: {e}")
            return None, 0

    async def test_rapid_connections(self, num_clients=10):
        """Test rapid connection/disconnection"""
        logger.info(f"Testing rapid connections with {num_clients} clients...")
        
        tasks = []
        for i in range(num_clients):
            task = asyncio.create_task(self.create_and_disconnect_client(i))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)

    async def create_and_disconnect_client(self, client_id):
        """Create client, hold connection briefly, then disconnect"""
        try:
            result = await self.create_client_session(client_id)
            sio, _ = result
            
            if sio:
                # Hold connection for random time
                await asyncio.sleep(random.uniform(0.1, 1.0))
                await sio.disconnect()
                return True
        except Exception as e:
            logger.error(f"Client {client_id} test failed: {e}")
            with self.lock:
                self.results['errors'].append(f"Rapid connection test failed for client {client_id}: {e}")
        return False

    async def test_audio_streaming(self, num_messages=20):
        """Test sending multiple audio chunks in succession"""
        logger.info(f"Testing audio streaming with {num_messages} messages...")
        
        result = await self.create_client_session("audio_stream_test")
        sio, messages_received = result
        
        if not sio:
            return
        
        try:
            # Generate test audio
            audio_data = self.generate_test_audio()
            
            # Send multiple audio chunks rapidly
            for i in range(num_messages):
                start_time = time.time()
                
                await sio.emit('audio_chunk', {
                    'audio': audio_data,
                    'chunk_id': i
                })
                
                with self.lock:
                    self.results['messages']['sent'] += 1
                
                # Small delay between messages
                await asyncio.sleep(0.1)
            
            # Wait for responses
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Audio streaming test failed: {e}")
            with self.lock:
                self.results['errors'].append(f"Audio streaming test failed: {e}")
        finally:
            await sio.disconnect()

    async def test_reconnection(self, num_reconnects=5):
        """Test reconnection after disconnect"""
        logger.info(f"Testing reconnection {num_reconnects} times...")
        
        for i in range(num_reconnects):
            try:
                result = await self.create_client_session(f"reconnect_test_{i}")
                sio, _ = result
                
                if sio:
                    # Hold connection
                    await asyncio.sleep(1)
                    
                    # Disconnect
                    await sio.disconnect()
                    
                    # Wait before reconnecting
                    await asyncio.sleep(0.5)
                    
                    # Reconnect
                    await sio.connect(self.server_url)
                    
                    with self.lock:
                        self.results['reconnections']['successful'] += 1
                    
                    await sio.disconnect()
                    
                else:
                    with self.lock:
                        self.results['reconnections']['failed'] += 1
                        
            except Exception as e:
                logger.error(f"Reconnection test {i} failed: {e}")
                with self.lock:
                    self.results['reconnections']['failed'] += 1
                    self.results['errors'].append(f"Reconnection test {i} failed: {e}")

    async def test_concurrent_sessions(self, num_concurrent=5):
        """Test multiple concurrent active sessions"""
        logger.info(f"Testing {num_concurrent} concurrent sessions...")
        
        sessions = []
        tasks = []
        
        try:
            # Create concurrent sessions
            for i in range(num_concurrent):
                result = await self.create_client_session(f"concurrent_{i}")
                sio, _ = result
                if sio:
                    sessions.append(sio)
                    # Create a task to send periodic messages
                    task = asyncio.create_task(self.send_periodic_messages(sio, f"concurrent_{i}"))
                    tasks.append(task)
            
            # Let sessions run concurrently
            await asyncio.sleep(10)
            
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            # Disconnect all sessions
            for sio in sessions:
                try:
                    await sio.disconnect()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Concurrent sessions test failed: {e}")
            with self.lock:
                self.results['errors'].append(f"Concurrent sessions test failed: {e}")

    async def send_periodic_messages(self, sio, client_id):
        """Send periodic messages for a client"""
        try:
            audio_data = self.generate_test_audio()
            
            for i in range(5):  # Send 5 messages per session
                await sio.emit('audio_chunk', {
                    'audio': audio_data,
                    'chunk_id': f"{client_id}_{i}"
                })
                
                with self.lock:
                    self.results['messages']['sent'] += 1
                
                await asyncio.sleep(2)  # Wait 2 seconds between messages
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Periodic messages failed for {client_id}: {e}")

    async def run_all_tests(self):
        """Run all stress tests"""
        logger.info("Starting WebSocket stress tests...")
        start_time = time.time()
        
        try:
            # Test 1: Rapid connections
            await self.test_rapid_connections(15)
            await asyncio.sleep(2)
            
            # Test 2: Audio streaming
            await self.test_audio_streaming(10)
            await asyncio.sleep(2)
            
            # Test 3: Reconnection
            await self.test_reconnection(3)
            await asyncio.sleep(2)
            
            # Test 4: Concurrent sessions
            await self.test_concurrent_sessions(3)
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.results['errors'].append(f"Test suite failed: {e}")
        
        total_time = time.time() - start_time
        
        # Generate report
        self.generate_report(total_time)

    def generate_report(self, total_time):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("WEBSOCKET STRESS TEST REPORT")
        print("="*60)
        print(f"Total test time: {total_time:.2f} seconds")
        print()
        
        # Connection statistics
        total_connections = self.results['connections']['successful'] + self.results['connections']['failed']
        success_rate = (self.results['connections']['successful'] / max(total_connections, 1)) * 100
        print(f"CONNECTIONS:")
        print(f"  Successful: {self.results['connections']['successful']}")
        print(f"  Failed: {self.results['connections']['failed']}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print()
        
        # Message statistics
        print(f"MESSAGES:")
        print(f"  Sent: {self.results['messages']['sent']}")
        print(f"  Received: {self.results['messages']['received']}")
        print(f"  Errors: {self.results['messages']['errors']}")
        print()
        
        # Reconnection statistics
        total_reconnects = self.results['reconnections']['successful'] + self.results['reconnections']['failed']
        if total_reconnects > 0:
            reconnect_rate = (self.results['reconnections']['successful'] / total_reconnects) * 100
            print(f"RECONNECTIONS:")
            print(f"  Successful: {self.results['reconnections']['successful']}")
            print(f"  Failed: {self.results['reconnections']['failed']}")
            print(f"  Success Rate: {reconnect_rate:.1f}%")
            print()
        
        # Latency statistics
        if self.results['latencies']:
            latencies = self.results['latencies']
            print(f"LATENCY (ms):")
            print(f"  Average: {np.mean(latencies):.1f}")
            print(f"  Min: {min(latencies):.1f}")
            print(f"  Max: {max(latencies):.1f}")
            print(f"  Median: {np.median(latencies):.1f}")
            print()
        
        # Error summary
        if self.results['errors']:
            print(f"ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors']) - 10} more errors")
            print()
        
        # Overall assessment
        print("OVERALL ASSESSMENT:")
        if success_rate > 95 and len(self.results['errors']) < 5:
            print("  ✓ EXCELLENT - Server is highly stable")
        elif success_rate > 90 and len(self.results['errors']) < 10:
            print("  ✓ GOOD - Server is stable with minor issues")
        elif success_rate > 80:
            print("  ⚠ FAIR - Server has moderate stability issues")
        else:
            print("  ✗ POOR - Server has significant stability issues")
        
        print("="*60)

async def main():
    """Run the stress test suite"""
    tester = WebSocketStressTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())