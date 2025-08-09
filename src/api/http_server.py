#!/usr/bin/env python3
"""
HTTP API endpoints for United Voice Agent
Provides REST API support alongside WebSocket functionality
"""

import base64
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.groq_whisper import GroqWhisperClient
from src.services.tts_service import get_tts_service
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models
class AudioTranscriptionRequest(BaseModel):
    audio: str  # Base64 encoded audio
    format: str = "webm"
    timestamp: str = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"

class TTSResponse(BaseModel):
    audio: str  # Base64 encoded audio
    format: str = "mp3"
    duration: float = 0

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    active_sessions: int = 0
    services: Dict[str, str]

# Create FastAPI app
app = FastAPI(
    title="United Voice Agent API",
    description="HTTP API for United Voice Agent with audio transcription support",
    version="1.0.0"
)

# Add CORS middleware with environment-based configuration
def get_cors_origins():
    """Get CORS origins based on environment"""
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # Get production origins from environment variable
        cors_origins = os.getenv('CORS_ORIGINS', '').split(',')
        cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
        
        # Default production origins if none specified
        if not cors_origins:
            cors_origins = [
                "https://*.vercel.app",
                "https://*.herokuapp.com",
                "https://*.railway.app",
                "https://*.render.com"
            ]
        return cors_origins
    else:
        # Development origins
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Whisper client
whisper_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global whisper_client
    try:
        # Use robust environment loading for fallback
        from ..utils.env_loader import load_groq_api_key
        groq_api_key = settings.groq.api_key or load_groq_api_key()
        if groq_api_key:
            whisper_client = GroqWhisperClient(api_key=groq_api_key)
            logger.info("Whisper client initialized successfully")
        else:
            logger.warning("GROQ_API_KEY not found - transcription will not work")
    except Exception as e:
        logger.error(f"Failed to initialize Whisper client: {e}")

# Initialize whisper client at startup
def init_services():
    """Initialize services"""
    global whisper_client
    try:
        # Use robust environment loading for fallback
        from ..utils.env_loader import load_groq_api_key
        groq_api_key = settings.groq.api_key or load_groq_api_key()
        if groq_api_key:
            whisper_client = GroqWhisperClient(api_key=groq_api_key)
            logger.info("Whisper client initialized successfully")
        else:
            logger.warning("GROQ_API_KEY not found - transcription will not work")
    except Exception as e:
        logger.error(f"Failed to initialize Whisper client: {e}")

# Initialize services immediately
try:
    init_services()
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")

# Include comprehensive health endpoints
from src.api.health import router as health_router
app.include_router(health_router)

@app.get("/health", response_model=HealthResponse)
async def basic_health_check():
    """Basic health check endpoint for backward compatibility"""
    services = {
        "whisper": "available" if whisper_client else "unavailable",
        "groq": "available" if (settings.groq.api_key or os.getenv('GROQ_API_KEY')) else "unavailable",
        "elevenlabs": "available" if (settings.elevenlabs.api_key or os.getenv('ELEVENLABS_API_KEY')) else "unavailable"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )

@app.post("/api/transcribe")
async def transcribe_audio(request: AudioTranscriptionRequest):
    """Transcribe audio from base64 encoded data"""
    if not whisper_client:
        raise HTTPException(status_code=503, detail="Transcription service unavailable")
    
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{request.format}', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using Groq Whisper
            transcription = whisper_client.transcribe_audio_file(
                temp_file_path,
                language="en"
            )
            
            logger.info(f"Transcribed: '{transcription}'")
            
            return {
                "transcription": transcription,
                "confidence": 0.9,  # Placeholder confidence
                "timestamp": datetime.utcnow().isoformat(),
                "format": request.format
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/transcribe/file")
async def transcribe_audio_file(audio: UploadFile = File(...)):
    """Transcribe audio from uploaded file"""
    if not whisper_client:
        raise HTTPException(status_code=503, detail="Transcription service unavailable")
    
    try:
        # Read file content
        audio_content = await audio.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{audio.content_type.split("/")[-1]}', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using Groq Whisper
            transcription = whisper_client.transcribe_audio_file(
                temp_file_path,
                language="en"
            )
            
            logger.info(f"Transcribed file '{audio.filename}': '{transcription}'")
            
            return {
                "transcription": transcription,
                "confidence": 0.9,
                "timestamp": datetime.utcnow().isoformat(),
                "filename": audio.filename,
                "content_type": audio.content_type
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"File transcription failed: {str(e)}")

@app.post("/api/tts", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech from text"""
    try:
        tts_service = get_tts_service()
        
        if not tts_service.is_available():
            raise HTTPException(status_code=503, detail="TTS service unavailable")
        
        # Synthesize speech
        audio_bytes = await tts_service.synthesize_speech_async(request.text)
        
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return TTSResponse(
            audio=audio_base64,
            format="mp3",
            duration=0  # Could calculate this if needed
        )
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

@app.get("/api/config")
async def get_configuration():
    """Get API configuration information"""
    return {
        "websocket": {
            "available": True,
            "endpoint": "/socket.io/",
            "protocols": ["socket.io"]
        },
        "http": {
            "transcribe": "/api/transcribe",
            "transcribe_file": "/api/transcribe/file",
            "health": "/health"
        },
        "audio": {
            "supported_formats": ["webm", "wav", "mp3", "ogg"],
            "max_duration": 30,  # seconds
            "sample_rate": 16000
        },
        "features": {
            "real_time_transcription": True,
            "conversation_memory": True,
            "flight_booking": True,
            "voice_synthesis": True
        }
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "United Voice Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "Connect to /socket.io/ for real-time communication"
    }