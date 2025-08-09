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

# Make all audio processing optional
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

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

# Make settings import optional
try:
    from src.config.settings import settings
    SETTINGS_AVAILABLE = True
except ImportError:
    # Create minimal settings fallback
    class MockSettings:
        class Elevenlabs:
            api_key = None
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice
            voice_name = "Eric"
            model = "eleven_monolingual_v1"
        elevenlabs = Elevenlabs()
    
    settings = MockSettings()
    SETTINGS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MockTTSService:
    """Mock TTS service that always works without any dependencies"""
    
    def __init__(self):
        self.elevenlabs_client = None
        self.pyttsx3_engine = None
        self.voice_id = None
        logger.info("Mock TTS service initialized (no dependencies required)")
    
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
        """Mock speech synthesis - returns None but logs the text"""
        clean_text = self._clean_text_for_speech(text)
        
        if not clean_text:
            return None
        
        logger.info(f"Mock TTS: Would synthesize speech for: '{clean_text[:100]}...'")
        logger.warning("Mock TTS service active - no audio will be generated. Install TTS dependencies for audio output.")
        return None
    
    def synthesize_speech(self, text: str) -> Optional[bytes]:
        """Synchronous mock speech synthesis"""
        try:
            # Handle asyncio event loop properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we can't use run_until_complete
                    # Just call the async function directly and return None
                    logger.info(f"Mock TTS: Would synthesize speech for: '{text[:100] if text else ''}...'")
                    return None
                else:
                    return loop.run_until_complete(self.synthesize_speech_async(text))
            except RuntimeError:
                # No event loop, create a new one
                return asyncio.run(self.synthesize_speech_async(text))
        except Exception as e:
            logger.warning(f"Mock TTS synthesis skipped: {e}")
            return None
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats (empty for mock)"""
        return []
    
    def is_available(self) -> bool:
        """Mock TTS is always 'available' but doesn't produce audio"""
        return True


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
            if not PYTTSX3_AVAILABLE:
                logger.warning("pyttsx3 not available - skipping pyttsx3 setup")
                return
                
            self.pyttsx3_engine = pyttsx3.init()
            
            # Configure voice settings safely
            try:
                voices = self.pyttsx3_engine.getProperty('voices')
                if voices and len(voices) > 0:
                    # Prefer a male voice if available
                    for voice in voices:
                        if voice and hasattr(voice, 'name') and voice.name:
                            if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                                self.pyttsx3_engine.setProperty('voice', voice.id)
                                break
                
                # Set speech rate and volume safely
                self.pyttsx3_engine.setProperty('rate', 180)  # Speed of speech
                self.pyttsx3_engine.setProperty('volume', 0.9)  # Volume level
            except Exception as voice_error:
                logger.warning(f"Could not configure pyttsx3 voice settings: {voice_error}")
            
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
                
                # Convert audio to MP3 using pydub (if available)
                if os.path.exists(temp_wav_path):
                    try:
                        if PYDUB_AVAILABLE:
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
                        else:
                            # Without pydub, just return the WAV file directly
                            with open(temp_wav_path, 'rb') as f:
                                audio_bytes = f.read()
                            
                            logger.info(f"pyttsx3 TTS successful, WAV format (pydub not available), size: {len(audio_bytes)} bytes")
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
        engine = None
        try:
            if not PYTTSX3_AVAILABLE:
                raise RuntimeError("pyttsx3 not available")
            
            # Create a new engine instance for thread safety
            engine = pyttsx3.init()
            
            # Configure voice settings safely
            try:
                voices = engine.getProperty('voices')
                if voices and len(voices) > 0:
                    # Use the first available voice
                    engine.setProperty('voice', voices[0].id)
            except Exception as voice_error:
                logger.warning(f"Could not set pyttsx3 voice: {voice_error}")
            
            try:
                # Set speech rate and volume
                engine.setProperty('rate', 150)  # Slower for clarity
                engine.setProperty('volume', 1.0)  # Maximum volume
            except Exception as prop_error:
                logger.warning(f"Could not set pyttsx3 properties: {prop_error}")
            
            # Generate speech
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            raise
        finally:
            # Clean up safely
            if engine:
                try:
                    engine.stop()
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up pyttsx3 engine: {cleanup_error}")
    
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

def get_tts_service():
    """Get or create global TTS service instance - guaranteed to never crash"""
    global _tts_service
    if _tts_service is None:
        try:
            # Try to create a full TTS service first
            _tts_service = TTSService()
            
            # If no TTS engines are available, use mock service
            if not _tts_service.is_available():
                logger.warning("No TTS engines available, falling back to Mock TTS service")
                _tts_service = MockTTSService()
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            logger.info("Falling back to Mock TTS service")
            try:
                _tts_service = MockTTSService()
            except Exception as mock_error:
                logger.error(f"Even Mock TTS service failed: {mock_error}")
                # Create the most basic fallback possible
                _tts_service = _create_emergency_tts_service()
    
    return _tts_service

def _create_emergency_tts_service():
    """Create an ultra-minimal TTS service that never crashes"""
    class EmergencyTTSService:
        def __init__(self):
            self.elevenlabs_client = None
            self.pyttsx3_engine = None
            self.voice_id = None
            
        async def synthesize_speech_async(self, text):
            return None
            
        def synthesize_speech(self, text):
            return None
            
        def get_supported_formats(self):
            return []
            
        def is_available(self):
            return False
    
    logger.warning("Using emergency TTS service - all TTS functionality disabled")
    return EmergencyTTSService()