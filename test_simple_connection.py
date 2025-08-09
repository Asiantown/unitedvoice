#!/usr/bin/env python3
"""Simple connection test"""

import requests
import time

def test_http_connection():
    try:
        response = requests.get("http://localhost:8000/socket.io/", timeout=5)
        print(f"HTTP Response: {response.status_code}")
        print(f"Headers: {response.headers}")
        return True
    except Exception as e:
        print(f"HTTP connection failed: {e}")
        return False

def test_socketio_handshake():
    try:
        response = requests.get("http://localhost:8000/socket.io/?EIO=4&transport=polling", timeout=5)
        print(f"Socket.IO Handshake: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return True
    except Exception as e:
        print(f"Socket.IO handshake failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing server connectivity...")
    print("=" * 50)
    
    print("\n1. Testing HTTP connection...")
    http_ok = test_http_connection()
    
    print("\n2. Testing Socket.IO handshake...")
    socketio_ok = test_socketio_handshake()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"HTTP: {'✅ OK' if http_ok else '❌ FAIL'}")
    print(f"Socket.IO: {'✅ OK' if socketio_ok else '❌ FAIL'}")