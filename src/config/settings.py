"""Configuration settings for United Voice Agent"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
try:
    from ..utils.env_loader import load_groq_api_key, load_elevenlabs_api_key, load_serpapi_key, validate_api_keys
except ImportError:
    # Fallback for when running from different contexts
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from utils.env_loader import load_groq_api_key, load_elevenlabs_api_key, load_serpapi_key, validate_api_keys

logger = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    """Whisper STT configuration"""
    model_size: str = "turbo"  # Using Whisper Turbo
    device: str = "cpu"
    compute_type: str = "int8"
    sample_rate: int = 16000
    channels: int = 1
    language: str = "en"
    beam_size: int = 5
    vad_filter: bool = True
    model_id: str = "whisper-large-v3-turbo"  # Groq model ID


@dataclass
class ElevenLabsConfig:
    """ElevenLabs TTS configuration"""
    api_key: Optional[str] = None
    voice_name: str = "Eric"
    voice_id: str = "IiT6R5TRB8W9oKaAjGvM"  # Eric's default ID
    model: str = "eleven_monolingual_v1"


@dataclass
class GroqConfig:
    """Groq LLM configuration"""
    api_key: Optional[str] = None
    model: str = "gemma2-9b-it"  # Using Gemma 2 9B for tool calling
    temperature: float = 0.7
    max_tokens: int = 1024
    whisper_model: str = "whisper-large-v3-turbo"  # Whisper Turbo for STT


@dataclass
class SerpApiConfig:
    """SerpApi configuration for Google Flights"""
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    cache_duration: int = 300  # 5 minutes


@dataclass
class FlightAPIConfig:
    """Flight API configuration"""
    use_real_api: bool = True
    fallback_to_mock: bool = True


@dataclass
class Settings:
    """Main application settings"""
    whisper: WhisperConfig
    elevenlabs: ElevenLabsConfig
    groq: GroqConfig
    serpapi: SerpApiConfig
    flight_api: FlightAPIConfig
    
    # Recording settings
    default_recording_duration: int = 5
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables using robust loader"""
        
        # Load API keys using robust environment loader
        groq_key = load_groq_api_key()
        elevenlabs_key = load_elevenlabs_api_key()
        serpapi_key = load_serpapi_key()
        
        # Validate API keys and log issues
        validation_issues = validate_api_keys()
        if validation_issues:
            logger.warning(f"API key validation issues: {', '.join(validation_issues)}")
        
        # Log successful key detection (without exposing the keys)
        if groq_key:
            logger.info("GROQ_API_KEY detected successfully")
        else:
            logger.warning("GROQ_API_KEY not found - transcription will be disabled")
        
        if elevenlabs_key:
            logger.info("ELEVENLABS_API_KEY detected successfully")
        else:
            logger.info("ELEVENLABS_API_KEY not found - TTS will use fallback")
        
        if serpapi_key:
            logger.info("SERPAPI_API_KEY detected successfully")
        else:
            logger.info("SERPAPI_API_KEY not found - flight search will use mock data")
        
        return cls(
            whisper=WhisperConfig(),
            elevenlabs=ElevenLabsConfig(
                api_key=elevenlabs_key
            ),
            groq=GroqConfig(
                api_key=groq_key
            ),
            serpapi=SerpApiConfig(
                api_key=serpapi_key
            ),
            flight_api=FlightAPIConfig(
                use_real_api=os.getenv('FLIGHT_API_USE_REAL', 'true').lower() == 'true',
                fallback_to_mock=os.getenv('FLIGHT_API_FALLBACK_TO_MOCK', 'true').lower() == 'true'
            )
        )


# Global settings instance
settings = Settings.from_env()