"""
Health check endpoints for production monitoring
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

# Import service clients for health checks
try:
    from src.services.groq_client import GroqClient
    from src.services.tts_service import get_tts_service
    from src.config.settings import settings
except ImportError:
    # Fallback for production environments
    GroqClient = None
    get_tts_service = None
    settings = None

router = APIRouter()


async def check_groq_health() -> Dict[str, Any]:
    """Check Groq API health"""
    try:
        if not settings or not settings.groq.api_key:
            return {"status": "unhealthy", "error": "API key not configured"}
        
        # Simple API call to test connection
        from groq import Groq
        client = Groq(api_key=settings.groq.api_key)
        
        # Test with a minimal completion request
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "health check"}],
            model="gemma2-9b-it",
            max_tokens=5
        )
        
        return {"status": "healthy", "model": "gemma2-9b-it"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_elevenlabs_health() -> Dict[str, Any]:
    """Check ElevenLabs API health"""
    try:
        if not settings or not settings.elevenlabs.api_key:
            return {"status": "unhealthy", "error": "API key not configured"}
        
        from elevenlabs import voices, set_api_key
        set_api_key(settings.elevenlabs.api_key)
        
        # Try to fetch voices (lightweight API call)
        voice_list = voices()
        return {
            "status": "healthy", 
            "voices_available": len(voice_list.voices) if voice_list else 0
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_serpapi_health() -> Dict[str, Any]:
    """Check SerpAPI health"""
    try:
        if not settings or not settings.serpapi.api_key:
            return {"status": "unhealthy", "error": "API key not configured"}
        
        import requests
        
        # Make a simple request to check API availability
        response = requests.get(
            "https://serpapi.com/account",
            params={"api_key": settings.serpapi.api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"status": "healthy", "credits": response.json().get("total_searches_left", "unknown")}
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including external services"""
    start_time = datetime.now()
    
    # Run all health checks concurrently
    results = await asyncio.gather(
        check_groq_health(),
        check_elevenlabs_health(),
        check_serpapi_health(),
        return_exceptions=True
    )
    
    groq_health, elevenlabs_health, serpapi_health = results
    
    # Calculate response time
    response_time = (datetime.now() - start_time).total_seconds()
    
    # Determine overall status
    services_healthy = all(
        isinstance(result, dict) and result.get("status") == "healthy"
        for result in [groq_health, elevenlabs_health, serpapi_health]
    )
    
    overall_status = "healthy" if services_healthy else "degraded"
    
    health_data = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "response_time_seconds": response_time,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0",
        "services": {
            "groq": groq_health if isinstance(groq_health, dict) else {"status": "error", "error": str(groq_health)},
            "elevenlabs": elevenlabs_health if isinstance(elevenlabs_health, dict) else {"status": "error", "error": str(elevenlabs_health)},
            "serpapi": serpapi_health if isinstance(serpapi_health, dict) else {"status": "error", "error": str(serpapi_health)}
        },
        "system": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "environment_vars": {
                "GROQ_API_KEY": "configured" if (os.getenv("GROQ_API_KEY") or settings.groq.api_key) else "missing",
                "ELEVENLABS_API_KEY": "configured" if (os.getenv("ELEVENLABS_API_KEY") or settings.elevenlabs.api_key) else "missing",
                "SERPAPI_API_KEY": "configured" if (os.getenv("SERPAPI_API_KEY") or settings.serpapi.api_key) else "missing",
                "CORS_ORIGINS": "configured" if os.getenv("CORS_ORIGINS") else "missing",
                "SSL_ENABLED": os.getenv("SSL_ENABLED", "false")
            }
        }
    }
    
    # Return appropriate HTTP status code
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=health_data, status_code=status_code)


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes/Docker liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes/Docker readiness probe endpoint"""
    try:
        # Basic checks for readiness
        # Check using settings which now uses robust environment loading
        required_checks = {
            "GROQ_API_KEY": settings.groq.api_key,
            "ELEVENLABS_API_KEY": settings.elevenlabs.api_key
        }
        missing_vars = [var for var, value in required_checks.items() if not value]
        
        if missing_vars:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "error": f"Missing required environment variables: {', '.join(missing_vars)}",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )