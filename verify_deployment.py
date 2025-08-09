#!/usr/bin/env python3
"""
Quick deployment verification script for Railway
Run this after deployment to verify everything is working
"""

import os
import sys
import requests
import socketio
import json
from typing import Dict, Any
import asyncio
import time

def check_health_endpoint(base_url: str) -> Dict[str, Any]:
    """Check if the health endpoint is responsive"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            return {
                "status": "success",
                "data": response.json(),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "response_time": None
        }

def check_websocket_connection(base_url: str) -> Dict[str, Any]:
    """Check if WebSocket connection is working"""
    try:
        # Create Socket.IO client
        sio = socketio.SimpleClient()
        
        # Connect to server
        start_time = time.time()
        sio.connect(base_url, transports=['websocket'])
        connection_time = time.time() - start_time
        
        # Test basic communication
        test_passed = False
        
        @sio.event
        def connect():
            nonlocal test_passed
            test_passed = True
        
        # Wait a bit for connection
        time.sleep(1)
        
        # Disconnect
        sio.disconnect()
        
        return {
            "status": "success" if test_passed else "warning",
            "connection_time": connection_time,
            "message": "WebSocket connection successful" if test_passed else "Connected but no response"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "connection_time": None
        }

def check_api_endpoints(base_url: str) -> Dict[str, Any]:
    """Check various API endpoints"""
    endpoints = {
        "root": "/",
        "config": "/api/config",
        "health_detailed": "/health/detailed"
    }
    
    results = {}
    
    for name, endpoint in endpoints.items():
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            results[name] = {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
            if response.status_code != 200:
                results[name]["error"] = response.text[:200]
        except Exception as e:
            results[name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

def main():
    """Main verification function"""
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <railway_url>")
        print("Example: python verify_deployment.py https://your-app.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 United Voice Agent - Deployment Verification")
    print("=" * 60)
    print(f"Testing URL: {base_url}")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("\n1. Testing Health Endpoint...")
    health_result = check_health_endpoint(base_url)
    
    if health_result["status"] == "success":
        print(f"   ✅ Health check passed ({health_result['response_time']:.2f}s)")
        services = health_result["data"].get("services", {})
        for service, status in services.items():
            emoji = "✅" if status == "available" else "❌"
            print(f"   {emoji} {service}: {status}")
    else:
        print(f"   ❌ Health check failed: {health_result['error']}")
    
    # Test 2: WebSocket connection
    print("\n2. Testing WebSocket Connection...")
    ws_result = check_websocket_connection(base_url)
    
    if ws_result["status"] == "success":
        print(f"   ✅ WebSocket connection successful ({ws_result['connection_time']:.2f}s)")
    elif ws_result["status"] == "warning":
        print(f"   ⚠️  WebSocket connected but limited response ({ws_result.get('connection_time', 0):.2f}s)")
    else:
        print(f"   ❌ WebSocket connection failed: {ws_result['error']}")
    
    # Test 3: API endpoints
    print("\n3. Testing API Endpoints...")
    api_results = check_api_endpoints(base_url)
    
    for endpoint, result in api_results.items():
        if result["status"] == "success":
            print(f"   ✅ {endpoint}: OK ({result['response_time']:.2f}s)")
        else:
            print(f"   ❌ {endpoint}: {result.get('error', f'HTTP {result.get(\"status_code\", \"unknown\")}')})")
    
    # Summary
    print("\n" + "=" * 60)
    total_tests = 3 + len(api_results)
    passed_tests = sum([
        1 if health_result["status"] == "success" else 0,
        1 if ws_result["status"] == "success" else 0,
        sum(1 for r in api_results.values() if r["status"] == "success")
    ])
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your deployment is ready.")
        print(f"\n📋 Frontend Environment Variable:")
        print(f"   NEXT_PUBLIC_WS_URL={base_url}")
        print(f"\n🔗 Useful URLs:")
        print(f"   • API Docs: {base_url}/docs")
        print(f"   • Health Check: {base_url}/health")
        print(f"   • WebSocket: {base_url}/socket.io/")
    else:
        print(f"⚠️  {passed_tests}/{total_tests} tests passed. Check the failures above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()