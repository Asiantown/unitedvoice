#!/usr/bin/env python3
"""
Text-to-Speech Service for United Voice Agent
Handles TTS using ElevenLabs API with fallback to pyttsx3
"""

import os
import logging
import asyncio
import tempfile
import base64
from typing import Optional, Union
from io import BytesIO
from pydub import AudioSegment

try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings, play, save
    ELEVENLABS_AVAILABLE = True
except ImportError:
    try:
        # Try alternate import
        from elevenlabs.client import ElevenLabs
        from elevenlabs import Voice, VoiceSettings, play, save
        ELEVENLABS_AVAILABLE = True
    except ImportError:
        ELEVENLABS_AVAILABLE = False
    
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service with ElevenLabs primary and pyttsx3 fallback"""
    
    def __init__(self):
        self.elevenlabs_client = None
        self.pyttsx3_engine = None
        self.voice_id = None
        
        # Try to initialize ElevenLabs first
        if ELEVENLABS_AVAILABLE:
            self._setup_elevenlabs()
        
        # Initialize pyttsx3 as fallback
        if PYTTSX3_AVAILABLE:
            self._setup_pyttsx3()
        
        if not self.elevenlabs_client and not self.pyttsx3_engine:
            logger.warning("No TTS engines available - TTS will be disabled")
            # Don't raise error - just disable TTS
    
    def _setup_elevenlabs(self):
        """Setup ElevenLabs TTS client"""
        try:
            api_key = settings.elevenlabs.api_key or os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                logger.warning("ElevenLabs API key not found, skipping ElevenLabs setup")
                return
            
            self.elevenlabs_client = ElevenLabs(api_key=api_key)
            self.voice_id = self._get_voice_id(settings.elevenlabs.voice_name)
            logger.info("ElevenLabs TTS initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs: {e}")
            self.elevenlabs_client = None
    
    def _setup_pyttsx3(self):
        """Setup pyttsx3 TTS engine"""
        try:
            self.pyttsx3_engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Prefer a male voice if available
                for voice in voices:
                    if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.pyttsx3_engine.setProperty('rate', 180)  # Speed of speech
            self.pyttsx3_engine.setProperty('volume', 0.9)  # Volume level
            
            logger.info("pyttsx3 TTS initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.pyttsx3_engine = None
    
    def _get_voice_id(self, voice_name: str = "Eric") -> str:
        """Get ElevenLabs voice ID"""
        try:
            if not self.elevenlabs_client:
                return settings.elevenlabs.voice_id
            
            response = self.elevenlabs_client.voices.get_all()
            for voice in response.voices:
                if voice.name.lower() == voice_name.lower():
                    return voice.voice_id
            
            # If voice not found, use first available voice
            if response.voices:
                logger.warning(f"Voice '{voice_name}' not found, using '{response.voices[0].name}'")
                return response.voices[0].voice_id
            else:
                raise Exception("No voices available")
        except Exception as e:
            logger.warning(f"Could not fetch voices: {e}")
            return settings.elevenlabs.voice_id
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        import re
        
        if not text:
            return text
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # Code
        text = re.sub(r'#{1,6}\s*', '', text)         # Headers
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)  # Lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)   # Numbered lists
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    async def synthesize_speech_async(self, text: str) -> Optional[bytes]:
        """Synthesize speech asynchronously and return audio bytes"""
        clean_text = self._clean_text_for_speech(text)
        
        if not clean_text:
            return None
        
        # Try ElevenLabs first
        if self.elevenlabs_client:
            try:
                logger.info(f"Synthesizing speech with ElevenLabs: '{clean_text[:50]}...'")
                
                # Run the blocking operation in a thread pool
                loop = asyncio.get_event_loop()
                audio_generator = await loop.run_in_executor(
                    None,
                    lambda: self.elevenlabs_client.text_to_speech.convert(
                        text=clean_text,
                        voice_id=self.voice_id,
                        model_id=settings.elevenlabs.model,
                        output_format="mp3_44100_128"
                    )
                )
                
                # Convert generator to bytes
                audio_bytes = b""
                for chunk in audio_generator:
                    audio_bytes += chunk
                
                logger.info(f"ElevenLabs TTS successful, audio size: {len(audio_bytes)} bytes")
                return audio_bytes
                
            except Exception as e:
                logger.error(f"ElevenLabs TTS failed: {e}")
        
        # Try gTTS as second option (free Google TTS)
        if GTTS_AVAILABLE:
            try:
                logger.info(f"Synthesizing speech with gTTS: '{clean_text[:50]}...'")
                
                # Use gTTS to generate MP3 directly
                tts = gTTS(text=clean_text, lang='en', slow=False)
                
                # Save to temporary MP3 file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                    temp_mp3_path = temp_mp3.name
                
                # Save the audio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, tts.save, temp_mp3_path)
                
                # Read the MP3 file
                if os.path.exists(temp_mp3_path):
                    with open(temp_mp3_path, 'rb') as f:
                        audio_bytes = f.read()
                    
                    # Clean up temp file
                    os.unlink(temp_mp3_path)
                    
                    logger.info(f"gTTS successful, MP3 size: {len(audio_bytes)} bytes")
                    return audio_bytes
                    
            except Exception as e:
                logger.error(f"gTTS failed: {e}")
        
        # Fallback to pyttsx3
        if self.pyttsx3_engine:
            try:
                logger.info(f"Synthesizing speech with pyttsx3: '{clean_text[:50]}...'")
                
                # Use temporary files for conversion
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_wav_path = temp_wav.name
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                    temp_mp3_path = temp_mp3.name
                
                # Run pyttsx3 synthesis in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._pyttsx3_synthesize,
                    clean_text,
                    temp_wav_path
                )
                
                # Convert audio to MP3 using pydub
                if os.path.exists(temp_wav_path):
                    try:
                        # Detect format and load audio file
                        with open(temp_wav_path, 'rb') as f:
                            header = f.read(4)
                        
                        if header == b'FORM':
                            # AIFF format (Mac default)
                            audio = AudioSegment.from_file(temp_wav_path, format="aiff")
                        elif header == b'RIFF':
                            # WAV format
                            audio = AudioSegment.from_wav(temp_wav_path)
                        else:
                            # Try auto-detection
                            audio = AudioSegment.from_file(temp_wav_path)
                        
                        # Export to MP3
                        audio.export(temp_mp3_path, format="mp3", bitrate="128k")
                        
                        # Read the MP3 file
                        with open(temp_mp3_path, 'rb') as f:
                            audio_bytes = f.read()
                        
                        logger.info(f"pyttsx3 TTS successful, converted to MP3, size: {len(audio_bytes)} bytes")
                    finally:
                        # Clean up temp files
                        if os.path.exists(temp_wav_path):
                            os.unlink(temp_wav_path)
                        if os.path.exists(temp_mp3_path):
                            os.unlink(temp_mp3_path)
                    
                    return audio_bytes
                
            except Exception as e:
                logger.error(f"pyttsx3 TTS failed: {e}")
        
        logger.error("All TTS methods failed")
        return None
    
    def _pyttsx3_synthesize(self, text: str, output_path: str):
        """Synthesize speech using pyttsx3 (blocking)"""
        # Create a new engine instance for thread safety
        engine = pyttsx3.init()
        
        # Configure voice settings
        voices = engine.getProperty('voices')
        if voices:
            # Use a clear voice
            engine.setProperty('voice', voices[0].id)
        
        # Set speech rate and volume
        engine.setProperty('rate', 150)  # Slower for clarity
        engine.setProperty('volume', 1.0)  # Maximum volume
        
        # Generate speech
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        # Clean up
        engine.stop()
    
    def synthesize_speech(self, text: str) -> Optional[bytes]:
        """Synchronous speech synthesis (for backward compatibility)"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.synthesize_speech_async(text))
        except Exception as e:
            logger.error(f"Synchronous TTS failed: {e}")
            return None
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        formats = []
        
        if self.elevenlabs_client:
            formats.extend(['mp3', 'wav'])
        
        if self.pyttsx3_engine:
            formats.append('wav')
        
        return list(set(formats))  # Remove duplicates
    
    def is_available(self) -> bool:
        """Check if TTS service is available"""
        return self.elevenlabs_client is not None or self.pyttsx3_engine is not None


# Global TTS service instance
_tts_service = None

def get_tts_service() -> TTSService:
    """Get or create global TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service