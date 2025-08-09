#!/usr/bin/env python3
"""
HTTP-based stress test for the United Voice Agent Server
Tests HTTP endpoints directly for basic server stability
"""

import asyncio
import aiohttp
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HTTPStressTester:
    def __init__(self, server_url='http://localhost:8000'):
        self.server_url = server_url
        self.results = {
            'requests': {'successful': 0, 'failed': 0},
            'response_times': [],
            'errors': []
        }
        self.lock = threading.Lock()

    async def test_health_endpoint(self, client, session_id="test"):
        """Test the /health endpoint"""
        try:
            start_time = time.time()
            async with client.get(f"{self.server_url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                
                with self.lock:
                    self.results['response_times'].append(response_time)
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Health check successful: {data}")
                    with self.lock:
                        self.results['requests']['successful'] += 1
                    return True
                else:
                    logger.error(f"Health check failed with status {response.status}")
                    with self.lock:
                        self.results['requests']['failed'] += 1
                    return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            with self.lock:
                self.results['requests']['failed'] += 1
                self.results['errors'].append(f"Health check: {e}")
            return False

    async def test_socketio_polling(self, client, session_id="test"):
        """Test Socket.IO polling endpoint"""
        try:
            start_time = time.time()
            async with client.get(f"{self.server_url}/socket.io/?EIO=4&transport=polling") as response:
                response_time = (time.time() - start_time) * 1000
                
                with self.lock:
                    self.results['response_times'].append(response_time)
                
                if response.status == 200:
                    logger.info(f"Socket.IO polling successful (session: {session_id})")
                    with self.lock:
                        self.results['requests']['successful'] += 1
                    return True
                else:
                    logger.error(f"Socket.IO polling failed with status {response.status}")
                    with self.lock:
                        self.results['requests']['failed'] += 1
                    return False
        except Exception as e:
            logger.error(f"Socket.IO polling error: {e}")
            with self.lock:
                self.results['requests']['failed'] += 1
                self.results['errors'].append(f"Socket.IO polling: {e}")
            return False

    async def test_concurrent_requests(self, num_concurrent=10):
        """Test concurrent HTTP requests"""
        logger.info(f"Testing {num_concurrent} concurrent HTTP requests...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Create concurrent requests
            for i in range(num_concurrent):
                # Mix of health checks and Socket.IO polling requests
                if i % 2 == 0:
                    task = asyncio.create_task(self.test_health_endpoint(session, f"concurrent_{i}"))
                else:
                    task = asyncio.create_task(self.test_socketio_polling(session, f"concurrent_{i}"))
                tasks.append(task)
            
            # Execute all requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            logger.info(f"Concurrent requests completed: {successful} successful")

    async def test_rapid_requests(self, num_requests=20):
        """Test rapid sequential requests"""
        logger.info(f"Testing {num_requests} rapid sequential requests...")
        
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                # Alternate between endpoints
                if i % 2 == 0:
                    await self.test_health_endpoint(session, f"rapid_{i}")
                else:
                    await self.test_socketio_polling(session, f"rapid_{i}")
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)

    async def test_sustained_load(self, duration=30, requests_per_second=2):
        """Test sustained load over time"""
        logger.info(f"Testing sustained load for {duration} seconds at {requests_per_second} req/sec...")
        
        start_time = time.time()
        request_count = 0
        
        async with aiohttp.ClientSession() as session:
            while (time.time() - start_time) < duration:
                # Send request
                if request_count % 2 == 0:
                    await self.test_health_endpoint(session, f"sustained_{request_count}")
                else:
                    await self.test_socketio_polling(session, f"sustained_{request_count}")
                
                request_count += 1
                
                # Wait to maintain desired rate
                await asyncio.sleep(1 / requests_per_second)
        
        logger.info(f"Sustained load test completed: {request_count} requests in {duration} seconds")

    async def run_all_tests(self):
        """Run all HTTP stress tests"""
        logger.info("Starting HTTP stress tests...")
        start_time = time.time()
        
        try:
            # Test 1: Rapid requests
            await self.test_rapid_requests(15)
            await asyncio.sleep(1)
            
            # Test 2: Concurrent requests
            await self.test_concurrent_requests(8)
            await asyncio.sleep(1)
            
            # Test 3: Sustained load
            await self.test_sustained_load(20, 3)
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.results['errors'].append(f"Test suite failed: {e}")
        
        total_time = time.time() - start_time
        self.generate_report(total_time)

    def generate_report(self, total_time):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("HTTP STRESS TEST REPORT")
        print("="*60)
        print(f"Total test time: {total_time:.2f} seconds")
        print()
        
        # Request statistics
        total_requests = self.results['requests']['successful'] + self.results['requests']['failed']
        success_rate = (self.results['requests']['successful'] / max(total_requests, 1)) * 100
        print(f"REQUESTS:")
        print(f"  Total: {total_requests}")
        print(f"  Successful: {self.results['requests']['successful']}")
        print(f"  Failed: {self.results['requests']['failed']}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if total_requests > 0:
            avg_rate = total_requests / total_time
            print(f"  Average Rate: {avg_rate:.2f} req/sec")
        print()
        
        # Response time statistics
        if self.results['response_times']:
            times = self.results['response_times']
            print(f"RESPONSE TIMES (ms):")
            print(f"  Average: {sum(times)/len(times):.1f}")
            print(f"  Min: {min(times):.1f}")
            print(f"  Max: {max(times):.1f}")
            print(f"  Median: {sorted(times)[len(times)//2]:.1f}")
            print()
        
        # Error summary
        if self.results['errors']:
            print(f"ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... and {len(self.results['errors']) - 5} more errors")
            print()
        
        # Performance assessment
        print("SERVER PERFORMANCE:")
        avg_response_time = sum(self.results['response_times']) / max(len(self.results['response_times']), 1)
        
        if success_rate > 95 and avg_response_time < 100:
            print("  ✓ EXCELLENT - Server is highly performant and stable")
        elif success_rate > 90 and avg_response_time < 300:
            print("  ✓ GOOD - Server is stable with good performance")
        elif success_rate > 80 and avg_response_time < 500:
            print("  ⚠ FAIR - Server has moderate performance")
        else:
            print("  ✗ POOR - Server has performance issues")
        
        # Stability assessment
        print("SERVER STABILITY:")
        if len(self.results['errors']) == 0 and success_rate == 100:
            print("  ✓ ROCK SOLID - No errors detected")
        elif len(self.results['errors']) < 3 and success_rate > 95:
            print("  ✓ STABLE - Minor issues detected")
        elif len(self.results['errors']) < 10 and success_rate > 85:
            print("  ⚠ UNSTABLE - Multiple issues detected")
        else:
            print("  ✗ UNRELIABLE - Significant stability issues")
        
        print("="*60)

async def main():
    """Run the HTTP stress test suite"""
    tester = HTTPStressTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())