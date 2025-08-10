# Branching Flows and User Prompts

## Overview
The United Voice Agent uses a sophisticated state machine combined with intent recognition to manage complex, branching conversation flows. This allows for natural, non-linear conversations that adapt to user needs.

## State Machine Architecture

### Core States
```python
class BookingState(Enum):
    IDLE = "idle"
    GREETING = "greeting"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_DEPARTURE = "collecting_departure"
    COLLECTING_DESTINATION = "collecting_destination"
    COLLECTING_TRIP_TYPE = "collecting_trip_type"
    COLLECTING_DATE = "collecting_date"
    COLLECTING_RETURN_DATE = "collecting_return_date"
    PRESENTING_OPTIONS = "presenting_options"
    CONFIRMING_SELECTION = "confirming_selection"
    BOOKING_COMPLETE = "booking_complete"
    ERROR = "error"
```

### State Transition Diagram
```
     GREETING
         ↓
   COLLECTING_NAME ←→ [Corrections]
         ↓
   COLLECTING_DEPARTURE ←→ [Corrections]
         ↓
   COLLECTING_DESTINATION ←→ [Corrections]
         ↓
   COLLECTING_TRIP_TYPE
      ↙        ↘
  One-Way    Round-Trip
     ↓           ↓
COLLECTING_DATE  COLLECTING_DATE
     ↓           ↓
     ↓      COLLECTING_RETURN_DATE
     ↓           ↓
     ↘         ↙
   PRESENTING_OPTIONS
         ↓
   CONFIRMING_SELECTION
         ↓
   BOOKING_COMPLETE
```

## Intent-Based Branching

### Intent Recognition System
```python
class IntentRecognizer:
    """Identifies user intent from natural language"""
    
    INTENTS = [
        "provide_name",      # User giving their name
        "provide_city",      # Providing departure/destination
        "provide_date",      # Date information
        "confirm_yes",       # Affirmative responses
        "confirm_no",        # Negative responses
        "correction",        # Fixing previous info
        "select_option",     # Choosing from presented options
        "cancel",           # Canceling the process
        "goodbye",          # Ending conversation
        "question"          # Asking for clarification
    ]
```

### Dynamic Flow Adaptation
```python
def process_input_with_intent(self, user_input: str) -> str:
    """Process input based on recognized intent"""
    
    intent_result = self.intent_recognizer.recognize_intent(
        user_input, 
        self.state.value, 
        self.booking_info
    )
    
    # Route to appropriate handler based on intent
    if intent_result.intent == "correction":
        return self._handle_correction(user_input, intent_result)
    elif intent_result.intent == "cancel":
        return self._handle_cancellation()
    # ... more intent handlers
```

## Handling Complex User Inputs

### Multi-Information Extraction
Users often provide multiple pieces of information at once:

```python
# User: "I'm John Smith and I need a round trip from SF to NYC next Tuesday"
# System extracts:
entities = {
    "name": "John Smith",
    "trip_type": "round_trip",
    "departure_city": "San Francisco",
    "destination_city": "New York",
    "departure_date": "next Tuesday"
}

# Update all at once
self.booking_info.update_customer_info("first_name", "John")
self.booking_info.update_customer_info("last_name", "Smith")
self.booking_info.update_trip_info("trip_type", "roundtrip")
# ... etc
```

### Correction Handling
```python
def _handle_correction(self, user_input: str, correction_type: str):
    """Handle user corrections at any point"""
    
    # Examples of corrections:
    # "Actually, make that Chicago instead"
    # "Sorry, I meant next Friday"
    # "No, my name is spelled J-O-N"
    
    if correction_type == 'departure':
        old_value = self.booking_info.trip.departure_city
        # Update and acknowledge
        response = f"Got it, changing from {old_value} to {new_value}"
```

## Conversation Flow Patterns

### 1. Linear Flow (Happy Path)
```python
# Straightforward booking
User: "Hi"
Alex: "Hi! I'm Alex. What trip are you planning?"
User: "I need to fly to Boston"
Alex: "Where are you flying from?"
User: "New York"
Alex: "Round trip or one-way?"
# ... continues linearly
```

### 2. Skip-Ahead Pattern
```python
# User provides info before being asked
User: "I need a round trip from LA to Seattle next Monday"
Alex: "Great! Round trip from LA to Seattle. When do you return?"
# Skips name, departure, destination, trip type, departure date
```

### 3. Correction Loop
```python
# User changes their mind
Alex: "Flying from San Francisco?"
User: "Yes"
Alex: "Where to?"
User: "Boston... actually wait, make that New York"
Alex: "No problem, changed to New York. Round trip or one-way?"
```

### 4. Clarification Branch
```python
# Ambiguous input requiring clarification
User: "I'm flying to London"
Alex: "I can help with that! Are you looking for London, Ontario or did you mean London, England? I can help with domestic flights."
User: "Oh, I need international"
Alex: "I'll connect you with our international booking team."
```

## Prompt Engineering

### Context-Aware Prompts
```python
def _determine_next_step(self) -> str:
    """Dynamically determine what to ask next"""
    
    if not self._get_customer_name():
        return "May I have your name please?"
    elif not self._get_departure_city():
        return "Which city are you flying from?"
    elif not self._get_arrival_city():
        return "Where are you headed?"
    elif self._is_roundtrip() and not self._get_return_date():
        return "When would you like to return?"
```

### Contextual Variations
```python
# First time asking
prompts = {
    "name": ["May I have your name?", "Who am I booking this for?"],
    "departure": ["Which city are you flying from?", "Where will you be departing from?"],
    "destination": ["Where are you headed?", "What's your destination?"]
}

# After correction
correction_prompts = {
    "name": "Could you spell your name for me?",
    "departure": "Which city did you want to fly from?",
    "destination": "Where did you want to go instead?"
}
```

## Advanced Flow Management

### State Persistence
```python
class EnhancedBookingInfo:
    """Maintains conversation state with confidence scores"""
    
    def update_with_confidence(self, field: str, value: Any, confidence: float):
        """Track information with certainty levels"""
        self.data[field] = {
            "value": value,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "source": "user_input"
        }
```

### Conditional Branching
```python
def _handle_flexible_search(self, user_input: str):
    """Handle requests for flexible dates/options"""
    
    if "cheapest" in user_input.lower():
        return self._search_by_price()
    elif "fastest" in user_input.lower():
        return self._search_by_duration()
    elif "flexible" in user_input.lower():
        return self._show_flexible_options()
```

### Recovery Strategies
```python
def _handle_confusion(self):
    """When conversation gets off track"""
    
    attempts = self.context.get('confusion_count', 0)
    
    if attempts == 0:
        return "Let me make sure I understand what you're looking for..."
    elif attempts == 1:
        return "Let's start over. What trip would you like to book?"
    else:
        return "I'll connect you with a human agent who can help better."
```

## User Prompt Strategies

### Progressive Disclosure
Don't overwhelm users with all options at once:
```python
# Initial options (simplified)
"I found 3 flights for you. Would you like to hear them?"

# Detailed presentation (after confirmation)
"Option 1: United flight 523, departing 7:15 AM, nonstop, 
 arriving 3:30 PM, priced at $289"
```

### Implicit Confirmation
Confirm information naturally in conversation:
```python
# Instead of: "You said San Francisco. Is that correct?"
# Use: "Great! Flying from San Francisco. Where to?"
```

### Smart Defaults
```python
def apply_smart_defaults(self):
    """Apply reasonable defaults when appropriate"""
    
    if not self.booking_info.trip.trip_type:
        # Most bookings are round trip
        self.booking_info.update_trip_info(
            "trip_type", "roundtrip", 
            confidence=0.7, source="default"
        )
```

## Testing Branching Flows

### Flow Coverage Testing
```python
test_scenarios = [
    {
        "name": "Happy Path",
        "inputs": ["John", "NYC", "LA", "round trip", "tomorrow", "next week"],
        "expected_states": ["GREETING", "COLLECTING_NAME", "COLLECTING_DEPARTURE", ...]
    },
    {
        "name": "With Corrections",
        "inputs": ["John", "NYC", "Actually Chicago", "LA", "one way", "tomorrow"],
        "expected_corrections": 1
    },
    {
        "name": "Skip Ahead",
        "inputs": ["I need a flight from NYC to LA tomorrow"],
        "expected_states": ["GREETING", "PRESENTING_OPTIONS"]
    }
]
```

### Intent Recognition Accuracy
```python
# Test intent recognition with various phrasings
test_phrases = {
    "confirm_yes": ["yes", "yeah", "sure", "sounds good", "yep", "definitely"],
    "confirm_no": ["no", "nope", "not really", "nah", "negative"],
    "correction": ["actually", "wait", "sorry I meant", "change that to"]
}
```

## Best Practices

### 1. Always Maintain Context
```python
# Keep conversation history
self.conversation_history.append({
    "role": "user", 
    "content": user_input,
    "state": self.state.value,
    "timestamp": datetime.now()
})
```

### 2. Graceful Degradation
```python
# Fallback when intent recognition fails
if intent_confidence < 0.5:
    return self._use_rule_based_processing(user_input)
```

### 3. Clear State Transitions
```python
def _transition_state(self, new_state: BookingState, reason: str):
    """Log all state changes for debugging"""
    logger.info(f"State: {self.state} → {new_state} ({reason})")
    self.state = new_state
```

### 4. User-Centric Design
- Allow corrections at any point
- Support non-linear information provision
- Remember context throughout conversation
- Provide clear next steps

## Common Patterns and Solutions

### Pattern: Information Overload
**Problem**: User provides too much info at once
**Solution**: Process all, confirm key points
```python
"Perfect! Let me make sure I have everything: Round trip from 
San Francisco to New York, departing August 10th. When do you return?"
```

### Pattern: Ambiguous Intent
**Problem**: Unclear what user wants
**Solution**: Clarifying questions
```python
"I want to help you with that. Are you looking to book a new flight, 
or check on an existing reservation?"
```

### Pattern: Loop Detection
**Problem**: Conversation going in circles
**Solution**: Break the loop with different approach
```python
if self._detect_loop():
    return "Let me try a different approach. What's the most important 
            thing you need help with right now?"
```

---

*For implementation details, see [component-architecture.md](./component-architecture.md)*