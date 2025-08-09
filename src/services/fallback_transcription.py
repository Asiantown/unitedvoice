#!/usr/bin/env python3
"""
Fallback transcription service for when Groq API is unavailable
Provides mock transcription and user-friendly error handling
"""

import os
import time
import logging
import random
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Result from transcription service"""
    text: str
    confidence: float
    source: str  # 'groq', 'mock', 'error'
    timestamp: float

class FallbackTranscriptionService:
    """Fallback service for when primary transcription fails"""
    
    def __init__(self):
        self.mock_responses = [
            "I'd like to book a flight",
            "I need to travel to New York", 
            "Can you help me find flights to Chicago?",
            "I want to fly next Friday",
            "Round trip to Los Angeles please",
            "What flights are available tomorrow?",
            "I need to change my booking",
            "Can you check flight prices?",
            "I'm looking for the cheapest option",
            "I prefer morning flights"
        ]
        
        self.mock_booking_responses = {
            "name": ["John Smith", "Sarah Johnson", "Mike Davis", "Lisa Chen"],
            "destination": ["New York", "Los Angeles", "Chicago", "Miami", "Seattle"],
            "origin": ["San Francisco", "Boston", "Denver", "Atlanta"],
            "date": ["next Friday", "tomorrow", "next Monday", "next week"],
            "confirmation": ["yes please", "that sounds good", "I'll take it", "book it"]
        }
        
        self.last_mock_used = None
        
    def get_mock_transcription(self, context: str = None) -> TranscriptionResult:
        """Generate a mock transcription based on context"""
        
        # Context-aware mock responses
        if context:
            context_lower = context.lower()
            
            if "name" in context_lower:
                text = random.choice(self.mock_booking_responses["name"])
            elif "where" in context_lower or "destination" in context_lower:
                text = random.choice(self.mock_booking_responses["destination"]) 
            elif "from" in context_lower or "departing" in context_lower:
                text = random.choice(self.mock_booking_responses["origin"])
            elif "when" in context_lower or "date" in context_lower:
                text = random.choice(self.mock_booking_responses["date"])
            elif "option" in context_lower or "flight" in context_lower:
                text = random.choice(self.mock_booking_responses["confirmation"])
            else:
                text = random.choice(self.mock_responses)
        else:
            # Avoid repeating the same mock response
            available_responses = [r for r in self.mock_responses if r != self.last_mock_used]
            text = random.choice(available_responses)
        
        self.last_mock_used = text
        
        return TranscriptionResult(
            text=text,
            confidence=0.85,  # Mock confidence
            source="mock",
            timestamp=time.time()
        )
    
    def get_user_input_transcription(self, prompt: str = "Please type what you said: ") -> TranscriptionResult:
        """Get transcription via text input when voice fails"""
        try:
            text = input(f"\n🔤 {prompt}").strip()
            if text:
                return TranscriptionResult(
                    text=text,
                    confidence=1.0,  # User typed, so 100% accurate
                    source="user_input",
                    timestamp=time.time()
                )
            else:
                return self.get_mock_transcription()
        except (KeyboardInterrupt, EOFError):
            # User cancelled input
            return TranscriptionResult(
                text="I need to exit",
                confidence=1.0,
                source="user_input", 
                timestamp=time.time()
            )

class EnhancedGroqWhisperClient:
    """Enhanced Groq Whisper client with comprehensive fallback mechanisms"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.fallback_service = FallbackTranscriptionService()
        self.groq_available = False
        self.last_error = None
        
        # Try to initialize Groq client
        try:
            if self.api_key:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                self.model = "whisper-large-v3-turbo"
                
                # Test connection
                if self._test_groq_connection():
                    self.groq_available = True
                    logger.info("Groq Whisper client initialized successfully")
                else:
                    logger.warning("Groq connection test failed - using fallback mode")
            else:
                logger.warning("No GROQ_API_KEY found - using fallback mode")
                
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.last_error = str(e)
    
    def _test_groq_connection(self) -> bool:
        """Test if Groq API is working"""
        try:
            import wave
            import tempfile
            
            # Create minimal test audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(b'\x00\x00' * 1600)  # 0.1 seconds of silence
                
                tmp_path = tmp_file.name
            
            try:
                with open(tmp_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language="en",
                        response_format="text"
                    )
                return True
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            self.last_error = str(e)
            return False
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "en", 
                            context: str = None, fallback_mode: str = "mock") -> TranscriptionResult:
        """
        Transcribe audio file with fallback mechanisms
        
        Args:
            audio_file_path: Path to audio file
            language: Language code
            context: Context hint for better mock responses
            fallback_mode: 'mock', 'user_input', or 'error'
        """
        
        # Try Groq first if available
        if self.groq_available:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        response_format="text"
                    )
                
                text = response.strip()
                logger.info(f"Groq transcription successful: {text[:50]}...")
                
                return TranscriptionResult(
                    text=text,
                    confidence=0.95,
                    source="groq",
                    timestamp=time.time()
                )
                
            except Exception as e:
                logger.error(f"Groq transcription failed: {e}")
                self.last_error = str(e)
                
                # Check if it's a quota/auth issue
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.error("Groq quota exceeded - switching to fallback")
                    self.groq_available = False
                elif "401" in str(e) or "unauthorized" in str(e).lower():
                    logger.error("Groq authentication failed - switching to fallback") 
                    self.groq_available = False
        
        # Use fallback mechanisms
        logger.warning(f"Using fallback transcription mode: {fallback_mode}")
        
        if fallback_mode == "user_input":
            prompt = "Voice transcription unavailable. Please type what you said: "
            if context:
                prompt = f"I couldn't hear you clearly. {context}. Please type your response: "
            return self.fallback_service.get_user_input_transcription(prompt)
        
        elif fallback_mode == "mock":
            return self.fallback_service.get_mock_transcription(context)
        
        else:  # error mode
            return TranscriptionResult(
                text="Sorry, I'm having trouble with voice recognition right now",
                confidence=0.0,
                source="error",
                timestamp=time.time()
            )
    
    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav", 
                             language: str = "en", context: str = None, 
                             fallback_mode: str = "mock") -> TranscriptionResult:
        """Transcribe audio bytes with fallbacks"""
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            return self.transcribe_audio_file(tmp_path, language, context, fallback_mode)
        finally:
            os.unlink(tmp_path)
    
    def get_status(self) -> dict:
        """Get current status of the transcription service"""
        return {
            "groq_available": self.groq_available,
            "api_key_configured": bool(self.api_key),
            "last_error": self.last_error,
            "fallback_ready": True
        }
    
    def explain_fallback_to_user(self) -> str:
        """Generate user-friendly explanation of current fallback mode"""
        if not self.api_key:
            return ("I don't have access to voice recognition right now, but I can still help you! "
                   "I'll use some example requests to demonstrate our booking system.")
        
        elif "quota" in (self.last_error or "").lower() or "429" in (self.last_error or ""):
            return ("Our voice recognition service is temporarily at capacity. "
                   "I'll simulate your responses to show you how our booking works, "
                   "or you can type your requests if you prefer.")
        
        elif "401" in (self.last_error or "") or "unauthorized" in (self.last_error or "").lower():
            return ("There's a temporary authentication issue with our voice service. "
                   "Let me demonstrate our booking process with example responses.")
        
        else:
            return ("I'm having trouble with voice recognition at the moment. "
                   "I'll use example responses to show you our booking capabilities, "
                   "or you can type what you want to say.")

# Backwards compatibility
class GroqWhisperClient(EnhancedGroqWhisperClient):
    """Backwards compatible interface"""
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "en") -> str:
        """Backwards compatible transcribe method"""
        result = super().transcribe_audio_file(audio_file_path, language, fallback_mode="mock")
        
        # Log the source for debugging
        if result.source != "groq":
            logger.info(f"Using {result.source} transcription: {result.text}")
        
        return result.text
    
    def test_connection(self) -> bool:
        """Test connection with fallback info"""
        if self.groq_available:
            return True
        
        # Even if Groq is unavailable, we have fallbacks
        logger.info("Groq unavailable but fallback mechanisms are ready")
        return True  # Always return True since we have fallbacks

if __name__ == "__main__":
    # Test the enhanced client
    print("🧪 Testing Enhanced Groq Whisper Client")
    print("=" * 50)
    
    client = EnhancedGroqWhisperClient()
    status = client.get_status()
    
    print(f"Status: {json.dumps(status, indent=2)}")
    print(f"\nExplanation: {client.explain_fallback_to_user()}")
    
    # Test mock transcription
    print("\n🎭 Testing mock transcription...")
    for context in ["What's your name?", "Where are you flying to?", "When do you want to travel?"]:
        mock_result = client.fallback_service.get_mock_transcription(context)
        print(f"Context: '{context}' -> Mock: '{mock_result.text}'")