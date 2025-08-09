#!/usr/bin/env python3
"""Test audio playback with conversion to MP3"""

import asyncio
import base64
import tempfile
import os
from src.services.tts_service import get_tts_service

async def test_tts():
    print("Initializing TTS service...")
    tts = get_tts_service()
    
    test_text = "Hello! This is a test of the text to speech system. The audio should now be in MP3 format and play correctly in your browser."
    
    print(f"Generating speech for: '{test_text}'")
    audio_bytes = await tts.synthesize_speech_async(test_text)
    
    if audio_bytes:
        print(f"✅ Audio generated successfully! Size: {len(audio_bytes)} bytes")
        
        # Check the format by looking at the header
        header = audio_bytes[:4]
        if header[:2] == b'ID' or header[:2] == b'\xff\xfb':
            print("✅ Audio is in MP3 format")
        elif header == b'RIFF':
            print("⚠️ Audio is in WAV format")
        elif header == b'FORM':
            print("⚠️ Audio is in AIFF format")
        else:
            print(f"❓ Unknown audio format: {header}")
        
        # Save to file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_bytes)
            print(f"Audio saved to: {f.name}")
            print("You can play this file to verify it works")
        
        # Encode to base64 like the server does
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        print(f"Base64 encoded length: {len(audio_base64)} chars")
        print(f"First 100 chars of base64: {audio_base64[:100]}...")
        
        return True
    else:
        print("❌ Failed to generate audio")
        return False

if __name__ == "__main__":
    asyncio.run(test_tts())