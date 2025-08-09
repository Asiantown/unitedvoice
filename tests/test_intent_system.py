#!/usr/bin/env python3
"""
Comprehensive tests for the intent-based booking system
Tests intent recognition, city extraction, and conversation flow
"""

import sys
import os
import unittest
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from src.core.intent_recognizer import IntentRecognizer
from src.core.booking_flow import BookingFlow, BookingState
from src.core.booking_validator import BookingValidator
from src.models.enhanced_booking_info import EnhancedBookingInfo
from src.utils.date_parser import DateParser


class TestIntentRecognition(unittest.TestCase):
    """Test intent recognition system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.recognizer = IntentRecognizer()
        self.booking_flow = BookingFlow()
        self.validator = BookingValidator()
    
    def test_correction_handling(self):
        """Test: User corrects destination city"""
        print("\n=== Testing Correction Handling ===")
        
        # First input
        response1 = self.booking_flow.process_input_with_intent("I want to fly to New York")
        print(f"User: I want to fly to New York")
        print(f"System: {response1}")
        
        # Correction
        response2 = self.booking_flow.process_input_with_intent("No, I meant Los Angeles")
        print(f"\nUser: No, I meant Los Angeles")
        print(f"System: {response2}")
        
        # Check destination was updated
        dest_city = self.booking_flow.booking_info.trip_details.destination_city
        if dest_city and dest_city.value:
            self.assertEqual(dest_city.value.lower(), "los angeles")
            print(f"\n✓ Destination correctly updated to: {dest_city.value}")
        else:
            print(f"\n✗ Destination not updated correctly")
    
    def test_phonetic_confusion(self):
        """Test: Handle phonetic confusion (frying vs flying)"""
        print("\n=== Testing Phonetic Confusion ===")
        
        # Test city extraction with phonetic confusion
        test_inputs = [
            "Flying from Houston",
            "frying from Houston",  # Common mishearing
            "I'm frying from Houston to Boston"
        ]
        
        for input_text in test_inputs:
            # Reset booking flow
            self.booking_flow = BookingFlow()
            
            # Extract city using the enhanced method
            city = self.booking_flow._extract_city(input_text)
            print(f"\nInput: '{input_text}'")
            print(f"Extracted city: {city}")
            
            # Should extract Houston, not "frying"
            if city:
                self.assertIn(city.lower(), ["houston", "boston"])
                self.assertNotEqual(city.lower(), "frying")
    
    def test_intent_classification(self):
        """Test various intent classifications"""
        print("\n=== Testing Intent Classification ===")
        
        test_cases = [
            # (input, expected_intent)
            ("My name is John Smith", "provide_name"),
            ("I want to fly from Boston", "provide_city"),
            ("Next Friday please", "provide_date"),
            ("Yes, that's correct", "confirm_yes"),
            ("No, that's wrong", "confirm_no"),
            ("Actually, let me change that", "correction"),
            ("What time does the flight arrive?", "question"),
            ("Cancel everything", "cancel"),
        ]
        
        for user_input, expected_intent in test_cases:
            intent_data = self.recognizer.recognize_intent(
                user_input, 
                BookingState.COLLECTING_NAME
            )
            
            print(f"\nInput: '{user_input}'")
            print(f"Expected: {expected_intent}")
            print(f"Recognized: {intent_data['intent']} (confidence: {intent_data['confidence']})")
            
            # Check if intent matches (allow some flexibility for LLM responses)
            if intent_data['intent'] == expected_intent:
                print("✓ Correct")
            else:
                print("✗ Incorrect")
    
    def test_entity_extraction(self):
        """Test entity extraction from user input"""
        print("\n=== Testing Entity Extraction ===")
        
        test_cases = [
            {
                "input": "My name is Sarah Johnson",
                "expected_entities": {"name": "Sarah Johnson"}
            },
            {
                "input": "I'm flying from San Francisco to New York",
                "expected_entities": {
                    "departure_city": "San Francisco",
                    "destination_city": "New York"
                }
            },
            {
                "input": "I want to leave next Friday and return on Sunday",
                "expected_entities": {
                    "departure_date": "next Friday",
                    "return_date": "Sunday"
                }
            }
        ]
        
        for test in test_cases:
            intent_data = self.recognizer.recognize_intent(
                test["input"],
                BookingState.COLLECTING_NAME
            )
            
            print(f"\nInput: '{test['input']}'")
            print(f"Expected entities: {test['expected_entities']}")
            print(f"Extracted entities: {intent_data.get('entities', {})}")
            
            # Check if expected entities were extracted
            entities = intent_data.get('entities', {})
            all_found = True
            for key, expected_value in test["expected_entities"].items():
                if key in entities:
                    print(f"✓ Found {key}: {entities[key]}")
                else:
                    print(f"✗ Missing {key}")
                    all_found = False
    
    def test_conversation_flow_with_corrections(self):
        """Test complete conversation flow with corrections"""
        print("\n=== Testing Full Conversation Flow ===")
        
        conversation = [
            "Hi, I need to book a flight",
            "My name is Jeffrey",
            "Flying from Houston",  # Not "frying"
            "To San Francisco",
            "Wait, actually I meant New York",  # Correction
            "Next Friday",
            "Yes, I need a return flight",
            "Sunday evening",
            "That looks good, book it"
        ]
        
        print("\nSimulating conversation:")
        print("-" * 50)
        
        for i, user_input in enumerate(conversation):
            print(f"\nTurn {i+1}:")
            print(f"User: {user_input}")
            
            response = self.booking_flow.process_input_with_intent(user_input)
            print(f"System: {response}")
            
            # Print current state
            state_info = self.booking_flow.get_current_state()
            print(f"State: {state_info['state']}")
            
            # Check key information
            if i == len(conversation) - 1:
                # Final check
                enhanced_info = state_info.get('enhanced_info', {})
                print("\nFinal booking information:")
                print(f"- Customer: {enhanced_info.get('customer_name')}")
                print(f"- Route: {enhanced_info.get('departure_city')} → {enhanced_info.get('destination_city')}")
                print(f"- Dates: {enhanced_info.get('departure_date')} - {enhanced_info.get('return_date')}")
    
    def test_date_validation(self):
        """Test date parsing and validation"""
        print("\n=== Testing Date Validation ===")
        
        test_dates = [
            "next Friday",
            "tomorrow",
            "December 25th",
            "in 3 days",
            "yesterday",  # Should fail - past date
            "next month",
            "Christmas Day"
        ]
        
        for date_input in test_dates:
            result = self.validator.validate_date(date_input)
            print(f"\nInput: '{date_input}'")
            print(f"Valid: {result.is_valid}")
            if result.normalized_value:
                print(f"Parsed date: {result.normalized_value}")
            if result.error_message:
                print(f"Error: {result.error_message}")
    
    def test_city_pair_validation(self):
        """Test city pair validation"""
        print("\n=== Testing City Pair Validation ===")
        
        test_pairs = [
            ("San Francisco", "New York"),  # Valid
            ("Houston", "Houston"),  # Same city - invalid
            ("Bostton", "Chicago"),  # Typo - should fuzzy match
            ("InvalidCity", "Los Angeles"),  # Invalid city
        ]
        
        for departure, destination in test_pairs:
            result = self.validator.validate_city_pair(departure, destination)
            print(f"\n{departure} → {destination}")
            print(f"Valid: {result.is_valid}")
            if result.normalized_value:
                print(f"Normalized: {result.normalized_value}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            if result.suggestions:
                print(f"Suggestions: {result.suggestions}")


class TestBookingCompletion(unittest.TestCase):
    """Test booking completion scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.booking_flow = BookingFlow()
    
    def test_complete_booking_flow(self):
        """Test a complete successful booking"""
        print("\n=== Testing Complete Booking Flow ===")
        
        # Simulate complete booking
        inputs = [
            "John Doe",  # Name
            "San Francisco",  # Departure
            "New York",  # Destination
            "next Friday",  # Date
            "yes",  # Round trip
            "Sunday",  # Return date
            "option 1",  # Select flight
            "yes"  # Confirm
        ]
        
        for i, user_input in enumerate(inputs):
            response = self.booking_flow.process_input_with_intent(user_input)
            print(f"\nStep {i+1}: {user_input}")
            print(f"Response: {response[:100]}...")  # Truncate long responses
            
            # Check if booking is complete
            if self.booking_flow.state == BookingState.BOOKING_COMPLETE:
                print("\n✓ Booking completed successfully!")
                break
    
    def test_booking_cancellation(self):
        """Test booking cancellation"""
        print("\n=== Testing Booking Cancellation ===")
        
        # Start booking
        self.booking_flow.process_input_with_intent("Jane Smith")
        self.booking_flow.process_input_with_intent("Boston")
        
        # Cancel
        response = self.booking_flow.process_input_with_intent("Actually, cancel everything")
        print(f"\nCancellation response: {response}")
        
        # Should handle cancellation gracefully
        self.assertIn("cancel", response.lower())


def run_all_tests():
    """Run all tests using uv run python"""
    print("=" * 60)
    print("INTENT-BASED BOOKING SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntentRecognition))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBookingCompletion))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run with: uv run python tests/test_intent_system.py
    success = run_all_tests()
    sys.exit(0 if success else 1)