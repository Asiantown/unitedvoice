# API Reference

## WebSocket API

The primary interface for real-time voice interactions uses Socket.IO WebSocket protocol.

### Connection

#### Endpoint
```javascript
// Production
wss://united-voice-agent.up.railway.app

// Development
ws://localhost:8000
```

#### Connection Options
```javascript
const socket = io(ENDPOINT, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 20000
});
```

### Events

#### Client → Server

##### `audio_data`
Send audio data for transcription and processing.

```typescript
// Request
socket.emit('audio_data', {
    audio: string,      // Base64 encoded audio
    format: string,     // Audio format: 'webm' | 'wav' | 'mp3'
    timestamp: number   // Unix timestamp
});

// Example
socket.emit('audio_data', {
    audio: 'SGVsbG8gV29ybGQh...',
    format: 'webm',
    timestamp: Date.now()
});
```

##### `get_session_state`
Request current conversation state.

```typescript
// Request
socket.emit('get_session_state');

// Response via 'session_state' event
{
    booking_state: string,
    booking_info: BookingInfo,
    conversation_length: number
}
```

##### `reset_conversation`
Reset the conversation to start fresh.

```typescript
// Request
socket.emit('reset_conversation');

// Response via 'conversation_reset' event
{
    message: string,
    timestamp: string
}
```

##### `health_check`
Check server health status.

```typescript
// Request
socket.emit('health_check');

// Response via 'health_response' event
{
    status: 'healthy' | 'degraded' | 'unhealthy',
    active_sessions: number,
    timestamp: string
}
```

#### Server → Client

##### `connected`
Emitted when client successfully connects.

```typescript
// Response
{
    session_id: string,
    message: string,
    timestamp: string
}

// Example
{
    session_id: 'abc123xyz',
    message: 'Connected to United Voice Agent',
    timestamp: '2025-08-10T12:00:00Z'
}
```

##### `transcription`
Real-time transcription of user speech.

```typescript
// Response
{
    text: string,
    confidence: number,
    timestamp: string
}

// Example
{
    text: "I need a flight to New York",
    confidence: 0.95,
    timestamp: '2025-08-10T12:00:01Z'
}
```

##### `agent_response`
AI agent's response with optional audio.

```typescript
// Response
{
    text: string,
    audio?: string,           // Base64 encoded MP3
    audio_format?: string,
    intent?: string,
    entities?: object,
    conversation_state?: object,
    timestamp: string
}

// Example
{
    text: "Great! Which city are you flying from?",
    audio: "UklGRiQAAABXQVZFZm10...",
    audio_format: "mp3",
    intent: "collecting_departure",
    entities: {
        destination_city: "New York"
    },
    conversation_state: {
        booking_state: "collecting_departure",
        booking_info: {
            destination: "New York"
        }
    },
    timestamp: '2025-08-10T12:00:02Z'
}
```

##### `status_update`
Processing status updates.

```typescript
// Response
{
    status: 'processing' | 'thinking' | 'speaking' | 'idle',
    message: string
}

// Example
{
    status: 'processing',
    message: 'Processing your audio...'
}
```

##### `error`
Error notifications.

```typescript
// Response
{
    message: string,
    details?: string,
    timestamp: string
}

// Example
{
    message: 'Audio processing failed',
    details: 'Invalid audio format',
    timestamp: '2025-08-10T12:00:03Z'
}
```

## REST API

HTTP endpoints for non-realtime operations.

### Base URL
```
Production: https://united-voice-agent.up.railway.app
Development: http://localhost:8000
```

### Endpoints

#### `GET /`
Health check endpoint.

```bash
curl https://united-voice-agent.up.railway.app/

# Response
{
    "status": "healthy",
    "service": "United Voice Agent",
    "version": "2.0.0",
    "timestamp": "2025-08-10T12:00:00Z"
}
```

#### `GET /health`
Detailed health status.

```bash
curl https://united-voice-agent.up.railway.app/health

# Response
{
    "status": "healthy",
    "components": {
        "websocket": "healthy",
        "groq_api": "healthy",
        "elevenlabs_api": "healthy",
        "database": "healthy"
    },
    "metrics": {
        "active_sessions": 5,
        "uptime_seconds": 3600,
        "memory_usage_mb": 256
    }
}
```

#### `POST /transcribe`
Transcribe audio file (REST alternative).

```bash
curl -X POST https://united-voice-agent.up.railway.app/transcribe \
    -H "Content-Type: application/json" \
    -d '{
        "audio": "base64_encoded_audio",
        "format": "webm",
        "language": "en"
    }'

# Response
{
    "transcription": "I need a flight to Boston",
    "confidence": 0.94,
    "duration_ms": 2500,
    "language": "en"
}
```

## Python SDK

### Installation
```bash
pip install united-voice-agent
```

### Core Classes

#### `UnitedVoiceAgent`
Main orchestrator for voice interactions.

```python
from src.core.voice_agent import UnitedVoiceAgent

# Initialize
agent = UnitedVoiceAgent()

# Process audio
audio_data = load_audio_file('recording.wav')
transcription = agent.transcribe_audio(audio_data)
response = agent.get_response(transcription)

# Text-to-speech
audio_response = agent.speak_response(response)
```

#### `BookingFlow`
Manages conversation state and flow.

```python
from src.core.booking_flow import BookingFlow, BookingState

# Initialize
flow = BookingFlow()

# Process input
response = flow.process_input_with_intent("I need a flight to NYC")
print(response)  # "Great! Which city are you flying from?"

# Check state
print(flow.state)  # BookingState.COLLECTING_DEPARTURE

# Get booking info
info = flow.booking_info.to_dict()
print(info['destination'])  # "New York"
```

#### `IntentRecognizer`
ML-powered intent classification.

```python
from src.core.intent_recognizer import IntentRecognizer

recognizer = IntentRecognizer()

# Recognize intent
result = recognizer.recognize_intent(
    user_input="I need to change my departure city",
    current_state="collecting_date",
    booking_info={}
)

print(result.intent)      # "correction"
print(result.confidence)  # 0.92
print(result.entities)    # {"correction_type": "departure_city"}
```

### Service Classes

#### `GroqWhisperClient`
Speech-to-text service.

```python
from src.services.groq_whisper import GroqWhisperClient

client = GroqWhisperClient(api_key="your_key")

# Transcribe audio file
transcription = client.transcribe_audio_file(
    file_path="audio.wav",
    language="en"
)

# With fallback
result = client.transcribe_with_fallback(
    audio_data=audio_bytes,
    fallback_mode="mock"
)
print(result.text)    # Transcribed text
print(result.source)  # "groq" or "fallback"
```

#### `ElevenLabsTTS`
Text-to-speech service.

```python
from src.services.tts_service import ElevenLabsTTS

tts = ElevenLabsTTS(
    api_key="your_key",
    voice_id="rachel"
)

# Generate speech
audio_bytes = await tts.synthesize_speech_async(
    text="Welcome to United Airlines"
)

# Check availability
if tts.is_available():
    audio = tts.generate_speech(text)
```

## TypeScript/React Components

### `VoiceInterface`
Main voice interface component.

```typescript
import { VoiceInterface } from '@/components/VoiceInterface';

function App() {
    return (
        <VoiceInterface
            backendUrl="wss://api.example.com"
            onTranscription={(text) => console.log(text)}
            onResponse={(response) => console.log(response)}
        />
    );
}
```

### `useVoiceStore`
Zustand store for state management.

```typescript
import { useVoiceStore } from '@/store/voiceStore';

function Component() {
    const {
        isRecording,
        startRecording,
        stopRecording,
        conversation
    } = useVoiceStore();
    
    // Use state and actions
}
```

### `useWebSocket`
WebSocket connection hook.

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function Component() {
    const { isConnected, send, on } = useWebSocket(
        'wss://api.example.com'
    );
    
    useEffect(() => {
        on('transcription', (data) => {
            console.log('Received:', data.text);
        });
    }, []);
    
    const sendAudio = (audioBlob: Blob) => {
        send('audio_data', {
            audio: audioBlob,
            format: 'webm'
        });
    };
}
```

## Error Codes

### WebSocket Errors
| Code | Description | Resolution |
|------|-------------|------------|
| 1000 | Normal closure | N/A |
| 1001 | Going away | Reconnect |
| 1002 | Protocol error | Check client version |
| 1003 | Unsupported data | Check data format |
| 1006 | Abnormal closure | Check network |
| 4000 | Invalid session | Reconnect |
| 4001 | Rate limited | Reduce request frequency |
| 4002 | Authentication failed | Check API keys |

### API Errors
| Status | Description | Example |
|--------|-------------|---------|
| 400 | Bad Request | Invalid audio format |
| 401 | Unauthorized | Missing API key |
| 403 | Forbidden | Invalid API key |
| 404 | Not Found | Endpoint doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service down |

## Rate Limits

### WebSocket Limits
- Connections per IP: 10
- Messages per second: 10
- Audio uploads per minute: 30
- Maximum audio size: 10MB

### REST API Limits
- Requests per minute: 60
- Requests per hour: 1000
- Concurrent requests: 10

## Webhooks

### Booking Completion
```json
POST /your-webhook-url
{
    "event": "booking.completed",
    "data": {
        "confirmation_number": "ABC123",
        "passenger_name": "John Smith",
        "departure": "San Francisco",
        "destination": "New York",
        "departure_date": "2025-08-15",
        "return_date": "2025-08-20",
        "flight_numbers": ["UA523", "UA847"]
    },
    "timestamp": "2025-08-10T12:00:00Z"
}
```

### Error Notification
```json
POST /your-webhook-url
{
    "event": "error.critical",
    "data": {
        "error_type": "api_failure",
        "service": "groq_whisper",
        "message": "API key invalid",
        "session_id": "abc123"
    },
    "timestamp": "2025-08-10T12:00:00Z"
}
```

---

*For implementation examples, see the [examples/](../examples/) directory.*