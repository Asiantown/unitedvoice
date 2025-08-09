"""
Robust Environment Variable Loader for Deployment Platforms

This module provides robust environment variable loading that handles various
deployment environments including Railway, Heroku, Vercel, and Docker containers.
It includes fallback mechanisms, fuzzy matching, and comprehensive validation.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

# Configure module logger
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


def validate_api_key_format(key: str, key_name: str, expected_prefix: Optional[str] = None, min_length: int = 20) -> List[str]:
    """
    Validate a single API key format.
    
    Args:
        key: API key to validate
        key_name: Name of the API key for error messages
        expected_prefix: Expected key prefix (e.g., 'gsk_' for Groq)
        min_length: Minimum expected key length
        
    Returns:
        List of validation issues for this key
    """
    issues = []
    
    if not key:
        issues.append(f"{key_name} not found")
        return issues
    
    # Check prefix if specified
    if expected_prefix and not key.startswith(expected_prefix):
        issues.append(f"{key_name} should start with '{expected_prefix}'")
    
    # Check length
    if len(key) < min_length:
        issues.append(f"{key_name} appears too short (minimum {min_length} characters)")
    
    # Check for placeholder values
    placeholder_patterns = [
        'YOUR_', 'your_', 'PLACEHOLDER', 'placeholder', 
        'REPLACE', 'replace', 'EXAMPLE', 'example',
        'INSERT', 'insert', 'ADD_HERE', 'add_here'
    ]
    
    if any(pattern in key for pattern in placeholder_patterns):
        issues.append(f"{key_name} appears to be a placeholder value")
    
    # Check for suspicious patterns
    if key.count('_') > 10:  # Too many underscores might indicate malformed key
        issues.append(f"{key_name} has unusual format (too many underscores)")
    
    if not any(c.isalnum() for c in key):
        issues.append(f"{key_name} should contain alphanumeric characters")
    
    return issues


def validate_api_keys() -> List[str]:
    """
    Validate API key formats and return list of issues.
    
    Returns:
        List of validation issues (empty if all valid)
    """
    issues = []
    
    # Validate each API key with specific requirements
    api_keys = [
        (load_groq_api_key(), "GROQ_API_KEY", "gsk_", 20),
        (load_elevenlabs_api_key(), "ELEVENLABS_API_KEY", None, 20),
        (load_serpapi_key(), "SERPAPI_API_KEY", None, 20),
    ]
    
    for key, name, prefix, min_len in api_keys:
        key_issues = validate_api_key_format(key, name, prefix, min_len)
        issues.extend(key_issues)
    
    return issues


def get_environment_summary() -> Dict[str, Any]:
    """
    Get a comprehensive summary of the environment configuration.
    
    Returns:
        Dictionary containing environment summary information
    """
    diagnosis = diagnose_env_vars()
    validation_issues = validate_api_keys()
    
    return {
        "platform": diagnosis["platform_info"],
        "environment_stats": diagnosis["env_var_counts"],
        "api_keys": diagnosis["api_keys_status"],
        "validation_issues": validation_issues,
        "configuration_health": "healthy" if not validation_issues else "issues_found"
    }


def main() -> None:
    """
    Diagnostic tool for environment variable configuration.
    
    Prints comprehensive information about the current environment
    configuration and API key status.
    """
    print("🔧 Environment Configuration Diagnostics")
    print("=" * 50)
    
    # Get comprehensive summary
    summary = get_environment_summary()
    
    # Platform information
    print("\n🏗️  Platform Detection:")
    for platform, detected in summary["platform"].items():
        status = "✅" if detected else "❌"
        print(f"  {status} {platform.replace('is_', '').title()}")
    
    # Environment statistics
    print("\n📊 Environment Variables:")
    stats = summary["environment_stats"]
    print(f"  Total variables: {stats['total_vars']}")
    print(f"  Railway variables: {stats['railway_vars']}")
    print(f"  API key variables: {stats['api_key_vars']}")
    
    # API key status
    print("\n🔑 API Key Status:")
    for key_name, available in summary["api_keys"].items():
        status = "✅ Found" if available else "❌ Missing"
        print(f"  {key_name}: {status}")
    
    # Validation issues
    issues = summary["validation_issues"]
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\n✅ All API keys are properly configured!")
    
    # Overall health
    health = summary["configuration_health"]
    health_emoji = "🟢" if health == "healthy" else "🟡"
    print(f"\n{health_emoji} Configuration Health: {health.replace('_', ' ').title()}")


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()