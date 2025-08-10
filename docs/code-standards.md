# Code Standards and Clarity

## Python Code Standards

### Type Hints and Documentation

#### Always Use Type Hints
```python
# ✅ Good - Clear types
def process_audio(
    audio_data: bytes, 
    format: str = 'webm',
    language: str = 'en'
) -> Tuple[str, float]:
    """
    Process audio data and return transcription with confidence.
    
    Args:
        audio_data: Raw audio bytes
        format: Audio format (webm, wav, mp3)
        language: ISO language code
        
    Returns:
        Tuple of (transcription_text, confidence_score)
        
    Raises:
        AudioProcessingError: If audio format is unsupported
        TranscriptionError: If STT service fails
    """
    pass

# ❌ Bad - No types or documentation
def process_audio(audio_data, format='webm', language='en'):
    pass
```

#### Comprehensive Docstrings
```python
class BookingFlow:
    """
    Manages the conversation flow for flight booking interactions.
    
    This class implements a state machine that guides users through
    the booking process, handling intent recognition, corrections,
    and natural conversation flow.
    
    Attributes:
        state: Current conversation state
        booking_info: Collected booking information
        intent_recognizer: ML-based intent classification
        conversation_history: Previous interactions
        
    Example:
        >>> flow = BookingFlow()
        >>> response = flow.process_input("I need a flight to NYC")
        >>> print(response)
        "Great! Which city are you flying from?"
    """
```

### Naming Conventions

#### Descriptive Variable Names
```python
# ✅ Good - Clear intent
departure_city = extract_city(user_input)
is_roundtrip = booking_info.trip_type == "roundtrip"
confirmation_number = generate_booking_reference()

# ❌ Bad - Ambiguous
dc = extract_city(ui)
rt = bi.tt == "roundtrip"
cn = gen_ref()
```

#### Method Naming Patterns
```python
class VoiceAgent:
    # Action methods - verb_noun
    def process_audio(self): pass
    def generate_response(self): pass
    
    # Boolean methods - is/has/can prefix
    def is_ready(self): pass
    def has_valid_key(self): pass
    def can_process(self): pass
    
    # Getters - get_ prefix
    def get_current_state(self): pass
    
    # Handlers - handle_ prefix
    def handle_error(self): pass
    
    # Internal - underscore prefix
    def _validate_input(self): pass
```

### Error Handling

#### Explicit Error Types
```python
# ✅ Good - Specific exceptions
class BookingError(Exception):
    """Base exception for booking-related errors"""
    pass

class InvalidCityError(BookingError):
    """Raised when city cannot be recognized"""
    pass

class NoFlightsAvailableError(BookingError):
    """Raised when no flights match criteria"""
    pass

# Usage
try:
    flights = search_flights(departure, destination)
except InvalidCityError as e:
    logger.error(f"City not recognized: {e}")
    return "I couldn't find that city. Could you try again?"
except NoFlightsAvailableError:
    return "No flights available for those dates."
```

#### Graceful Degradation
```python
def transcribe_with_fallback(audio_data: bytes) -> str:
    """
    Attempt transcription with multiple fallback options.
    """
    # Primary: Groq Whisper
    try:
        return groq_whisper.transcribe(audio_data)
    except GroqAPIError as e:
        logger.warning(f"Groq failed: {e}, trying fallback")
    
    # Fallback 1: Local Whisper
    try:
        return local_whisper.transcribe(audio_data)
    except Exception as e:
        logger.warning(f"Local Whisper failed: {e}")
    
    # Fallback 2: Mock response
    logger.error("All transcription methods failed")
    return "I'm having trouble hearing you. Could you type instead?"
```

### Code Organization

#### Single Responsibility Principle
```python
# ✅ Good - Each class has one clear purpose
class IntentRecognizer:
    """Only handles intent recognition"""
    def recognize_intent(self, text: str) -> Intent:
        pass

class BookingValidator:
    """Only validates booking information"""
    def validate_booking(self, info: BookingInfo) -> bool:
        pass

class FlightSearcher:
    """Only searches for flights"""
    def search(self, criteria: SearchCriteria) -> List[Flight]:
        pass

# ❌ Bad - Class doing too much
class BookingManager:
    def recognize_intent(self): pass
    def validate_booking(self): pass
    def search_flights(self): pass
    def send_email(self): pass
    def process_payment(self): pass
```

#### Modular Structure
```
src/
├── core/               # Core business logic
│   ├── voice_agent.py  # Main orchestrator
│   ├── booking_flow.py # State management
│   └── intent.py       # Intent recognition
├── services/           # External service integrations
│   ├── groq_stt.py     # Speech-to-text
│   ├── elevenlabs.py   # Text-to-speech
│   └── flights_api.py  # Flight search
├── utils/              # Shared utilities
│   ├── validators.py   # Input validation
│   └── formatters.py   # Output formatting
└── config/             # Configuration
    └── settings.py     # Environment settings
```

## TypeScript/React Standards

### Component Structure
```typescript
// ✅ Good - Clear, typed, documented
interface VoiceButtonProps {
  /** Whether recording is active */
  isRecording: boolean;
  /** Callback when recording starts */
  onStart: () => void;
  /** Callback when recording stops */
  onStop: () => void;
  /** Optional CSS class */
  className?: string;
}

/**
 * Voice recording button with visual feedback
 */
export const VoiceButton: React.FC<VoiceButtonProps> = memo(({
  isRecording,
  onStart,
  onStop,
  className
}) => {
  // Component logic
});

// ❌ Bad - No types, no docs
export const VoiceButton = ({ isRecording, onStart, onStop }) => {
  // Component logic
};
```

### State Management
```typescript
// ✅ Good - Typed Zustand store
interface VoiceStore {
  // State
  isRecording: boolean;
  transcription: string;
  
  // Actions
  startRecording: () => void;
  stopRecording: () => void;
  setTranscription: (text: string) => void;
}

export const useVoiceStore = create<VoiceStore>()((set) => ({
  isRecording: false,
  transcription: '',
  
  startRecording: () => set({ isRecording: true }),
  stopRecording: () => set({ isRecording: false }),
  setTranscription: (text) => set({ transcription: text })
}));
```

### Custom Hooks
```typescript
/**
 * Hook for managing WebSocket connection
 * @param url - WebSocket server URL
 * @returns Connection state and methods
 */
export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<Socket | null>(null);
  
  useEffect(() => {
    // Connection logic
  }, [url]);
  
  return {
    isConnected,
    error,
    send: useCallback((event: string, data: any) => {
      socketRef.current?.emit(event, data);
    }, [])
  };
}
```

## Testing Standards

### Descriptive Test Names
```python
# ✅ Good - Clear what's being tested
def test_booking_flow_handles_city_correction():
    """User should be able to correct city after providing it"""
    flow = BookingFlow()
    flow.process_input("Flying from NYC")
    response = flow.process_input("Actually, make that Boston")
    assert "Boston" in response
    assert flow.booking_info.departure_city == "Boston"

# ❌ Bad - Unclear test purpose
def test_flow_1():
    flow = BookingFlow()
    flow.process_input("NYC")
    flow.process_input("Boston")
```

### Test Organization
```python
class TestBookingFlow:
    """Tests for BookingFlow class"""
    
    class TestStateTransitions:
        """Test state machine transitions"""
        def test_greeting_to_collecting_name(self): pass
        def test_collecting_name_to_departure(self): pass
    
    class TestIntentHandling:
        """Test intent recognition and routing"""
        def test_correction_intent(self): pass
        def test_cancellation_intent(self): pass
    
    class TestErrorCases:
        """Test error handling"""
        def test_invalid_city(self): pass
        def test_api_failure(self): pass
```

## Documentation Standards

### README Structure
```markdown
# Component Name

## Overview
Brief description of what this component does.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from module import Component
component = Component()
result = component.process()
```

## API Reference
### `Component.process(input: str) -> str`
Process input and return result.

## Examples
See `examples/` directory for usage examples.

## Testing
```bash
pytest tests/
```

## Contributing
See CONTRIBUTING.md for guidelines.
```

### Inline Comments
```python
# ✅ Good - Explains WHY, not WHAT
# Use exponential backoff to avoid overwhelming the API
retry_delay = 2 ** attempt

# Check for Whisper hallucinations (common in silence)
if transcription.lower() in HALLUCINATION_PHRASES:
    return ""

# ❌ Bad - Explains obvious code
# Set x to 5
x = 5

# Loop through list
for item in items:
    pass
```

## Performance Considerations

### Efficient Data Structures
```python
# ✅ Good - O(1) lookup
CITY_AIRPORTS = {
    "new york": ["JFK", "LGA", "EWR"],
    "los angeles": ["LAX"],
    "chicago": ["ORD", "MDW"]
}

def get_airport(city: str) -> List[str]:
    return CITY_AIRPORTS.get(city.lower(), [])

# ❌ Bad - O(n) lookup
CITIES = [
    {"name": "new york", "airports": ["JFK", "LGA", "EWR"]},
    {"name": "los angeles", "airports": ["LAX"]}
]

def get_airport(city: str) -> List[str]:
    for c in CITIES:
        if c["name"] == city.lower():
            return c["airports"]
    return []
```

### Async Operations
```python
# ✅ Good - Concurrent processing
async def process_requests(requests: List[Request]) -> List[Response]:
    """Process multiple requests concurrently"""
    tasks = [process_single(req) for req in requests]
    return await asyncio.gather(*tasks)

# ❌ Bad - Sequential processing
async def process_requests(requests: List[Request]) -> List[Response]:
    responses = []
    for req in requests:
        response = await process_single(req)
        responses.append(response)
    return responses
```

## Security Standards

### Input Validation
```python
def validate_city_input(city: str) -> str:
    """Validate and sanitize city input"""
    # Length check
    if len(city) > 100:
        raise ValueError("City name too long")
    
    # Character validation
    if not re.match(r'^[a-zA-Z\s\-\.]+$', city):
        raise ValueError("Invalid characters in city name")
    
    # Normalize
    return city.strip().title()
```

### Secrets Management
```python
# ✅ Good - Environment variables
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise EnvironmentError("GROQ_API_KEY not set")

# ❌ Bad - Hardcoded secrets
api_key = "gsk_1234567890abcdef"  # NEVER DO THIS
```

## Code Review Checklist

### Before Submitting PR
- [ ] All functions have type hints
- [ ] All classes/functions have docstrings
- [ ] Complex logic has explanatory comments
- [ ] No hardcoded secrets or credentials
- [ ] Tests pass with >80% coverage
- [ ] No console.log or print statements
- [ ] Error handling for external service calls
- [ ] Follows naming conventions
- [ ] No commented-out code
- [ ] Dependencies are documented

### Review Focus Areas
1. **Correctness**: Does it work as intended?
2. **Clarity**: Is it easy to understand?
3. **Efficiency**: Are there performance issues?
4. **Security**: Are inputs validated?
5. **Maintainability**: Will it be easy to modify?

---

*These standards ensure our codebase remains clean, understandable, and maintainable.*