# Component Architecture

## System Overview

The United Voice Agent is built with a modular, microservices-inspired architecture that ensures scalability, maintainability, and resilience.

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Voice UI   │  │   WebSocket  │  │    State     │  │
│  │  Components  │  │    Client    │  │  Management  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                              ↕
                     WebSocket (Socket.IO)
                              ↕
┌─────────────────────────────────────────────────────────┐
│                    Backend (Python)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   WebSocket  │  │     Core     │  │   Services   │  │
│  │    Server    │  │    Engine    │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                 ↓                 ↓            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              External Services                    │  │
│  │  Groq API │ ElevenLabs │ Google Flights │ etc.  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer

#### Voice Interface (`voice-frontend/src/components/`)
```typescript
// VoiceInterface.tsx - Main UI component
interface VoiceInterfaceProps {
    onTranscription: (text: string) => void;
    onAgentResponse: (response: AgentResponse) => void;
    connectionStatus: ConnectionState;
}

// Key responsibilities:
// - Audio recording via MediaRecorder API
// - Real-time waveform visualization
// - Touch/click interaction handling
// - Audio playback queue management
```

#### State Management (`voice-frontend/src/store/`)
```typescript
// voiceStore.ts - Zustand state management
interface VoiceStoreState {
    connectionState: ConnectionState;
    recordingState: RecordingState;
    conversation: ConversationEntry[];
    audioQueue: AudioQueueItem[];
    
    // Actions
    setConnectionState: (state: ConnectionState) => void;
    addToConversation: (entry: ConversationEntry) => void;
    processAudioQueue: () => void;
}
```

#### WebSocket Client (`voice-frontend/src/services/`)
```typescript
class WebSocketService {
    private socket: Socket;
    
    connect(): void {
        this.socket = io(BACKEND_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5
        });
    }
    
    sendAudio(audioBlob: Blob): void {
        const base64 = await this.blobToBase64(audioBlob);
        this.socket.emit('audio_data', {
            audio: base64,
            format: 'webm',
            timestamp: Date.now()
        });
    }
}
```

### 2. Backend Core

#### Voice Agent (`src/core/voice_agent.py`)
```python
class UnitedVoiceAgent:
    """Central orchestrator for voice interactions"""
    
    def __init__(self):
        self.setup_stt()      # Speech-to-Text
        self.setup_llm()      # Language Model
        self.setup_tts()      # Text-to-Speech
        self.booking_flow = BookingFlow()
        self.conversation_history = []
    
    def get_response(self, user_input: str) -> str:
        """Main processing pipeline"""
        # 1. Add to conversation history
        # 2. Process through booking flow
        # 3. Enhance with LLM
        # 4. Return response
```

#### Booking Flow Engine (`src/core/booking_flow.py`)
```python
class BookingFlow:
    """Manages conversation state and flow"""
    
    def __init__(self):
        self.state = BookingState.GREETING
        self.booking_info = EnhancedBookingInfo()
        self.intent_recognizer = IntentRecognizer()
    
    def process_input_with_intent(self, user_input: str) -> str:
        """Intent-based processing"""
        intent = self.intent_recognizer.recognize_intent(
            user_input, 
            self.state, 
            self.booking_info
        )
        return self._route_to_handler(intent)
```

#### Intent Recognition (`src/core/intent_recognizer.py`)
```python
class IntentRecognizer:
    """ML-powered intent classification"""
    
    def recognize_intent(self, user_input: str, state: str, context: dict):
        # Use Groq LLM for intent classification
        prompt = self._build_intent_prompt(user_input, state, context)
        response = self.groq_client.chat(prompt)
        return self._parse_intent(response)
```

### 3. Service Layer

#### WebSocket Server (`src/services/websocket_server.py`)
```python
@sio.event
async def audio_data(sid, data):
    """Handle incoming audio stream"""
    # 1. Decode base64 audio
    audio_bytes = base64.b64decode(data['audio'])
    
    # 2. Transcribe with Whisper
    transcription = await voice_agent.transcribe_streaming_audio(
        audio_bytes, 
        data.get('format', 'webm')
    )
    
    # 3. Process through voice agent
    response = await voice_agent.process_voice_input(transcription)
    
    # 4. Generate TTS audio
    audio_response = await tts_service.synthesize_speech_async(response)
    
    # 5. Send back to client
    await sio.emit('agent_response', {
        'text': response,
        'audio': base64.b64encode(audio_response).decode(),
        'conversation_state': voice_agent.get_conversation_state()
    })
```

#### Speech Services (`src/services/`)

##### Groq Whisper STT
```python
class GroqWhisperClient:
    """Speech-to-Text using Groq's Whisper API"""
    
    def transcribe_audio_file(self, file_path: str, language="en"):
        with open(file_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                language=language,
                response_format="json"
            )
        return transcription.text
```

##### ElevenLabs TTS
```python
class ElevenLabsTTS:
    """Text-to-Speech using ElevenLabs"""
    
    async def synthesize_speech_async(self, text: str) -> bytes:
        audio = await self.client.text_to_speech.convert_async(
            text=text,
            voice_id=self.voice_id,
            model_id="eleven_monolingual_v1"
        )
        return audio
```

## Component Integration

### 1. Request Flow
```
User Speech → Frontend Audio Capture → WebSocket → Backend
    ↓
Whisper STT → Text Transcription
    ↓
Intent Recognition → Booking Flow Processing
    ↓
LLM Enhancement → Natural Response Generation
    ↓
ElevenLabs TTS → Audio Generation
    ↓
WebSocket → Frontend → Audio Playback → User
```

### 2. Data Flow
```python
# 1. Audio Input
{
    "audio": "base64_encoded_audio",
    "format": "webm",
    "timestamp": 1234567890
}

# 2. Transcription
{
    "text": "I need a flight to New York",
    "confidence": 0.95,
    "language": "en"
}

# 3. Intent Recognition
{
    "intent": "provide_city",
    "entities": {
        "destination_city": "New York"
    },
    "confidence": 0.92
}

# 4. Booking State Update
{
    "state": "collecting_departure",
    "booking_info": {
        "destination": "New York",
        "collected_fields": ["destination"]
    }
}

# 5. Response Generation
{
    "text": "Great! Which city are you flying from?",
    "audio": "base64_encoded_mp3",
    "state": "collecting_departure"
}
```

### 3. Error Handling & Fallbacks

#### Service Fallback Chain
```python
class ServiceWithFallback:
    """Base class for services with fallback mechanisms"""
    
    def execute_with_fallback(self, primary_func, fallback_func, *args):
        try:
            return primary_func(*args)
        except Exception as e:
            logger.warning(f"Primary service failed: {e}")
            return fallback_func(*args)
```

#### Specific Fallbacks
```python
# STT Fallback
if not groq_available:
    # Use mock transcription for development
    return MockTranscriptionService()

# TTS Fallback  
if not elevenlabs_available:
    # Use browser's built-in TTS
    return BrowserTTSService()

# LLM Fallback
if not groq_llm_available:
    # Use rule-based responses
    return RuleBasedResponseGenerator()
```

## Configuration Management

### Environment Configuration (`src/config/settings.py`)
```python
@dataclass
class Settings:
    """Centralized configuration"""
    
    groq: GroqConfig
    elevenlabs: ElevenLabsConfig
    websocket: WebSocketConfig
    deployment: DeploymentConfig
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        load_dotenv()
        return cls(
            groq=GroqConfig(
                api_key=os.getenv('GROQ_API_KEY'),
                model='llama-3.1-70b-versatile'
            ),
            # ... more config
        )
```

### Dynamic Configuration
```python
class WebSocketConfig:
    """WebSocket configuration with environment detection"""
    
    def get_cors_origins(self) -> List[str]:
        if self.environment == "production":
            return [
                "https://unitedvoice.vercel.app",
                "https://*.vercel.app"
            ]
        else:
            return ["http://localhost:3000"]
```

## Deployment Architecture

### Production Deployment
```
┌─────────────┐     ┌─────────────┐
│   Vercel    │────→│   Railway   │
│  (Frontend) │     │  (Backend)  │
└─────────────┘     └─────────────┘
       ↓                   ↓
┌─────────────┐     ┌─────────────┐
│     CDN     │     │  Database   │
│  (Static)   │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘
```

### Container Architecture
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "src.main"]
```

## Monitoring & Observability

### Logging Strategy
```python
# Structured logging
logger.info("Processing audio", extra={
    "session_id": sid,
    "audio_format": format,
    "audio_size": len(audio_bytes),
    "timestamp": datetime.utcnow().isoformat()
})
```

### Metrics Collection
```python
class MetricsCollector:
    """Track system performance"""
    
    metrics = {
        "transcription_latency": [],
        "response_generation_time": [],
        "tts_generation_time": [],
        "total_request_time": [],
        "success_rate": 0.0
    }
```

## Security Considerations

### API Key Management
```python
# Never hardcode keys
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise ValueError("GROQ_API_KEY not configured")

# Validate key format
if not api_key.startswith('gsk_'):
    raise ValueError("Invalid Groq API key format")
```

### Input Sanitization
```python
def sanitize_user_input(text: str) -> str:
    """Remove potentially harmful content"""
    # Remove HTML/script tags
    text = re.sub(r'<[^>]+>', '', text)
    # Limit length
    text = text[:1000]
    return text.strip()
```

## Testing Strategy

### Unit Testing
```python
def test_booking_flow_state_transitions():
    flow = BookingFlow()
    assert flow.state == BookingState.GREETING
    
    flow.process_input("John Smith")
    assert flow.state == BookingState.COLLECTING_DEPARTURE
```

### Integration Testing
```python
async def test_websocket_audio_processing():
    """Test complete audio processing pipeline"""
    client = TestClient(app)
    audio_data = load_test_audio()
    
    response = await client.emit('audio_data', {
        'audio': base64.b64encode(audio_data)
    })
    
    assert 'transcription' in response
    assert 'agent_response' in response
```

## Performance Optimization

### Caching Strategy
```python
@lru_cache(maxsize=100)
def get_city_airport_code(city_name: str) -> str:
    """Cache frequently looked up airports"""
    return AIRPORT_CODES.get(city_name.lower())
```

### Async Processing
```python
async def process_multiple_requests(requests: List[AudioRequest]):
    """Process multiple audio requests concurrently"""
    tasks = [process_audio(req) for req in requests]
    return await asyncio.gather(*tasks)
```

## Scalability Considerations

### Horizontal Scaling
- Stateless WebSocket servers behind load balancer
- Redis for session state sharing
- Message queue for async processing

### Vertical Scaling
- Optimize memory usage with streaming
- Use connection pooling for external services
- Implement request batching

---

*For more details on specific components, see the individual documentation files.*