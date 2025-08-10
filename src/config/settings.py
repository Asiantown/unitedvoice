"""
Configuration Settings for United Voice Agent

This module defines the configuration structure and default values for all
components of the United Voice Agent system including STT, TTS, LLM, and
external API integrations.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Safe import with fallback for environment loader
try:
    from ..utils.env_loader import (
        load_groq_api_key,
        load_elevenlabs_api_key, 
        load_serpapi_key,
        validate_api_keys
    )
except ImportError:
    # Fallback for when running from different contexts
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    try:
        from utils.env_loader import (
            load_groq_api_key,
            load_elevenlabs_api_key,
            load_serpapi_key, 
            validate_api_keys
        )
    except ImportError:
        # Ultimate fallback - define basic functions
        def load_groq_api_key() -> Optional[str]:
            return os.getenv('GROQ_API_KEY')
        
        def load_elevenlabs_api_key() -> Optional[str]:
            return os.getenv('ELEVENLABS_API_KEY')
        
        def load_serpapi_key() -> Optional[str]:
            return os.getenv('SERPAPI_API_KEY')
        
        def validate_api_keys() -> List[str]:
            issues = []
            if not load_groq_api_key():
                issues.append("GROQ_API_KEY missing")
            if not load_elevenlabs_api_key():
                issues.append("ELEVENLABS_API_KEY missing")
            if not load_serpapi_key():
                issues.append("SERPAPI_API_KEY missing")
            return issues

logger = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    """
    Configuration for Whisper Speech-to-Text service.
    
    This configuration supports both Groq's hosted Whisper API and
    local Whisper model execution.
    
    Attributes:
        model_size: Size variant of the Whisper model
        device: Processing device (cpu/cuda)
        compute_type: Precision for inference
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels
        language: Primary language for transcription
        beam_size: Beam search width for decoding
        vad_filter: Voice activity detection filtering
        model_id: Groq-specific model identifier
    """
    model_size: str = "turbo"
    device: str = "cpu"
    compute_type: str = "int8" 
    sample_rate: int = 16000
    channels: int = 1
    language: str = "en"
    beam_size: int = 5
    vad_filter: bool = True
    model_id: str = "whisper-large-v3-turbo"
    
    # Advanced configuration
    chunk_length_s: int = 30  # Audio chunk length in seconds
    timeout_s: int = 30  # Request timeout
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if self.channels not in (1, 2):
            raise ValueError("Channels must be 1 (mono) or 2 (stereo)")
        if self.beam_size < 1:
            raise ValueError("Beam size must be at least 1")


@dataclass
class ElevenLabsConfig:
    """
    Configuration for ElevenLabs Text-to-Speech service.
    
    Provides settings for voice selection, audio quality, and API behavior.
    
    Attributes:
        api_key: ElevenLabs API authentication key
        voice_name: Human-readable voice name
        voice_id: ElevenLabs voice identifier
        model: TTS model version to use
        stability: Voice stability setting (0.0-1.0)
        similarity_boost: Similarity enhancement (0.0-1.0)
        style: Style exaggeration (0.0-1.0)
    """
    api_key: Optional[str] = None
    voice_name: str = "Eric"
    voice_id: str = "IiT6R5TRB8W9oKaAjGvM"
    model: str = "eleven_monolingual_v1"
    
    # Voice tuning parameters
    stability: float = 0.5
    similarity_boost: float = 0.8  
    style: float = 0.2
    
    # API configuration
    timeout_s: int = 30
    max_retries: int = 3
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        for param_name, param_value in [
            ("stability", self.stability),
            ("similarity_boost", self.similarity_boost),
            ("style", self.style)
        ]:
            if not 0.0 <= param_value <= 1.0:
                raise ValueError(f"{param_name} must be between 0.0 and 1.0")


@dataclass
class GroqConfig:
    """
    Configuration for Groq Language Model service.
    
    Controls LLM behavior for natural language understanding and generation.
    
    Attributes:
        api_key: Groq API authentication key
        model: Primary LLM model identifier
        temperature: Sampling randomness (0.0-2.0)
        max_tokens: Maximum response length
        whisper_model: STT model for Groq Whisper
        top_p: Nucleus sampling parameter
        frequency_penalty: Repetition reduction
        presence_penalty: Topic diversity encouragement
    """
    api_key: Optional[str] = None
    model: str = "gemma2-9b-it"
    temperature: float = 0.7
    max_tokens: int = 1024
    whisper_model: str = "whisper-large-v3-turbo"
    
    # Advanced generation parameters
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # API configuration
    timeout_s: int = 30
    max_retries: int = 3
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("Top_p must be between 0.0 and 1.0")


@dataclass
class SerpApiConfig:
    """
    Configuration for SerpApi Google Flights integration.
    
    Controls flight search API behavior and caching strategy.
    
    Attributes:
        api_key: SerpApi authentication key
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        cache_duration: Response cache duration in seconds
        rate_limit_delay: Delay between requests in seconds
    """
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    cache_duration: int = 300  # 5 minutes
    
    # Rate limiting
    rate_limit_delay: float = 1.0
    
    # Search configuration
    max_results: int = 10
    currency: str = "USD"
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.cache_duration < 0:
            raise ValueError("Cache duration cannot be negative")


@dataclass
class FlightAPIConfig:
    """
    Configuration for flight search API behavior.
    
    Controls the strategy for flight search including fallback behavior.
    
    Attributes:
        use_real_api: Whether to use real flight APIs
        fallback_to_mock: Whether to fallback to mock data on API failure
        prefer_nonstop: Preference for nonstop flights
        max_layovers: Maximum number of layovers to consider
    """
    use_real_api: bool = True
    fallback_to_mock: bool = True
    
    # Search preferences
    prefer_nonstop: bool = True
    max_layovers: int = 2
    
    # Performance settings
    parallel_searches: bool = True
    search_timeout: int = 15


@dataclass
class Settings:
    """
    Main application configuration container.
    
    Aggregates all service configurations and provides application-wide settings.
    
    Attributes:
        whisper: Speech-to-text configuration
        elevenlabs: Text-to-speech configuration  
        groq: Language model configuration
        serpapi: Flight search API configuration
        flight_api: Flight search behavior configuration
        default_recording_duration: Audio recording length in seconds
        log_level: Application logging level
        debug_mode: Enable debug features
    """
    whisper: WhisperConfig
    elevenlabs: ElevenLabsConfig
    groq: GroqConfig
    serpapi: SerpApiConfig
    flight_api: FlightAPIConfig
    
    # Application settings
    default_recording_duration: int = 5
    log_level: str = "INFO"
    debug_mode: bool = False
    
    # Performance settings
    max_conversation_history: int = 20
    response_cache_size: int = 100
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables with robust error handling.
        
        Returns:
            Fully configured Settings instance
            
        Raises:
            ValueError: If critical configuration is invalid
        """
        # Load API keys using robust environment loader
        groq_key = load_groq_api_key()
        elevenlabs_key = load_elevenlabs_api_key()
        serpapi_key = load_serpapi_key()
        
        # Validate API keys and collect issues
        validation_issues = validate_api_keys()
        if validation_issues:
            logger.warning(f"API key validation issues: {', '.join(validation_issues)}")
        
        # Log key detection status (without exposing actual keys)
        cls._log_key_status("GROQ_API_KEY", groq_key, "transcription will be disabled")
        cls._log_key_status("ELEVENLABS_API_KEY", elevenlabs_key, "TTS will use fallback")
        cls._log_key_status("SERPAPI_API_KEY", serpapi_key, "flight search will use mock data")
        
        # Parse environment-specific settings
        debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_log_levels:
            logger.warning(f"Invalid LOG_LEVEL '{log_level}', defaulting to INFO")
            log_level = 'INFO'
        
        try:
            return cls(
                whisper=WhisperConfig(),
                elevenlabs=ElevenLabsConfig(api_key=elevenlabs_key),
                groq=GroqConfig(api_key=groq_key),
                serpapi=SerpApiConfig(api_key=serpapi_key),
                flight_api=FlightAPIConfig(
                    use_real_api=os.getenv('FLIGHT_API_USE_REAL', 'true').lower() == 'true',
                    fallback_to_mock=os.getenv('FLIGHT_API_FALLBACK_TO_MOCK', 'true').lower() == 'true'
                ),
                default_recording_duration=int(os.getenv('RECORDING_DURATION', '5')),
                log_level=log_level,
                debug_mode=debug_mode
            )
        except Exception as e:
            logger.error(f"Failed to create settings from environment: {e}")
            raise ValueError(f"Configuration initialization failed: {e}")
    
    @staticmethod
    def _log_key_status(key_name: str, key_value: Optional[str], fallback_msg: str) -> None:
        """
        Log the status of an API key without exposing its value.
        
        Args:
            key_name: Name of the API key
            key_value: The key value (or None)
            fallback_msg: Message to show when key is missing
        """
        if key_value:
            logger.info(f"{key_name} detected successfully")
        else:
            logger.warning(f"{key_name} not found - {fallback_msg}")
    
    def validate(self) -> List[str]:
        """
        Validate the complete configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate recording duration
        if self.default_recording_duration <= 0:
            errors.append("Default recording duration must be positive")
        
        # Validate conversation history limit
        if self.max_conversation_history <= 0:
            errors.append("Max conversation history must be positive")
        
        # Check for at least one working API key
        if not any([self.groq.api_key, self.elevenlabs.api_key, self.serpapi.api_key]):
            errors.append("At least one API key must be configured")
        
        return errors
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the current configuration.
        
        Returns:
            Dictionary containing non-sensitive configuration details
        """
        return {
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "recording_duration": self.default_recording_duration,
            "apis_configured": {
                "groq": bool(self.groq.api_key),
                "elevenlabs": bool(self.elevenlabs.api_key),
                "serpapi": bool(self.serpapi.api_key)
            },
            "models": {
                "groq_model": self.groq.model,
                "whisper_model": self.whisper.model_id,
                "tts_model": self.elevenlabs.model
            }
        }


# Global settings instance - initialized from environment
try:
    settings = Settings.from_env()
    
    # Validate the loaded settings
    validation_errors = settings.validate()
    if validation_errors:
        logger.error(f"Configuration validation failed: {'; '.join(validation_errors)}")
        # Don't fail completely, but warn the user
        
    logger.info("Configuration loaded successfully")
    
    # Log debug info if in debug mode
    if settings.debug_mode:
        debug_info = settings.get_debug_info()
        logger.debug(f"Configuration debug info: {debug_info}")
        
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Create minimal fallback configuration
    logger.warning("Using minimal fallback configuration")
    settings = Settings(
        whisper=WhisperConfig(),
        elevenlabs=ElevenLabsConfig(),
        groq=GroqConfig(),
        serpapi=SerpApiConfig(),
        flight_api=FlightAPIConfig(use_real_api=False)
    )