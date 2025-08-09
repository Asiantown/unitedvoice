# United Voice Agent Backend API Documentation

## 🚀 Quick Start

### Required Environment Variables
```bash
# Required API Keys
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
```

### Start the Backend Server
```bash
# Using UV (recommended)
uv run python start_websocket_fixed.py

# Or directly with Python
python start_websocket_fixed.py
```

Server will run on: **http://localhost:8000**

---

## 📡 WebSocket/Socket.IO API

### Connection

Connect to the Socket.IO server:
```javascript
const socket = io('http://localhost:8000', {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});
```

### WebSocket Events

#### Client → Server Events

| Event | Description | Payload | Response |
|-------|-------------|---------|----------|
| `audio_data` | Send audio for transcription | `{ audio: base64String, format: 'webm', timestamp: ISO8601, size: number }` | `transcription` event |
| `health_check` | Request server health status | None | `health_response` event |
| `get_session_state` | Get current session state | None | `session_state` event |
| `reset_conversation` | Reset conversation context | None | `conversation_reset` event |

#### Server → Client Events

| Event | Description | Payload |
|-------|-------------|---------|
| `connect` | Socket.IO connection established | Socket ID |
| `connected` | Custom connection confirmation | `{ session_id: string, message: string, timestamp: ISO8601 }` |
| `agent_response` | AI agent response with audio | `{ text: string, intent: string, entities: {}, audio?: base64String, audio_format?: 'mp3', timestamp: ISO8601 }` |
| `transcription` | Audio transcription result | `{ text: string, confidence: float, timestamp: ISO8601 }` |
| `status_update` | Processing status updates | `{ status: 'processing'|'thinking'|'speaking'|'idle', message: string }` |
| `error` | Error messages | `{ message: string, details?: string, timestamp: ISO8601 }` |
| `health_response` | Health check response | `{ status: string, active_sessions: number, timestamp: ISO8601 }` |
| `session_state` | Current session state | `{ booking_state: string, booking_info: {}, conversation_length: number }` |
| `conversation_reset` | Conversation reset confirmation | `{ message: string, timestamp: ISO8601 }` |

### WebSocket Flow Example

```javascript
// 1. Connect
socket.on('connect', () => {
  console.log('Connected:', socket.id);
});

// 2. Receive greeting
socket.on('connected', (data) => {
  console.log('Server greeting:', data.message);
});

// 3. Receive initial agent message
socket.on('agent_response', (data) => {
  console.log('Agent says:', data.text);
  if (data.audio) {
    // Play audio: data.audio is base64 MP3
    playAudio(data.audio);
  }
});

// 4. Send audio for transcription
const audioBlob = await recordAudio(); // Your recording logic
const reader = new FileReader();
reader.onload = () => {
  const base64Audio = reader.result.split(',')[1];
  socket.emit('audio_data', {
    audio: base64Audio,
    format: 'webm',
    timestamp: new Date().toISOString(),
    size: audioBlob.size
  });
};
reader.readAsDataURL(audioBlob);

// 5. Receive transcription
socket.on('transcription', (data) => {
  console.log('You said:', data.text);
});

// 6. Receive agent response
socket.on('agent_response', (data) => {
  console.log('Agent response:', data.text);
});

// 7. Handle status updates
socket.on('status_update', (data) => {
  console.log('Status:', data.status, data.message);
});
```

---

## 🌐 HTTP REST API

### Base URL
`http://localhost:8000`

### Endpoints

#### 1. Health Check
- **GET** `/health`
- **Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T08:11:07.996560",
  "active_sessions": 0,
  "services": {
    "whisper": "available",
    "groq": "available",
    "elevenlabs": "available"
  }
}
```

#### 2. Root Endpoint
- **GET** `/`
- **Response:**
```json
{
  "message": "United Voice Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "websocket": "Connect to /socket.io/ for real-time communication"
}
```

#### 3. Audio Transcription (Base64)
- **POST** `/api/transcribe`
- **Content-Type:** `application/json`
- **Body:**
```json
{
  "audio": "base64_encoded_audio_string",
  "format": "webm",
  "timestamp": "2025-08-08T12:00:00Z"
}
```
- **Response:**
```json
{
  "success": true,
  "transcription": "Hello, I want to book a flight",
  "confidence": 0.95,
  "timestamp": "2025-08-08T12:00:01Z"
}
```

#### 4. Audio Transcription (File Upload)
- **POST** `/api/transcribe/file`
- **Content-Type:** `multipart/form-data`
- **Body:** Audio file (webm, wav, mp3, etc.)
- **Response:**
```json
{
  "success": true,
  "transcription": "Hello, I want to book a flight",
  "confidence": 0.95,
  "format": "webm",
  "size": 102400,
  "timestamp": "2025-08-08T12:00:01Z"
}
```

#### 5. Configuration
- **GET** `/api/config`
- **Response:**
```json
{
  "websocket": {
    "enabled": true,
    "url": "ws://localhost:8000",
    "transports": ["websocket", "polling"]
  },
  "audio": {
    "supported_formats": ["webm", "wav", "mp3", "ogg"],
    "max_size": 10485760,
    "sample_rate": 16000
  },
  "features": {
    "transcription": true,
    "tts": true,
    "voice_agent": true
  }
}
```

---

## 🎤 Audio Processing

### Supported Audio Formats
- WebM (recommended for browser recording)
- WAV
- MP3
- OGG

### Audio Recording Settings (Browser)
```javascript
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  }
});

const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus'
});
```

### Audio Data Flow
1. **Recording** → Browser MediaRecorder API
2. **Encoding** → Base64 string
3. **Transmission** → WebSocket or HTTP POST
4. **Transcription** → Groq Whisper API
5. **Processing** → Voice Agent (LLM)
6. **TTS** → ElevenLabs or pyttsx3
7. **Response** → Base64 MP3 audio

---

## 🔧 Frontend Integration Guide

### 1. Install Socket.IO Client
```bash
npm install socket.io-client
```

### 2. Create WebSocket Service
```javascript
// websocket.service.js
import io from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
  }

  connect() {
    this.socket = io('http://localhost:8000', {
      transports: ['websocket', 'polling'],
      reconnection: true
    });

    this.socket.on('connect', () => {
      this.isConnected = true;
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      this.isConnected = false;
      console.log('WebSocket disconnected');
    });

    return this.socket;
  }

  sendAudio(audioBlob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Audio = reader.result.split(',')[1];
        this.socket.emit('audio_data', {
          audio: base64Audio,
          format: 'webm',
          timestamp: new Date().toISOString(),
          size: audioBlob.size
        });
        resolve();
      };
      reader.onerror = reject;
      reader.readAsDataURL(audioBlob);
    });
  }

  onTranscription(callback) {
    this.socket.on('transcription', callback);
  }

  onAgentResponse(callback) {
    this.socket.on('agent_response', callback);
  }

  onStatusUpdate(callback) {
    this.socket.on('status_update', callback);
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}

export default new WebSocketService();
```

### 3. Audio Recording Service
```javascript
// audio.service.js
class AudioService {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
  }

  async startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    this.audioChunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };

    this.mediaRecorder.start(100); // Collect data every 100ms
  }

  stopRecording() {
    return new Promise((resolve) => {
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        resolve(audioBlob);
      };
      this.mediaRecorder.stop();
    });
  }

  playAudio(base64Audio) {
    const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
    return audio.play();
  }
}

export default new AudioService();
```

### 4. React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import WebSocketService from './services/websocket.service';
import AudioService from './services/audio.service';

function VoiceAgent() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [agentMessage, setAgentMessage] = useState('');
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    // Connect to WebSocket
    const socket = WebSocketService.connect();

    // Set up event listeners
    WebSocketService.onTranscription((data) => {
      setTranscript(data.text);
    });

    WebSocketService.onAgentResponse((data) => {
      setAgentMessage(data.text);
      if (data.audio) {
        AudioService.playAudio(data.audio);
      }
    });

    WebSocketService.onStatusUpdate((data) => {
      setStatus(data.status);
    });

    return () => {
      WebSocketService.disconnect();
    };
  }, []);

  const handleRecord = async () => {
    if (!isRecording) {
      await AudioService.startRecording();
      setIsRecording(true);
    } else {
      const audioBlob = await AudioService.stopRecording();
      setIsRecording(false);
      await WebSocketService.sendAudio(audioBlob);
    }
  };

  return (
    <div>
      <h1>United Voice Agent</h1>
      <button onClick={handleRecord}>
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
      <div>Status: {status}</div>
      <div>You said: {transcript}</div>
      <div>Agent: {agentMessage}</div>
    </div>
  );
}

export default VoiceAgent;
```

---

## 🔒 CORS Configuration

The backend allows connections from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`
- `https://localhost:3000`
- `https://localhost:3001`

To add more origins, modify `src/services/websocket_server.py`:
```python
cors_allowed_origins=[
    "http://localhost:3000",
    "http://your-frontend-domain.com",
    # Add more origins here
]
```

---

## 🧪 Testing

### Test WebSocket Connection
```bash
# Install wscat
npm install -g wscat

# Test connection
wscat -c ws://localhost:8000/socket.io/?EIO=4&transport=websocket
```

### Test HTTP Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Configuration
curl http://localhost:8000/api/config

# Socket.IO polling
curl "http://localhost:8000/socket.io/?EIO=4&transport=polling"
```

### Test with Python
```python
import socketio
import asyncio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connected to server')

@sio.event
async def agent_response(data):
    print(f"Agent: {data['text']}")

async def main():
    await sio.connect('http://localhost:8000')
    await sio.wait()

asyncio.run(main())
```

---

## 📊 Response Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid audio data) |
| 413 | File too large |
| 415 | Unsupported media type |
| 500 | Internal server error |

---

## 🛠️ Troubleshooting

### Common Issues

1. **"Not connected to server" error**
   - Ensure backend is running: `uv run python start_websocket_fixed.py`
   - Check port 8000 is available: `lsof -i :8000`

2. **CORS errors**
   - Add your frontend URL to `cors_allowed_origins` in `websocket_server.py`

3. **Audio not transcribing**
   - Check GROQ_API_KEY is set in .env
   - Verify audio format is supported (webm, wav, mp3)

4. **TTS not working**
   - Check ELEVENLABS_API_KEY is set
   - Note: Falls back to pyttsx3 if quota exceeded

---

## 📦 Dependencies

Backend requires:
- Python 3.8+
- UV package manager
- See `pyproject.toml` for full list

Key packages:
- `python-socketio==5.11.0`
- `fastapi`
- `uvicorn`
- `groq`
- `elevenlabs`
- `pyttsx3`

---

## 🚀 Production Deployment

For production, consider:
1. Use environment variables for API keys (never commit them)
2. Set up proper CORS origins
3. Use HTTPS/WSS for secure connections
4. Implement rate limiting
5. Add authentication/authorization
6. Monitor API quotas (ElevenLabs, Groq)

---

## 📝 License & Support

This backend is part of the United Voice Agent project.
For issues or questions, refer to the main README.md file.