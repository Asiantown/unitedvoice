#!/usr/bin/env python3
"""
Test if empty input triggers automatic greeting
"""

import sys
import os
sys.path.append('/Users/ryanyin/united-voice-agent')

# Mock sounddevice to avoid import error
import sys
sys.modules['sounddevice'] = type('MockModule', (), {})()

from src.core.booking_flow import BookingFlow, BookingState

def test_greeting_triggers():
    """Test what triggers the greeting"""
    print("🧪 Testing Booking Flow Greeting Triggers")
    print("=" * 50)
    
    # Create a booking flow
    flow = BookingFlow()
    print(f"Initial state: {flow.state}")
    
    # Test empty input
    print("\n1. Testing empty string input:")
    try:
        response = flow.process_input_with_intent("")
        print(f"   Response: '{response}'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Reset flow
    flow = BookingFlow()
    
    # Test None input
    print("\n2. Testing None input:")
    try:
        response = flow.process_input_with_intent(None)
        print(f"   Response: '{response}'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Reset flow
    flow = BookingFlow()
    
    # Test whitespace input
    print("\n3. Testing whitespace input:")
    try:
        response = flow.process_input_with_intent("   ")
        print(f"   Response: '{response}'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Reset flow
    flow = BookingFlow()
    
    # Test if just creating flow generates anything
    print("\n4. Testing flow creation:")
    print(f"   State after creation: {flow.state}")
    print(f"   Any automatic responses? No - creation doesn't generate responses")
    
    # Test the _handle_greeting method directly
    print("\n5. Testing _handle_greeting directly with empty input:")
    flow = BookingFlow()
    try:
        response = flow._handle_greeting("")
        print(f"   Response: '{response}'")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_greeting_triggers()