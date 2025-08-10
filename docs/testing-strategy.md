# Testing Strategy

## Overview
Our testing strategy ensures the United Voice Agent delivers reliable, natural conversations with comprehensive test coverage across all components.

## Testing Pyramid

```
         /\
        /  \  E2E Tests (10%)
       /    \  - Full conversation flows
      /──────\  - Production-like environment
     /        \  
    /          \  Integration Tests (30%)
   /            \  - Component interactions
  /              \  - API integrations
 /                \  - WebSocket connections
/──────────────────\
                     Unit Tests (60%)
                     - Individual functions
                     - Pure logic
                     - Edge cases
```

## Unit Testing

### Python Unit Tests

#### Test Structure
```python
# test_booking_flow.py
import pytest
from src.core.booking_flow import BookingFlow, BookingState

class TestBookingFlow:
    """Test suite for BookingFlow class"""
    
    @pytest.fixture
    def booking_flow(self):
        """Create fresh BookingFlow instance for each test"""
        return BookingFlow()
    
    def test_initial_state(self, booking_flow):
        """Flow should start in GREETING state"""
        assert booking_flow.state == BookingState.GREETING
    
    def test_name_collection(self, booking_flow):
        """Should collect and store customer name"""
        response = booking_flow.process_input("John Smith")
        assert "John" in booking_flow.booking_info.customer.first_name.value
        assert booking_flow.state == BookingState.COLLECTING_DEPARTURE
```

#### Testing Intent Recognition
```python
class TestIntentRecognizer:
    """Test intent recognition accuracy"""
    
    @pytest.mark.parametrize("input_text,expected_intent", [
        ("My name is John", "provide_name"),
        ("I need to fly to NYC", "provide_city"),
        ("Actually, make that Chicago", "correction"),
        ("Yes, that's correct", "confirm_yes"),
        ("Cancel everything", "cancel")
    ])
    def test_intent_recognition(self, input_text, expected_intent):
        recognizer = IntentRecognizer()
        result = recognizer.recognize_intent(input_text, "greeting", {})
        assert result.intent == expected_intent
        assert result.confidence > 0.7
```

#### Testing Error Handling
```python
def test_invalid_city_handling():
    """Should handle unrecognized cities gracefully"""
    flow = BookingFlow()
    flow.state = BookingState.COLLECTING_DEPARTURE
    
    response = flow.process_input("Atlantis")
    assert "couldn't find that city" in response.lower()
    assert flow.state == BookingState.COLLECTING_DEPARTURE  # Stay in same state
```

### TypeScript Unit Tests

#### Component Testing
```typescript
// VoiceButton.test.tsx
import { render, fireEvent, screen } from '@testing-library/react';
import { VoiceButton } from '@/components/VoiceButton';

describe('VoiceButton', () => {
    it('should toggle recording on click', () => {
        const onStart = jest.fn();
        const onStop = jest.fn();
        
        const { rerender } = render(
            <VoiceButton 
                isRecording={false}
                onStart={onStart}
                onStop={onStop}
            />
        );
        
        // Click to start
        fireEvent.click(screen.getByRole('button'));
        expect(onStart).toHaveBeenCalled();
        
        // Rerender with recording state
        rerender(
            <VoiceButton 
                isRecording={true}
                onStart={onStart}
                onStop={onStop}
            />
        );
        
        // Click to stop
        fireEvent.click(screen.getByRole('button'));
        expect(onStop).toHaveBeenCalled();
    });
});
```

#### Store Testing
```typescript
// voiceStore.test.ts
import { renderHook, act } from '@testing-library/react';
import { useVoiceStore } from '@/store/voiceStore';

describe('VoiceStore', () => {
    it('should manage recording state', () => {
        const { result } = renderHook(() => useVoiceStore());
        
        expect(result.current.recordingState).toBe('idle');
        
        act(() => {
            result.current.setRecordingState('recording');
        });
        
        expect(result.current.recordingState).toBe('recording');
        expect(result.current.isRecordingIndicatorVisible).toBe(true);
    });
});
```

## Integration Testing

### WebSocket Integration
```python
# test_websocket_integration.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.services.websocket_server import create_websocket_app

@pytest.mark.asyncio
async def test_audio_processing_pipeline():
    """Test complete audio processing flow"""
    app = create_websocket_app()
    
    # Mock audio data
    audio_data = {
        'audio': 'base64_encoded_test_audio',
        'format': 'webm',
        'timestamp': 1234567890
    }
    
    with patch('src.services.groq_whisper.GroqWhisperClient.transcribe_audio_file') as mock_transcribe:
        mock_transcribe.return_value = "I need a flight to Boston"
        
        # Simulate WebSocket event
        response = await app.handle_audio_data('test_session', audio_data)
        
        assert 'transcription' in response
        assert response['transcription']['text'] == "I need a flight to Boston"
        assert 'agent_response' in response
```

### API Integration Tests
```python
@pytest.mark.integration
class TestGroqIntegration:
    """Test Groq API integration"""
    
    @pytest.mark.skipif(not os.getenv('GROQ_API_KEY'), reason="No API key")
    def test_whisper_transcription(self):
        """Test real Whisper API call"""
        client = GroqWhisperClient()
        
        # Use test audio file
        test_audio = "tests/fixtures/test_audio.wav"
        result = client.transcribe_audio_file(test_audio)
        
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
    
    def test_llm_response_generation(self):
        """Test LLM response generation"""
        client = GroqClient()
        
        response = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-70b-versatile"
        )
        
        assert response is not None
        assert 'message' in response
```

### Database Integration
```python
@pytest.mark.database
async def test_conversation_persistence():
    """Test saving and retrieving conversations"""
    from src.services.database import ConversationDB
    
    db = ConversationDB()
    
    # Save conversation
    conversation_id = await db.save_conversation({
        'session_id': 'test123',
        'messages': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ],
        'booking_info': {'destination': 'NYC'}
    })
    
    # Retrieve
    conversation = await db.get_conversation(conversation_id)
    assert conversation['session_id'] == 'test123'
    assert len(conversation['messages']) == 2
```

## End-to-End Testing

### Complete Booking Flow Test
```python
# test_e2e_booking.py
class TestCompleteBookingFlow:
    """Test complete booking conversation"""
    
    def test_happy_path_booking(self):
        """Test successful booking from start to finish"""
        agent = UnitedVoiceAgent()
        
        # Simulate complete conversation
        conversations = [
            ("Hi", "greeting"),
            ("John Smith", "name_collected"),
            ("San Francisco", "departure_collected"),
            ("New York", "destination_collected"),
            ("Round trip", "trip_type_collected"),
            ("Next Monday", "departure_date_collected"),
            ("Following Friday", "return_date_collected"),
            ("Option 2 please", "flight_selected"),
            ("Yes, book it", "booking_confirmed")
        ]
        
        for user_input, expected_state in conversations:
            response = agent.get_response(user_input)
            assert response is not None
            
            # Verify state progression
            state = agent.booking_flow.state.value
            assert expected_state in state.lower() or \
                   state == 'booking_complete'
        
        # Verify booking completion
        assert agent.booking_flow.state == BookingState.BOOKING_COMPLETE
        assert agent.booking_flow.booking_info.confirmation_number
```

### Voice Interaction E2E Test
```javascript
// test_voice_e2e.js
const puppeteer = require('puppeteer');

describe('Voice Interface E2E', () => {
    let browser, page;
    
    beforeAll(async () => {
        browser = await puppeteer.launch();
        page = await browser.newPage();
        
        // Grant microphone permission
        const context = browser.defaultBrowserContext();
        await context.overridePermissions('http://localhost:3000', ['microphone']);
    });
    
    test('Complete voice booking', async () => {
        await page.goto('http://localhost:3000');
        
        // Wait for WebSocket connection
        await page.waitForSelector('.connection-status.connected');
        
        // Start recording
        await page.click('.voice-button');
        
        // Simulate audio input (using mock audio file)
        await page.evaluate(() => {
            // Inject test audio
            window.testAudioInput('I need a flight to Boston');
        });
        
        // Stop recording
        await page.click('.voice-button');
        
        // Wait for transcription
        await page.waitForSelector('.transcription-text');
        const transcription = await page.$eval('.transcription-text', el => el.textContent);
        expect(transcription).toContain('Boston');
        
        // Wait for agent response
        await page.waitForSelector('.agent-response');
        const response = await page.$eval('.agent-response', el => el.textContent);
        expect(response).toContain('Which city are you flying from?');
    });
});
```

## Performance Testing

### Load Testing
```python
# test_load.py
import asyncio
import aiohttp
import time

async def simulate_user_session(session_id: int):
    """Simulate a single user session"""
    async with aiohttp.ClientSession() as session:
        ws = await session.ws_connect('ws://localhost:8000/socket.io/')
        
        # Send test audio
        await ws.send_json({
            'event': 'audio_data',
            'data': {
                'audio': 'test_audio_base64',
                'format': 'webm'
            }
        })
        
        # Wait for response
        response = await ws.receive_json()
        await ws.close()
        return response

async def load_test(concurrent_users: int = 100):
    """Test with multiple concurrent users"""
    start_time = time.time()
    
    tasks = [simulate_user_session(i) for i in range(concurrent_users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    successful = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"Concurrent users: {concurrent_users}")
    print(f"Duration: {duration:.2f}s")
    print(f"Success rate: {successful}/{concurrent_users}")
    print(f"Avg response time: {duration/concurrent_users:.3f}s")
```

### Latency Testing
```python
def test_transcription_latency():
    """Measure transcription latency"""
    import time
    
    client = GroqWhisperClient()
    audio_file = "tests/fixtures/3_second_audio.wav"
    
    latencies = []
    for _ in range(10):
        start = time.time()
        client.transcribe_audio_file(audio_file)
        latency = time.time() - start
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 2.0, f"Transcription too slow: {avg_latency:.2f}s"
    print(f"Average transcription latency: {avg_latency:.2f}s")
```

## Test Data Management

### Fixtures
```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def test_audio_files():
    """Provide test audio files"""
    return {
        'short': Path('tests/fixtures/short_audio.wav'),
        'long': Path('tests/fixtures/long_audio.wav'),
        'noisy': Path('tests/fixtures/noisy_audio.wav'),
        'silent': Path('tests/fixtures/silent_audio.wav')
    }

@pytest.fixture
def mock_booking_info():
    """Provide mock booking information"""
    return {
        'customer': {'first_name': 'John', 'last_name': 'Doe'},
        'trip': {
            'departure_city': 'San Francisco',
            'arrival_city': 'New York',
            'departure_date': '2025-08-15',
            'trip_type': 'roundtrip'
        }
    }
```

### Test Conversations
```python
# test_conversations.py
CONVERSATION_SCENARIOS = {
    'happy_path': [
        ("Hi", "greeting"),
        ("John Smith", "name"),
        ("NYC to LA", "cities"),
        ("Next Monday", "date")
    ],
    'with_corrections': [
        ("Hi", "greeting"),
        ("Jon Smith", "name"),
        ("Actually it's John with an H", "correction"),
        ("Flying from NYC", "departure")
    ],
    'complex_input': [
        ("I'm John and I need a round trip from SF to NYC next week returning Friday", "multi_info")
    ]
}
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-report=xml
      
      - name: Run integration tests
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: pytest tests/integration -m "not slow"
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: cd voice-frontend && npm ci
      
      - name: Run tests
        run: cd voice-frontend && npm test -- --coverage
      
      - name: Run E2E tests
        run: cd voice-frontend && npm run test:e2e
```

## Test Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 80%
- **Core Logic** (`src/core/`): 90%
- **API Handlers** (`src/api/`): 85%
- **Services** (`src/services/`): 75%
- **Utilities** (`src/utils/`): 95%

### Coverage Report
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Testing Best Practices

### 1. Test Naming
```python
# ✅ Good - Descriptive test names
def test_booking_flow_handles_destination_correction_after_confirmation():
    pass

def test_whisper_returns_empty_string_for_silent_audio():
    pass

# ❌ Bad - Vague names
def test_1():
    pass

def test_booking():
    pass
```

### 2. Test Independence
```python
# ✅ Good - Each test is independent
def test_departure_collection():
    flow = BookingFlow()  # Fresh instance
    flow.state = BookingState.COLLECTING_DEPARTURE
    # ... test logic

# ❌ Bad - Tests depend on shared state
class TestBooking:
    flow = BookingFlow()  # Shared instance
    
    def test_step1(self):
        self.flow.process_input("John")  # Modifies shared state
```

### 3. Mock External Services
```python
# ✅ Good - Mock external dependencies
@patch('src.services.groq_whisper.GroqWhisperClient.transcribe_audio_file')
def test_transcription_handling(mock_transcribe):
    mock_transcribe.return_value = "Test transcription"
    # ... test logic

# ❌ Bad - Real API calls in tests
def test_transcription():
    client = GroqWhisperClient()  # Real API calls
    result = client.transcribe_audio_file("audio.wav")
```

## Debugging Tests

### Verbose Output
```bash
# Run with verbose output
pytest -vv tests/

# Show print statements
pytest -s tests/

# Run specific test
pytest tests/unit/test_booking_flow.py::TestBookingFlow::test_name_collection
```

### Debugging Failed Tests
```python
# Add breakpoint in test
def test_complex_scenario():
    flow = BookingFlow()
    response = flow.process_input("Complex input")
    
    import pdb; pdb.set_trace()  # Debugger breakpoint
    
    assert "expected" in response
```

---

*For more testing examples, see the `tests/` directory.*