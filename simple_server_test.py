#!/usr/bin/env python3
"""
Simple server test to verify the basic components work
"""

import sys
import os
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test that all imports work"""
    try:
        print("Testing imports...")
        
        # Test HTTP server
        from src.api.http_server import app
        print("✅ HTTP server imports work")
        
        # Test WebSocket components
        from src.services.websocket_server import sio, voice_agents
        print("✅ WebSocket server imports work")
        
        # Test core components
        from src.core.voice_agent import UnitedVoiceAgent
        print("✅ Voice agent imports work")
        
        from src.services.groq_whisper import GroqWhisperClient
        print("✅ Groq Whisper client imports work")
        
        from src.services.tts_service import get_tts_service
        print("✅ TTS service imports work")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        print("\nTesting basic functionality...")
        
        # Test voice agent creation
        from src.core.voice_agent import UnitedVoiceAgent
        agent = UnitedVoiceAgent()
        print("✅ Voice agent created successfully")
        
        # Test simple response
        response = agent.get_response("Hello")
        print(f"✅ Agent response: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_simple_http_server():
    """Start just the HTTP server for testing"""
    try:
        print("\nStarting simple HTTP server...")
        
        from src.api.http_server import app
        import uvicorn
        
        print("Starting server on http://localhost:8000")
        print("Press Ctrl+C to stop")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Server start error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Simple Server Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test basic functionality
    if not test_basic_functionality():
        sys.exit(1)
    
    print("\n🎉 All tests passed! Starting simple HTTP server...")
    
    # Start simple server
    start_simple_http_server()