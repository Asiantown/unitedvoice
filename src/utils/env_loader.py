"""
Robust Environment Variable Loader for Railway and other platforms
================================================================

This module provides robust environment variable loading that handles
Railway's specific deployment environment and various edge cases.
"""

import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def load_env_var_robust(
    var_name: str, 
    prefixes: Optional[List[str]] = None,
    case_sensitive: bool = True,
    fallback_value: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Robust environment variable loader for Railway and other platforms
    
    Args:
        var_name: Base variable name (e.g., 'GROQ_API_KEY')
        prefixes: List of prefixes to try (e.g., ['RAILWAY_', 'APP_'])
        case_sensitive: Whether to try case variations
        fallback_value: Value to return if not found
        required: Whether this variable is required (logs warning if missing)
    
    Returns:
        The environment variable value if found, fallback_value otherwise
    """
    
    # Default prefixes for Railway and common deployment platforms
    if prefixes is None:
        prefixes = [
            '',           # No prefix (standard)
            'RAILWAY_',   # Railway platform
            'APP_',       # Generic app prefix
            'SERVICE_',   # Service-specific
            'BACKEND_',   # Backend-specific
            'PRODUCTION_', # Production environment
            'PROD_',      # Short production
            'API_',       # API-specific
            'ENV_',       # Environment prefix
        ]
    
    # Case variations to try if not case sensitive
    case_variations = [var_name]
    if not case_sensitive:
        case_variations.extend([
            var_name.lower(),
            var_name.upper(), 
            var_name.title(),
            var_name.capitalize(),
            var_name.swapcase(),
            # Common variations
            var_name.replace('_', '-'),
            var_name.replace('-', '_'),
        ])
    
    # Remove duplicates while preserving order
    case_variations = list(dict.fromkeys(case_variations))
    
    # Try all combinations of prefixes and case variations
    for prefix in prefixes:
        for case_var in case_variations:
            full_key = f"{prefix}{case_var}"
            
            # Try multiple access methods
            for method in [os.getenv, os.environ.get]:
                try:
                    value = method(full_key)
                    if value and value.strip():  # Check for non-empty strings
                        logger.debug(f"Found {var_name} as {full_key}")
                        return value.strip()
                except Exception as e:
                    logger.debug(f"Error accessing {full_key}: {e}")
                    continue
    
    # Last resort: fuzzy matching for partial key names
    # This catches cases where Railway might use different naming
    var_name_lower = var_name.lower()
    for env_key, env_value in os.environ.items():
        if env_value and env_value.strip():
            env_key_lower = env_key.lower()
            
            # Check if the key contains the main parts of our variable name
            if (var_name_lower in env_key_lower or 
                any(part in env_key_lower for part in var_name_lower.split('_') if len(part) > 2)):
                logger.debug(f"Found {var_name} via fuzzy match: {env_key}")
                return env_value.strip()
    
    # If we get here, the variable wasn't found
    if required:
        logger.warning(f"Required environment variable {var_name} not found")
    else:
        logger.debug(f"Optional environment variable {var_name} not found")
    
    return fallback_value


def load_groq_api_key() -> Optional[str]:
    """Load GROQ API key with Railway-specific handling"""
    return load_env_var_robust(
        'GROQ_API_KEY',
        prefixes=[
            '',
            'RAILWAY_',
            'APP_', 
            'BACKEND_',
            'PRODUCTION_',
            'PROD_',
            'GROQ_',  # Sometimes services prefix with service name
            'LLM_',   # Generic LLM prefix
            'STT_',   # Speech-to-text prefix
        ],
        required=True
    )


def load_elevenlabs_api_key() -> Optional[str]:
    """Load ElevenLabs API key with Railway-specific handling"""
    return load_env_var_robust(
        'ELEVENLABS_API_KEY',
        prefixes=[
            '',
            'RAILWAY_',
            'APP_', 
            'BACKEND_',
            'PRODUCTION_',
            'PROD_',
            'ELEVENLABS_',
            'TTS_',
            'VOICE_',
        ],
        required=False
    )


def load_serpapi_key() -> Optional[str]:
    """Load SerpAPI key with Railway-specific handling"""
    return load_env_var_robust(
        'SERPAPI_API_KEY',
        prefixes=[
            '',
            'RAILWAY_',
            'APP_',
            'BACKEND_', 
            'PRODUCTION_',
            'PROD_',
            'SERPAPI_',
            'SERP_',
            'SEARCH_',
            'GOOGLE_',
        ],
        required=False
    )


def diagnose_env_vars() -> Dict[str, Any]:
    """
    Diagnose environment variable loading issues
    
    Returns:
        Dictionary with diagnostic information
    """
    diagnosis = {
        'platform_info': {
            'is_railway': bool(os.getenv('RAILWAY_PROJECT_ID')),
            'is_heroku': bool(os.getenv('DYNO')),
            'is_vercel': bool(os.getenv('VERCEL')),
            'is_docker': bool(os.getenv('DOCKER_CONTAINER')),
        },
        'env_var_counts': {
            'total_vars': len(os.environ),
            'railway_vars': len([k for k in os.environ.keys() if k.startswith('RAILWAY_')]),
            'api_key_vars': len([k for k in os.environ.keys() if 'API_KEY' in k.upper()]),
        },
        'api_keys_status': {
            'GROQ_API_KEY': bool(load_groq_api_key()),
            'ELEVENLABS_API_KEY': bool(load_elevenlabs_api_key()),
            'SERPAPI_API_KEY': bool(load_serpapi_key()),
        }
    }
    
    return diagnosis


def validate_api_keys() -> List[str]:
    """
    Validate API key format and return list of issues
    
    Returns:
        List of validation issues (empty if all good)
    """
    issues = []
    
    # Check GROQ API key
    groq_key = load_groq_api_key()
    if groq_key:
        if not groq_key.startswith('gsk_'):
            issues.append("GROQ_API_KEY should start with 'gsk_'")
        if len(groq_key) < 20:
            issues.append("GROQ_API_KEY appears too short")
        if groq_key in ['YOUR_GROQ_API_KEY_HERE', 'your_groq_api_key_here']:
            issues.append("GROQ_API_KEY is still a placeholder value")
    else:
        issues.append("GROQ_API_KEY not found")
    
    # Check ElevenLabs API key
    elevenlabs_key = load_elevenlabs_api_key()
    if elevenlabs_key:
        if len(elevenlabs_key) < 20:
            issues.append("ELEVENLABS_API_KEY appears too short")
        if elevenlabs_key in ['YOUR_ELEVENLABS_API_KEY_HERE', 'your_elevenlabs_api_key_here']:
            issues.append("ELEVENLABS_API_KEY is still a placeholder value")
    
    # Check SerpAPI key  
    serpapi_key = load_serpapi_key()
    if serpapi_key:
        if len(serpapi_key) < 20:
            issues.append("SERPAPI_API_KEY appears too short")
        if serpapi_key in ['YOUR_SERPAPI_API_KEY_HERE', 'your_serpapi_api_key_here']:
            issues.append("SERPAPI_API_KEY is still a placeholder value")
    
    return issues