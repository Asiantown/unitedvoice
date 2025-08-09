#!/usr/bin/env python3
"""
Fallback LLM service for when Groq API is unavailable
Provides basic but functional responses to keep the booking flow working
"""

import random
from typing import Dict, List
from src.core.booking_flow import BookingState

class FallbackLLMService:
    """Provides basic responses when primary LLM is unavailable"""
    
    def __init__(self):
        self.responses = {
            # Greeting responses
            "greeting": [
                "Hi! I'd be happy to help you book a flight today.",
                "Welcome to United Airlines! Let's find you the perfect flight.",
                "Hello! Ready to plan your next trip? I'm here to help."
            ],
            
            # Name collection
            "ask_name": [
                "Great! What's your name so I can help you today?",
                "Perfect! Could you tell me your name please?",
                "Wonderful! What name should I use for your booking?"
            ],
            
            # Trip information
            "ask_departure": [
                "Where will you be flying from today?",
                "What city are you departing from?",
                "Which airport will you be leaving from?"
            ],
            
            "ask_destination": [
                "And where would you like to go?",
                "What's your destination city?",
                "Where are you headed?"
            ],
            
            "ask_date": [
                "When would you like to travel?",
                "What date are you thinking for your departure?",
                "When do you want to fly?"
            ],
            
            "ask_return": [
                "When would you like to return?",
                "What date for your return flight?",
                "When should I book your return trip?"
            ],
            
            # Flight options
            "presenting_options": [
                "Great! I found some flights for you. Let me show you the options.",
                "Perfect! Here are the flights available for your trip.",
                "Excellent! I have several flight options for you to choose from."
            ],
            
            # Selection
            "flight_selected": [
                "Excellent choice! That's a great flight.",
                "Perfect! I'll book that flight for you.",
                "Great selection! Let me get that reserved for you."
            ],
            
            # Confirmation
            "booking_complete": [
                "Wonderful! Your flight is booked. Have a fantastic trip!",
                "All set! Your booking is confirmed. Safe travels!",
                "Perfect! Everything is booked. Looking forward to having you fly with us!"
            ],
            
            # Error handling
            "clarification": [
                "I want to make sure I have that right. Could you repeat that for me?",
                "Just to confirm, could you say that again?",
                "I want to get this perfect for you. Could you repeat that please?"
            ],
            
            "general_help": [
                "I'm here to help you book a flight. What would you like to do?",
                "Let me help you find the perfect flight. What are you looking for?",
                "I'd be happy to assist with your travel plans. How can I help?"
            ]
        }
        
        # State-specific prompts  
        self.state_responses = {
            BookingState.IDLE: "greeting",
            BookingState.GREETING: "ask_name",
            BookingState.COLLECTING_NAME: "ask_departure", 
            BookingState.COLLECTING_DEPARTURE: "ask_destination",
            BookingState.COLLECTING_DESTINATION: "ask_date",
            BookingState.COLLECTING_DATE: "ask_return",
            BookingState.COLLECTING_RETURN_DATE: "presenting_options",
            BookingState.PRESENTING_OPTIONS: "flight_selected",
            BookingState.CONFIRMING_SELECTION: "booking_complete",
            BookingState.BOOKING_COMPLETE: "booking_complete"
        }
    
    def get_response(self, user_input: str, state: BookingState, 
                    booking_response: str, context: Dict = None) -> str:
        """Generate a basic response based on state and input"""
        
        user_lower = user_input.lower()
        
        # Handle specific user intents
        if any(word in user_lower for word in ["hello", "hi", "hey"]):
            return random.choice(self.responses["greeting"])
        
        if any(word in user_lower for word in ["help", "confused", "what"]):
            return random.choice(self.responses["general_help"])
        
        if "sorry" in user_lower or "didn't hear" in user_lower:
            return random.choice(self.responses["clarification"])
        
        # Use booking flow response if it looks good
        if booking_response and len(booking_response) > 10:
            # If the booking response is substantial, use it with basic enhancement
            if state == BookingState.PRESENTING_OPTIONS:
                if "Option" in booking_response:
                    return f"Perfect! {booking_response} Which one would you prefer?"
                else:
                    return booking_response
            else:
                return booking_response
        
        # Fallback to state-based responses
        response_category = self.state_responses.get(state, "general_help")
        response = random.choice(self.responses[response_category])
        
        # Add context if available
        if context and "customer_name" in context:
            response = response.replace("you", context["customer_name"]).replace("your", f"{context['customer_name']}'s")
        
        return response
    
    def enhance_booking_response(self, booking_response: str, state: BookingState) -> str:
        """Add natural language enhancements to booking flow responses"""
        
        if not booking_response:
            return self.get_response("", state, booking_response)
        
        # Add natural transitions based on state
        if state == BookingState.COLLECTING_NAME:
            if "name" in booking_response.lower():
                return f"Great! {booking_response}"
        
        elif state == BookingState.PRESENTING_OPTIONS:
            if "flight" in booking_response.lower():
                transitions = ["Excellent!", "Perfect!", "Great news!", "Wonderful!"]
                return f"{random.choice(transitions)} {booking_response}"
        
        elif state == BookingState.CONFIRMING_SELECTION:
            transitions = ["Perfect choice!", "Excellent selection!", "Great pick!"]
            return f"{random.choice(transitions)} {booking_response}"
        
        return booking_response

def create_simple_llm_client(fallback_service: FallbackLLMService = None):
    """Create a simple LLM client that works without external APIs"""
    
    if not fallback_service:
        fallback_service = FallbackLLMService()
    
    class SimpleLLMClient:
        def __init__(self):
            self.fallback = fallback_service
            
        def chat(self, messages: List[Dict], model: str = None, temperature: float = 0.7) -> Dict:
            """Simple chat implementation using template responses"""
            
            # Get the last user message
            user_message = ""
            system_message = ""
            
            for msg in messages:
                if msg["role"] == "user":
                    user_message = msg["content"]
                elif msg["role"] == "system":
                    system_message = msg["content"]
            
            # Extract context from system message
            context = {}
            if "Customer:" in system_message:
                # Try to extract customer name
                import re
                name_match = re.search(r"Customer: ([^;,\n]+)", system_message)
                if name_match:
                    context["customer_name"] = name_match.group(1).strip()
            
            # Generate a simple response
            response_text = self.fallback.get_response(
                user_message, 
                BookingState.IDLE,  # Default state
                "",
                context
            )
            
            return {
                "message": {
                    "content": response_text
                },
                "usage": {"total_tokens": 10},  # Mock usage
                "model": "fallback-simple"
            }
        
        def test_connection(self):
            """Always return success for fallback client"""
            return True, "Fallback LLM ready"
    
    return SimpleLLMClient()

if __name__ == "__main__":
    # Test the fallback service
    print("🧪 Testing Fallback LLM Service")
    print("=" * 50)
    
    fallback = FallbackLLMService()
    
    test_cases = [
        ("Hello", BookingState.IDLE),
        ("My name is John", BookingState.COLLECTING_NAME),
        ("I want to go to New York", BookingState.COLLECTING_DESTINATION),
        ("Next Friday", BookingState.COLLECTING_DATE),
        ("I'll take the first option", BookingState.PRESENTING_OPTIONS)
    ]
    
    for user_input, state in test_cases:
        response = fallback.get_response(user_input, state, "")
        print(f"User: '{user_input}' (State: {state.value})")
        print(f"Bot: '{response}'")
        print()
    
    # Test simple LLM client
    print("🤖 Testing Simple LLM Client")
    print("=" * 50)
    
    client = create_simple_llm_client(fallback)
    messages = [
        {"role": "system", "content": "You are a helpful booking assistant."},
        {"role": "user", "content": "I need to book a flight"}
    ]
    
    response = client.chat(messages)
    print(f"Response: {response['message']['content']}")