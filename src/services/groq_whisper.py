#!/usr/bin/env python3
"""
Groq Whisper client for speech-to-text using Whisper Turbo
"""

import os
import base64
from typing import Optional, Dict, Any
from groq import Groq
import logging

logger = logging.getLogger(__name__)


class GroqWhisperClient:
    """Client for Groq's Whisper Turbo API"""
    
    def __init__(self, api_key: str = None):
        """Initialize Groq Whisper client"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "whisper-large-v3-turbo"
        
    def transcribe_audio_file(self, audio_file_path: str, language: str = "en") -> str:
        """
        Transcribe audio file using Groq Whisper Turbo
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (default: "en")
            
        Returns:
            Transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            
            # Response is directly the transcribed text
            return response.strip()
            
        except Exception as e:
            logger.error(f"Groq Whisper transcription error: {e}")
            raise
    
    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav", language: str = "en") -> str:
        """
        Transcribe audio bytes using Groq Whisper Turbo
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Filename for the audio (helps with format detection)
            language: Language code (default: "en")
            
        Returns:
            Transcribed text
        """
        try:
            # Save to temporary file (Groq API requires file-like object)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            try:
                # Transcribe using file path
                result = self.transcribe_audio_file(tmp_path, language)
                return result
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Groq Whisper transcription error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Groq Whisper API connection"""
        try:
            # Create a tiny silent audio file for testing
            import wave
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    # Write 0.1 seconds of silence
                    wav_file.writeframes(b'\x00\x00' * 1600)
                
                tmp_path = tmp_file.name
            
            try:
                # Try to transcribe the silent audio
                result = self.transcribe_audio_file(tmp_path, "en")
                logger.info(f"Groq Whisper test successful. Result: '{result}'")
                return True
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Groq Whisper test failed: {e}")
            return False


# Test the client
if __name__ == "__main__":
    print("Testing Groq Whisper Client")
    print("=" * 50)
    
    client = GroqWhisperClient()
    
    # Test connection
    if client.test_connection():
        print("✅ Groq Whisper API connection successful")
    else:
        print("❌ Groq Whisper API connection failed")
    
    # Test with a sample audio file if provided
    import sys
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"\nTranscribing: {audio_file}")
        try:
            result = client.transcribe_audio_file(audio_file)
            print(f"Transcription: {result}")
        except Exception as e:
            print(f"Error: {e}")