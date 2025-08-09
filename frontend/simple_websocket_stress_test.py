#!/usr/bin/env python3
"""
Simple WebSocket Stress Test for United Voice Agent Server
Tests basic connection and event handling with the actual server implementation.
"""

import asyncio
import socketio
import time
import json
import base64
import logging
import random
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleStressTester:
    def __init__(self, server_url='http://localhost:8000'):
        self.server_url = server_url
        self.results = {
            'connections': {'successful': 0, 'failed': 0},
            'events': {'sent': 0, 'received': 0, 'errors': 0},
            'errors': []
        }
        self.lock = threading.Lock()

    async def test_single_connection(self, client_id):
        """Test a single client connection"""
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        events_received = 0
        
        # Event handlers
        @sio.event
        async def connect():
            logger.info(f"Client {client_id} connected successfully")
            with self.lock:
                self.results['connections']['successful'] += 1
        
        @sio.event
        async def disconnect():
            logger.info(f"Client {client_id} disconnected")
        
        @sio.event
        async def connected(data):
            nonlocal events_received
            events_received += 1
            logger.info(f"Client {client_id} received connected event: {data}")
            with self.lock:
                self.results['events']['received'] += 1
        
        @sio.event
        async def agent_response(data):
            nonlocal events_received
            events_received += 1
            logger.info(f"Client {client_id} received agent_response")
            with self.lock:
                self.results['events']['received'] += 1
        
        @sio.event
        async def status_update(data):
            nonlocal events_received
            events_received += 1
            logger.info(f"Client {client_id} received status_update: {data}")
            with self.lock:
                self.results['events']['received'] += 1
        
        @sio.event
        async def error(data):
            logger.error(f"Client {client_id} received error: {data}")
            with self.lock:
                self.results['events']['errors'] += 1
        
        try:
            # Connect to server
            await sio.connect(self.server_url)
            
            # Wait for initial events
            await asyncio.sleep(2)
            
            # Test health check event
            await sio.emit('health_check')
            with self.lock:
                self.results['events']['sent'] += 1
            
            # Wait for response
            await asyncio.sleep(1)
            
            # Test session state request
            await sio.emit('get_session_state')
            with self.lock:
                self.results['events']['sent'] += 1
            
            # Wait for response
            await asyncio.sleep(1)
            
            # Disconnect
            await sio.disconnect()
            
            return events_received
            
        except Exception as e:
            logger.error(f"Client {client_id} connection failed: {e}")
            with self.lock:
                self.results['connections']['failed'] += 1
                self.results['errors'].append(f"Client {client_id}: {e}")
            return 0

    async def test_rapid_connections(self, num_clients=10):
        """Test rapid connection/disconnection"""
        logger.info(f"Testing {num_clients} rapid connections...")
        
        tasks = []
        for i in range(num_clients):
            task = asyncio.create_task(self.test_single_connection(f"rapid_{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        successful_events = [r for r in results if isinstance(r, int) and r > 0]
        logger.info(f"Rapid connections test completed. {len(successful_events)} clients received events")

    async def test_concurrent_connections(self, num_concurrent=5, duration=10):
        """Test multiple concurrent connections"""
        logger.info(f"Testing {num_concurrent} concurrent connections for {duration} seconds...")
        
        sessions = []
        try:
            # Create concurrent sessions
            for i in range(num_concurrent):
                sio = socketio.AsyncClient(logger=False, engineio_logger=False)
                
                @sio.event
                async def connect():
                    with self.lock:
                        self.results['connections']['successful'] += 1
                
                @sio.event
                async def connected(data):
                    with self.lock:
                        self.results['events']['received'] += 1
                
                @sio.event
                async def agent_response(data):
                    with self.lock:
                        self.results['events']['received'] += 1
                
                try:
                    await sio.connect(self.server_url)
                    sessions.append(sio)
                    logger.info(f"Concurrent client {i} connected")
                except Exception as e:
                    logger.error(f"Concurrent client {i} failed to connect: {e}")
                    with self.lock:
                        self.results['connections']['failed'] += 1
            
            # Let sessions run
            logger.info(f"Running {len(sessions)} concurrent sessions for {duration} seconds...")
            
            # Send periodic events
            for _ in range(duration):
                for j, sio in enumerate(sessions):
                    try:
                        await sio.emit('health_check')
                        with self.lock:
                            self.results['events']['sent'] += 1
                    except Exception as e:
                        logger.error(f"Failed to send event to concurrent client {j}: {e}")
                
                await asyncio.sleep(1)
            
        finally:
            # Disconnect all sessions
            for i, sio in enumerate(sessions):
                try:
                    await sio.disconnect()
                    logger.info(f"Concurrent client {i} disconnected")
                except Exception as e:
                    logger.error(f"Failed to disconnect concurrent client {i}: {e}")

    async def test_reconnection(self, num_tests=3):
        """Test reconnection after disconnect"""
        logger.info(f"Testing reconnection {num_tests} times...")
        
        for i in range(num_tests):
            sio = socketio.AsyncClient(logger=False, engineio_logger=False)
            
            @sio.event
            async def connect():
                logger.info(f"Reconnection test {i} - connected")
                with self.lock:
                    self.results['connections']['successful'] += 1
            
            @sio.event
            async def connected(data):
                with self.lock:
                    self.results['events']['received'] += 1
            
            try:
                # Initial connection
                await sio.connect(self.server_url)
                await asyncio.sleep(1)
                
                # Disconnect
                await sio.disconnect()
                await asyncio.sleep(1)
                
                # Reconnect
                await sio.connect(self.server_url)
                await asyncio.sleep(1)
                
                # Final disconnect
                await sio.disconnect()
                
                logger.info(f"Reconnection test {i} completed successfully")
                
            except Exception as e:
                logger.error(f"Reconnection test {i} failed: {e}")
                with self.lock:
                    self.results['connections']['failed'] += 1
                    self.results['errors'].append(f"Reconnection test {i}: {e}")

    async def run_all_tests(self):
        """Run all stress tests"""
        logger.info("Starting simple WebSocket stress tests...")
        start_time = time.time()
        
        try:
            # Test 1: Rapid connections
            await self.test_rapid_connections(8)
            await asyncio.sleep(1)
            
            # Test 2: Concurrent connections
            await self.test_concurrent_connections(3, 5)
            await asyncio.sleep(1)
            
            # Test 3: Reconnection
            await self.test_reconnection(2)
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.results['errors'].append(f"Test suite failed: {e}")
        
        total_time = time.time() - start_time
        self.generate_report(total_time)

    def generate_report(self, total_time):
        """Generate test report"""
        print("\n" + "="*60)
        print("SIMPLE WEBSOCKET STRESS TEST REPORT")
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
        
        # Event statistics
        print(f"EVENTS:")
        print(f"  Sent: {self.results['events']['sent']}")
        print(f"  Received: {self.results['events']['received']}")
        print(f"  Errors: {self.results['events']['errors']}")
        print()
        
        # Error summary
        if self.results['errors']:
            print(f"ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... and {len(self.results['errors']) - 5} more errors")
            print()
        
        # Overall assessment
        print("OVERALL ASSESSMENT:")
        if success_rate > 95 and len(self.results['errors']) < 2:
            print("  ✓ EXCELLENT - Server is highly stable")
        elif success_rate > 90 and len(self.results['errors']) < 5:
            print("  ✓ GOOD - Server is stable with minor issues")
        elif success_rate > 80:
            print("  ⚠ FAIR - Server has moderate stability issues")
        else:
            print("  ✗ POOR - Server has significant stability issues")
        
        print("="*60)

async def main():
    """Run the simple stress test suite"""
    tester = SimpleStressTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())