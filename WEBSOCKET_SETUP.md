# WebSocket Integration Setup Guide

This guide explains how to set up the WebSocket integration between the Next.js frontend and Python backend for the United Airlines voice agent.

## Architecture Overview

The system consists of:

1. **Python Backend** - FastAPI + Socket.IO server handling:
   - WebSocket connections
   - Audio transcription (Groq Whisper)
   - Voice agent conversations
   - HTTP API endpoints

2. **Next.js Frontend** - React application with:
   - WebSocket client (Socket.IO)
   - Audio recording interface
   - Real-time transcription display
   - HTTP fallback support

## Connection Flow

```
Frontend (Next.js) ←→ WebSocket ←→ Backend (Python/FastAPI)
       ↓                                    ↓
   Audio Recording                    Groq Whisper
       ↓                                    ↓
   Base64 Encoding                    Transcription
       ↓                                    ↓
   Socket.IO Message              Voice Agent Response
```

## Quick Start

### 1. Backend Setup

```bash
cd /Users/ryanyin/united-voice-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# GROQ_API_KEY=your_groq_api_key
# ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Start WebSocket server
./start-websocket-server.sh
```

The backend will be available at:
- WebSocket: `ws://localhost:8000`
- HTTP API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd /Users/ryanyin/united-voice-agent/frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# The default configuration should work for local development

# Start development server
./start-frontend.sh
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)
```bash
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_BACKEND_HTTP_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_WEBSOCKET_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_VOICE_RECORDING=true
NEXT_PUBLIC_DEBUG=true
```

## Files Created/Modified

### Python Backend

**New Files:**
- `src/services/websocket_server.py` - WebSocket server with Socket.IO
- `src/api/http_server.py` - HTTP API endpoints
- `websocket_main.py` - Main server entry point
- `start-websocket-server.sh` - Startup script

**Modified Files:**
- `pyproject.toml` - Added WebSocket dependencies

### Next.js Frontend

**New Files:**
- `src/app/api/websocket/route.ts` - WebSocket info endpoint
- `src/app/api/audio/upload/route.ts` - HTTP audio upload fallback
- `src/app/api/health/route.ts` - Health check endpoint
- `.env.local` - Environment variables
- `.env.example` - Environment template
- `start-frontend.sh` - Startup script

**Modified Files:**
- `src/lib/config.ts` - Added environment variable support
- `src/hooks/useSocket.ts` - Enhanced WebSocket functionality
- `src/components/voice/VoiceInterface.tsx` - Updated audio handling

## WebSocket Events

### Client → Server
- `audio_data` - Send audio for transcription
- `get_session_state` - Request conversation state
- `reset_conversation` - Reset the conversation
- `health_check` - Check server health

### Server → Client
- `connected` - Connection established
- `transcription` - Audio transcription result
- `agent_response` - Voice agent response
- `status_update` - Processing status updates
- `conversation_reset` - Conversation reset confirmation
- `error` - Error messages

## Audio Streaming Process

1. **Frontend Records Audio**
   - Uses `MediaRecorder` API
   - Records in WebM format
   - Collects audio chunks

2. **Audio Encoding**
   - Converts Blob to Base64
   - Sends via WebSocket with metadata

3. **Backend Processing**
   - Receives Base64 audio
   - Saves to temporary file
   - Transcribes with Groq Whisper
   - Processes with voice agent

4. **Response Flow**
   - Sends transcription back to frontend
   - Generates agent response
   - Returns response with metadata

## HTTP Fallback

If WebSocket is unavailable, the system falls back to HTTP:
- Frontend uploads audio to `/api/audio/upload`
- Next.js API routes proxy to Python backend
- Response sent back via HTTP

## Testing the Integration

### 1. Health Check
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000/api/health
```

### 2. WebSocket Connection
1. Open browser to `http://localhost:3000`
2. Check browser console for connection logs
3. Should see "Connected to voice agent" message

### 3. Audio Recording
1. Click the microphone button
2. Speak for a few seconds
3. Check for transcription in the chat
4. Verify agent response

### 4. Debug Mode
Enable debug mode in `.env.local`:
```bash
NEXT_PUBLIC_DEBUG=true
```

This will log all WebSocket events to the browser console.

## Troubleshooting

### WebSocket Connection Issues
1. Check if backend is running on port 8000
2. Verify CORS settings in `websocket_server.py`
3. Check browser console for connection errors
4. Try HTTP fallback mode

### Audio Recording Issues
1. Check microphone permissions in browser
2. Verify audio recording format support
3. Check browser compatibility (Chrome recommended)
4. Test with different audio devices

### Transcription Issues
1. Verify GROQ_API_KEY is set correctly
2. Check audio quality and volume
3. Test with different speech patterns
4. Monitor backend logs for errors

## Development Tips

1. **Use Debug Mode** - Enable verbose logging
2. **Monitor Network Tab** - Check WebSocket messages
3. **Test Fallback** - Disable WebSocket to test HTTP mode
4. **Audio Quality** - Use good microphone for better transcription
5. **Error Handling** - Check both frontend and backend logs

## Production Deployment

For production deployment:
1. Update environment variables for production URLs
2. Use proper SSL certificates for WSS connections
3. Configure production-grade server (nginx, etc.)
4. Set up proper logging and monitoring
5. Implement rate limiting and authentication

## API Endpoints

### Backend HTTP API
- `GET /health` - Health check
- `POST /api/transcribe` - Transcribe base64 audio
- `POST /api/transcribe/file` - Transcribe uploaded file
- `GET /api/config` - Get API configuration
- `GET /docs` - API documentation

### Frontend API Routes
- `GET /api/health` - Frontend health check
- `GET /api/websocket` - WebSocket connection info
- `POST /api/audio/upload` - Audio upload fallback

## Next Steps

1. Add authentication for production use
2. Implement rate limiting
3. Add monitoring and analytics
4. Optimize audio compression
5. Add support for multiple languages
6. Implement conversation persistence