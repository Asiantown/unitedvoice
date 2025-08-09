#!/usr/bin/env python3
"""
WebSocket Server for United Voice Agent
Handles real-time audio streaming and voice conversation management
"""

import asyncio
import json
import base64
import logging
import tempfile
import os
import re
from typing import Dict, Any, Optional, Set
from datetime import datetime
import wave
import numpy as np
import socketio

from src.core.voice_agent import UnitedVoiceAgent
from src.services.groq_whisper import GroqWhisperClient
from src.services.tts_service import get_tts_service
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Socket.IO server with CORS enabled
from src.services.websocket_config import get_websocket_config
websocket_config = get_websocket_config()

sio = socketio.AsyncServer(
    **websocket_config.get_socket_io_config()
)

# Store active voice agents per session
voice_agents: Dict[str, UnitedVoiceAgent] = {}
session_states: Dict[str, Dict[str, Any]] = {}
# Track recent messages to prevent duplicates
recent_messages: Dict[str, Dict[str, Any]] = {}

# Common Whisper hallucinations to filter out
WHISPER_HALLUCINATIONS: Set[str] = {
    'thank you', 'thanks', 'thank', 'you', 'bye', 'goodbye', 
    'hello', 'hi', 'hey', 'oh', 'okay', 'ok', 'yes', 'no',
    'um', 'uh', 'ah', 'hmm', 'mmm', '.', '...', 
    'please', 'sorry', 'excuse me', 'pardon'
}

# Minimum confidence threshold for accepting transcriptions - REDUCED for better responsiveness
MIN_TRANSCRIPTION_CONFIDENCE = 0.4  # Reduced from 0.7
MIN_TRANSCRIPTION_LENGTH = 2  # Reduced from 3 
MAX_HALLUCINATION_LENGTH = 20  # Increased from 15


def is_duplicate_message(session_id: str, message_type: str, message_text: str) -> bool:
    """Check if this message is a duplicate and track it"""
    import time
    current_time = time.time()
    
    # Initialize session tracking if needed
    if session_id not in recent_messages:
        recent_messages[session_id] = {}
    
    # Clean old messages (older than 5 seconds)
    to_remove = []
    for msg_key, msg_data in recent_messages[session_id].items():
        if current_time - msg_data['timestamp'] > 5:
            to_remove.append(msg_key)
    
    for key in to_remove:
        del recent_messages[session_id][key]
    
    # Create message key
    message_key = f"{message_type}:{hash(message_text)}"
    
    # Check for recent duplicate
    if message_key in recent_messages[session_id]:
        time_diff = current_time - recent_messages[session_id][message_key]['timestamp']
        if time_diff < 2.0:  # Consider duplicates if within 2 seconds
            logger.info(f"🚫 Duplicate {message_type} message filtered for session {session_id}: '{message_text[:50]}...'")
            return True
    
    # Track this message
    recent_messages[session_id][message_key] = {
        'timestamp': current_time,
        'text': message_text
    }
    
    return False


class WebSocketVoiceAgent:
    """WebSocket-enabled voice agent for real-time communication"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        try:
            self.voice_agent = UnitedVoiceAgent()
        except Exception as e:
            logger.error(f"Failed to initialize UnitedVoiceAgent: {e}")
            # Use mock agent as fallback
            from src.services.mock_agent import MockVoiceAgent
            self.voice_agent = MockVoiceAgent()
            logger.warning("Using MockVoiceAgent - API keys not configured")
        
        try:
            # Use robust environment loading for fallback
            from ..utils.env_loader import load_groq_api_key
            api_key = settings.groq.api_key or load_groq_api_key()
            if api_key:
                self.whisper_client = GroqWhisperClient(api_key=api_key)
            else:
                logger.warning("GROQ_API_KEY not found - transcription disabled")
                self.whisper_client = None
        except Exception as e:
            logger.error(f"Failed to initialize WhisperClient: {e}")
            self.whisper_client = None
        
        # Initialize TTS service
        self.tts_service = get_tts_service()
        logger.info(f"TTS service initialized: {self.tts_service.is_available()}")
        
        # Remove the main loop audio recording - we'll handle streaming audio
        self.voice_agent.record_audio = None
        self.voice_agent.transcribe_audio = self.transcribe_streaming_audio
        
        logger.info(f"WebSocket voice agent initialized for session {session_id}")
    
    def is_likely_hallucination(self, text: str) -> bool:
        """Check if transcribed text is likely a Whisper hallucination - REDUCED filtering"""
        if not text or len(text.strip()) == 0:
            return True
            
        # Clean and normalize the text
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower().strip())
        
        # Check if it's too short to be meaningful - MORE LENIENT
        if len(cleaned_text) < MIN_TRANSCRIPTION_LENGTH:
            logger.info(f"⚠️ Rejecting transcription (too short): '{text}'")
            return True
            
        # Check if it's a short phrase that's likely a hallucination - MORE SELECTIVE 
        if len(cleaned_text) <= MAX_HALLUCINATION_LENGTH:
            # Only check against most obvious hallucinations
            obvious_hallucinations = {'thank you', 'thanks', 'bye', 'goodbye', 'um', 'uh', 'ah', 'hmm'}
            if cleaned_text in obvious_hallucinations:
                logger.info(f"⚠️ Rejecting obvious hallucination: '{text}'")
                return True
                
            # Check for single word obvious repetitions only
            words = cleaned_text.split()
            if len(words) == 1 and words[0] in obvious_hallucinations:
                logger.info(f"⚠️ Rejecting single word obvious hallucination: '{text}'")
                return True
                
            # Only reject if it's exactly the same word repeated 3+ times
            if len(words) >= 3 and len(set(words)) == 1 and words[0] in obvious_hallucinations:
                logger.info(f"⚠️ Rejecting repeated obvious hallucination: '{text}'")
                return True
        
        # Check for patterns that indicate noise transcription - ONLY most obvious noise
        noise_patterns = [
            r'^[\s\.\,\!\?]+$',  # Only punctuation and whitespace
            r'^(uh|um|ah|mm|hmm)\s*$',  # Common filler words alone
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, cleaned_text, re.IGNORECASE):
                logger.info(f"⚠️ Rejecting noise pattern '{pattern}': '{text}'")
                return True
                
        return False
    
    async def transcribe_streaming_audio(self, audio_data: bytes, audio_format: str = 'webm') -> str:
        """Transcribe streaming audio data with hallucination filtering"""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe using Groq Whisper
                transcription = self.whisper_client.transcribe_audio_file(
                    temp_file_path,
                    language="en"
                )
                
                if not transcription or not transcription.strip():
                    logger.info(f"Empty transcription for session {self.session_id}")
                    return ""
                
                # Check if it's likely a hallucination
                if self.is_likely_hallucination(transcription):
                    logger.info(f"Filtered hallucination for session {self.session_id}: '{transcription}'")
                    return ""
                
                logger.info(f"Accepted transcription: '{transcription}' for session {self.session_id}")
                return transcription
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Transcription error for session {self.session_id}: {e}")
            return ""
    
    async def process_voice_input(self, transcribed_text: str) -> str:
        """Process voice input and return agent response"""
        try:
            # Get response from voice agent
            response = self.voice_agent.get_response(transcribed_text)
            logger.info(f"Agent response for session {self.session_id}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error processing voice input for session {self.session_id}: {e}")
            return "I'm sorry, I encountered an error processing your request. Could you please try again?"
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return {
            'booking_state': self.voice_agent.booking_flow.state.value,
            'booking_info': self.voice_agent.booking_flow.booking_info.to_dict(),
            'conversation_length': len(self.voice_agent.conversation_history)
        }


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")
    
    # Initialize voice agent for this session
    voice_agents[sid] = WebSocketVoiceAgent(sid)
    session_states[sid] = {
        'connected_at': datetime.utcnow().isoformat(),
        'status': 'connected'
    }
    
    # Send connection confirmation
    await sio.emit('connected', {
        'session_id': sid,
        'message': 'Connected to United Voice Agent',
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)
    
    # Automatic greeting removed - waiting for user to initiate conversation
    logger.info(f"Session {sid} connected and ready for user to start conversation")


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")
    
    # Clean up session data
    if sid in voice_agents:
        del voice_agents[sid]
    if sid in session_states:
        del session_states[sid]
    if sid in recent_messages:
        del recent_messages[sid]


@sio.event
async def audio_data(sid, data):
    """Handle incoming audio data"""
    try:
        if sid not in voice_agents:
            await sio.emit('error', {'message': 'Session not found'}, room=sid)
            return
        
        voice_agent = voice_agents[sid]
        
        # Extract audio data
        audio_base64 = data.get('audio')
        audio_format = data.get('format', 'webm')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        
        if not audio_base64:
            await sio.emit('error', {'message': 'No audio data provided'}, room=sid)
            return
        
        logger.info(f"Received audio data from session {sid} (format: {audio_format})")
        
        # Update session status
        session_states[sid]['status'] = 'processing_audio'
        await sio.emit('status_update', {
            'status': 'processing', 
            'message': 'Processing your audio...'
        }, room=sid)
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Transcribe audio
        transcription = await voice_agent.transcribe_streaming_audio(audio_bytes, audio_format)
        
        # Additional validation after transcription - MUCH MORE LENIENT
        if transcription and transcription.strip():
            # Final check for edge cases that might have passed initial filtering
            cleaned_transcription = transcription.strip()
            
            # Log the transcription for debugging
            logger.info(f"✅ Processing transcription: '{cleaned_transcription}' (length: {len(cleaned_transcription)})")
            
            # Only check for completely empty content
            if len(cleaned_transcription) < 1:
                logger.info(f"❌ Transcription completely empty: '{cleaned_transcription}'")
                transcription = ""
        
        if transcription and transcription.strip():
            # Calculate a basic confidence score - MUCH MORE LENIENT
            confidence = 0.9  # Default confidence
            
            # Only reduce confidence for extremely short transcriptions
            if len(transcription.strip()) < 3:
                confidence *= 0.9  # Reduced penalty
            
            # Remove the aggressive filtering for common words
            # Users might actually say "thank you" legitimately
                
            # Only proceed if confidence meets threshold (now much lower)
            if confidence >= MIN_TRANSCRIPTION_CONFIDENCE:
                # Check for duplicate transcription before sending
                if not is_duplicate_message(sid, 'transcription', transcription):
                    # Send transcription back to client
                    await sio.emit('transcription', {
                        'text': transcription,
                        'confidence': confidence,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=sid)
            else:
                logger.info(f"⚠️ Transcription rejected due to low confidence ({confidence:.2f}): '{transcription}'")
                await sio.emit('error', {
                    'message': f'Audio confidence too low ({confidence:.2f}). Please speak more clearly.',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                session_states[sid]['status'] = 'idle'
                return
            
            # Process with voice agent
            session_states[sid]['status'] = 'generating_response'
            await sio.emit('status_update', {
                'status': 'thinking', 
                'message': 'Thinking...'
            }, room=sid)
            
            agent_response = await voice_agent.process_voice_input(transcription)
            
            # Get conversation state
            conversation_state = voice_agent.get_conversation_state()
            
            # Update session status for TTS
            session_states[sid]['status'] = 'generating_speech'
            await sio.emit('status_update', {
                'status': 'speaking', 
                'message': 'Generating speech...'
            }, room=sid)
            
            # Generate speech audio
            audio_data = None
            try:
                if voice_agent.tts_service.is_available():
                    logger.info(f"Generating TTS for: '{agent_response[:50]}...'")
                    audio_bytes = await voice_agent.tts_service.synthesize_speech_async(agent_response)
                    
                    if audio_bytes:
                        # Convert to base64 for transmission
                        audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                        logger.info(f"TTS generated successfully, size: {len(audio_bytes)} bytes")
                    else:
                        logger.warning("TTS generation returned no audio")
                else:
                    logger.warning("TTS service not available")
            except Exception as tts_error:
                logger.error(f"TTS generation failed: {tts_error}")
            
            # Check for duplicate response before sending
            if not is_duplicate_message(sid, 'agent_response', agent_response):
                # Send agent response with audio
                response_data = {
                    'text': agent_response,
                    'intent': conversation_state.get('booking_state', 'unknown'),
                    'entities': {},
                    'conversation_state': conversation_state,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Add audio if available
                if audio_data:
                    response_data['audio'] = audio_data
                    response_data['audio_format'] = 'mp3'  # ElevenLabs uses MP3
                
                await sio.emit('agent_response', response_data, room=sid)
            else:
                logger.info(f"Duplicate agent response blocked for session {sid}")
            
            session_states[sid]['status'] = 'idle'
            await sio.emit('status_update', {
                'status': 'idle',
                'message': 'Ready for next input'
            }, room=sid)
            
        else:
            # No transcription found or filtered out
            logger.info(f"⚠️ No valid transcription for session {sid}")
            await sio.emit('error', {
                'message': 'No speech detected or audio was filtered. Please speak clearly and try again.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            session_states[sid]['status'] = 'idle'
        
    except Exception as e:
        logger.error(f"Error processing audio data for session {sid}: {e}")
        await sio.emit('error', {
            'message': 'Error processing audio data',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, room=sid)
        
        if sid in session_states:
            session_states[sid]['status'] = 'error'


@sio.event
async def get_session_state(sid):
    """Get current session state"""
    if sid in voice_agents:
        state = voice_agents[sid].get_conversation_state()
        await sio.emit('session_state', state, room=sid)
    else:
        await sio.emit('error', {'message': 'Session not found'}, room=sid)


@sio.event
async def reset_conversation(sid):
    """Reset the conversation for a session"""
    if sid in voice_agents:
        # Recreate the voice agent
        voice_agents[sid] = WebSocketVoiceAgent(sid)
        session_states[sid]['status'] = 'reset'
        
        await sio.emit('conversation_reset', {
            'message': 'Conversation reset successfully',
            'timestamp': datetime.utcnow().isoformat()
        }, room=sid)
        
        # Automatic greeting removed after reset - waiting for user to start conversation
        logger.info(f"Session {sid} reset and ready for user to start conversation")
    else:
        await sio.emit('error', {'message': 'Session not found'}, room=sid)


# Health check endpoint for monitoring
@sio.event
async def health_check(sid):
    """Health check endpoint"""
    await sio.emit('health_response', {
        'status': 'healthy',
        'active_sessions': len(voice_agents),
        'timestamp': datetime.utcnow().isoformat()
    }, room=sid)


# Create ASGI app
def create_websocket_app():
    """Create and configure the WebSocket ASGI application"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from src.api.http_server import app as http_app
    
    # Use the HTTP app as the base and add WebSocket support
    app = http_app
    app.title = "United Voice Agent - WebSocket + HTTP Server"
    app.description = "Combined WebSocket and HTTP API for United Voice Agent"
    
    # Mount Socket.IO
    from socketio import ASGIApp
    socket_app = ASGIApp(sio, app)
    
    return socket_app


if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_websocket_app()
    
    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True
    )