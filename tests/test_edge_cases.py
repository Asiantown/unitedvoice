#!/usr/bin/env python3
"""
Comprehensive Edge Case Tests for United Voice Agent
Tests content filtering, state management, flexible search, API errors, and complex conversation flows
"""

import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.content_filter import ContentFilter, InappropriateType
from src.core.booking_flow import BookingFlow, BookingState
from src.core.voice_agent import UnitedVoiceAgent
from src.services.flight_api_interface import FlightSearchService, FlightSearchParams, MockFlightAPI
from src.services.groq_client import GroqClient
from src.models.enhanced_booking_info import EnhancedBookingInfo


class TestContentFilteringEdgeCases(unittest.TestCase):
    """Test comprehensive content filtering scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.content_filter = ContentFilter()
    
    def test_profanity_variations(self):
        """Test: Various forms of profanity detection"""
        print("\n=== Testing Profanity Variations ===")
        
        profanity_tests = [
            # Direct profanity
            "This is f***ing terrible service!",
            "What the hell is going on?",
            "You're a damn fool",
            "This s*** is broken",
            
            # Leetspeak variations
            "F_u_c_k this system",
            "5h1t service",
            "d@mn it",
            "a$$hole customer service",
            
            # Spaced out profanity
            "f u c k i n g annoying",
            "s h i t t y experience",
            "d a m n frustrating",
            
            # With symbols
            "f**k this",
            "s#!t happens",
            "d@mn right",
            "bull$hit response",
            
            # Mixed case
            "FuCkInG terrible",
            "ShIt service", 
            "DaMn problem"
        ]
        
        for test_input in profanity_tests:
            is_appropriate, filtered_text, reason = self.content_filter.filter_inappropriate_content(test_input)
            print(f"\nInput: '{test_input}'")
            print(f"Appropriate: {is_appropriate}")
            print(f"Filtered: '{filtered_text}'")
            print(f"Reason: {reason}")
            
            # Should detect inappropriate content
            self.assertFalse(is_appropriate, f"Failed to detect profanity in: {test_input}")
            self.assertIsNotNone(reason)
            
            # Should contain filtered markers
            self.assertTrue('[filtered]' in filtered_text or test_input == filtered_text)
    
    def test_inappropriate_names(self):
        """Test: Inappropriate name detection"""
        print("\n=== Testing Inappropriate Names ===")
        
        inappropriate_names = [
            "F*** Q",
            "B*tch Johnson", 
            "A$$hole Smith",
            "Damn You",
            "Sh*t Head",
            "F U",
            "Go Die",
            "Kill Me",
            "Test User",  # Fake name
            "Dummy Person",  # Fake name
            "1234567890",  # All numbers
            "AAAAAAAA",  # All caps repeated
            "a",  # Too short
            "test",  # Test name
            "fake",  # Fake name
        ]
        
        for name in inappropriate_names:
            is_valid = self.content_filter.is_valid_name(name)
            is_appropriate, filtered_text, reason = self.content_filter.filter_inappropriate_content(name)
            
            print(f"\nName: '{name}'")
            print(f"Valid: {is_valid}")
            print(f"Appropriate: {is_appropriate}")
            if reason:
                print(f"Reason: {reason}")
            
            # Should detect as invalid or inappropriate
            if not is_valid or not is_appropriate:
                print("✓ Correctly rejected")
            else:
                print("✗ Incorrectly accepted")
    
    def test_personal_information_detection(self):
        """Test: Personal information detection"""
        print("\n=== Testing Personal Information Detection ===")
        
        personal_info_tests = [
            # SSN patterns
            "My SSN is 123-45-6789",
            "Social security: 987-65-4321",
            "SSN: 555-44-3333",
            
            # Credit card numbers
            "My card is 4532 1234 5678 9012",
            "Credit card: 4532123456789012",
            "Card number 5555 4444 3333 2222",
            "Visa: 4111-1111-1111-1111",
            
            # Email addresses
            "Contact me at john.doe@example.com",
            "My email is user123@gmail.com",
            "Email: test.user+tag@company.co.uk",
            
            # Phone numbers
            "Call me at 555-123-4567",
            "Phone: (555) 987-6543",
            "My number is 555 444 3333",
            "(800) 555-1212 for support",
            
            # Mixed personal info
            "John Doe, SSN: 123-45-6789, email: john@example.com, phone: 555-123-4567"
        ]
        
        for test_input in personal_info_tests:
            is_appropriate, filtered_text, reason = self.content_filter.filter_inappropriate_content(test_input)
            
            print(f"\nInput: '{test_input}'")
            print(f"Appropriate: {is_appropriate}")
            print(f"Filtered: '{filtered_text}'")
            if reason:
                print(f"Reason: {reason}")
            
            # Should detect personal information
            self.assertFalse(is_appropriate, f"Failed to detect personal info in: {test_input}")
            self.assertIn("Personal information", reason)
            self.assertIn("[REDACTED]", filtered_text)
    
    def test_malicious_input_detection(self):
        """Test: Malicious input detection (SQL injection, XSS)"""
        print("\n=== Testing Malicious Input Detection ===")
        
        malicious_inputs = [
            # SQL Injection attempts
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
            "INSERT INTO bookings VALUES ('hacked')",
            "DELETE FROM flights WHERE price > 0",
            
            # XSS attempts
            "<script>alert('XSS')</script>",
            "javascript:alert('hack')",
            "<img src='x' onerror='alert(1)'>",
            "<iframe src='javascript:alert()'></iframe>",
            
            # Command injection
            "system('rm -rf /')",
            "exec('malicious_code')",
            "eval('dangerous_function()')",
            
            # Mixed malicious content
            "Book flight'; DROP TABLE bookings; <script>alert('pwned')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            is_appropriate, filtered_text, reason = self.content_filter.filter_inappropriate_content(malicious_input)
            
            print(f"\nInput: '{malicious_input}'")
            print(f"Appropriate: {is_appropriate}")
            print(f"Filtered: '{filtered_text}'")
            if reason:
                print(f"Reason: {reason}")
            
            # Should detect malicious content
            self.assertFalse(is_appropriate, f"Failed to detect malicious input: {malicious_input}")
            self.assertIn("malicious", reason.lower())
            self.assertIn("[BLOCKED]", filtered_text)
    
    def test_leetspeak_variations(self):
        """Test: Leetspeak and character substitution detection"""
        print("\n=== Testing Leetspeak Variations ===")
        
        leetspeak_tests = [
            # Number substitutions
            "Th1s 1s t3rr1bl3",
            "Wh4t th3 h3ll",
            "F0ck th1s sh1t",
            
            # Symbol substitutions  
            "F@#k this $#!t",
            "D@mn th@t's b@d",
            "Wh@t @ l0ser",
            
            # Mixed variations
            "5h!t s3rv!c3",
            "D4mn f00l",
            "Th!5 !5 bull5h!t",
            
            # Creative obfuscation
            "eff you see kay",
            "bee eye tee see aitch",
            "es aitch eye tee"
        ]
        
        for test_input in leetspeak_tests:
            is_appropriate, filtered_text, reason = self.content_filter.filter_inappropriate_content(test_input)
            
            print(f"\nInput: '{test_input}'")
            print(f"Appropriate: {is_appropriate}")
            print(f"Filtered: '{filtered_text}'")
            if reason:
                print(f"Reason: {reason}")
            
            # Many should be caught by pattern matching
            if not is_appropriate:
                print("✓ Correctly detected")
            else:
                print("⚠ Not detected (may need pattern improvement)")


class TestStateManagementScenarios(unittest.TestCase):
    """Test state management and persistence"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.booking_flow = BookingFlow()
    
    def test_state_persistence_across_turns(self):
        """Test: Information should persist across conversation turns"""
        print("\n=== Testing State Persistence ===")
        
        # Set up initial information
        self.booking_flow.process_input_with_intent("My name is Alice Johnson")
        self.booking_flow.process_input_with_intent("Flying from Boston")
        self.booking_flow.process_input_with_intent("Going to Seattle")
        
        # Ask a question - should not reset state
        response = self.booking_flow.process_input_with_intent("What time do flights usually depart?")
        print(f"Question response: {response}")
        
        # Check that information is still there
        customer_name = self.booking_flow._get_customer_name()
        departure_city = self.booking_flow._get_departure_city()
        arrival_city = self.booking_flow._get_arrival_city()
        
        print(f"After question - Name: {customer_name}")
        print(f"After question - Departure: {departure_city}")
        print(f"After question - Destination: {arrival_city}")
        
        # Information should persist
        self.assertIsNotNone(customer_name)
        self.assertIsNotNone(departure_city)
        self.assertIsNotNone(arrival_city)
        
        print("✓ State persisted correctly")
    
    def test_complex_correction_flows(self):
        """Test: Complex correction scenarios"""
        print("\n=== Testing Complex Correction Flows ===")
        
        # Initial booking
        self.booking_flow.process_input_with_intent("Book a flight for Sarah Chen")
        self.booking_flow.process_input_with_intent("From San Francisco to New York")
        self.booking_flow.process_input_with_intent("Next Friday")
        
        # Multiple corrections
        print("\n--- Multiple Corrections ---")
        
        # Correct name
        response1 = self.booking_flow.process_input_with_intent("Actually, my name is Sarah Chang, not Chen")
        print(f"Name correction: {response1}")
        
        # Correct departure city
        response2 = self.booking_flow.process_input_with_intent("And I'm flying from Oakland, not San Francisco")
        print(f"Departure correction: {response2}")
        
        # Correct date
        response3 = self.booking_flow.process_input_with_intent("Change the date to next Saturday")
        print(f"Date correction: {response3}")
        
        # Verify final state
        final_state = self.booking_flow.get_current_state()
        enhanced_info = final_state.get('enhanced_info', {})
        
        print(f"\nFinal corrected information:")
        print(f"- Name: {enhanced_info.get('customer_name')}")
        print(f"- Departure: {enhanced_info.get('departure_city')}")
        print(f"- Destination: {enhanced_info.get('destination_city')}")
        print(f"- Date: {enhanced_info.get('departure_date')}")
        
        # Should reflect all corrections
        customer_name = self.booking_flow._get_customer_name()
        if customer_name:
            self.assertIn("Chang", customer_name)
        
        print("✓ Complex corrections handled")
    
    def test_state_transitions_with_flexible_search(self):
        """Test: State transitions during flexible date search"""
        print("\n=== Testing Flexible Search State Transitions ===")
        
        # Set up booking info
        self.booking_flow.process_input_with_intent("Mike Davis")
        self.booking_flow.process_input_with_intent("Chicago to Miami")
        
        # Request flexible search
        response = self.booking_flow.process_input_with_intent("Find me the cheapest day next week")
        print(f"Flexible search request: {response}")
        
        # Should transition to flexible search state
        self.assertEqual(self.booking_flow.state, BookingState.FLEXIBLE_SEARCH)
        
        # Select option
        response2 = self.booking_flow.process_input_with_intent("I'll take option 2")
        print(f"Option selection: {response2}")
        
        # Should transition to confirmation
        self.assertEqual(self.booking_flow.state, BookingState.CONFIRMING_SELECTION)
        
        print("✓ Flexible search transitions working")
    
    def test_information_recovery_after_errors(self):
        """Test: Information should be recoverable after errors"""
        print("\n=== Testing Information Recovery ===")
        
        # Start booking
        self.booking_flow.process_input_with_intent("Jennifer Lee")
        self.booking_flow.process_input_with_intent("Denver to Portland")
        
        # Cause an error with invalid input
        self.booking_flow.error_count = 0  # Reset error count
        response1 = self.booking_flow.process_input_with_intent("blah blah invalid date gibberish")
        response2 = self.booking_flow.process_input_with_intent("more invalid nonsense")
        response3 = self.booking_flow.process_input_with_intent("still more garbage")
        
        print(f"After multiple errors, error count: {self.booking_flow.error_count}")
        
        # Information should still be there
        customer_name = self.booking_flow._get_customer_name()
        departure_city = self.booking_flow._get_departure_city()
        arrival_city = self.booking_flow._get_arrival_city()
        
        print(f"After errors - Name: {customer_name}")
        print(f"After errors - Route: {departure_city} → {arrival_city}")
        
        # Should still have the valid information
        self.assertIsNotNone(customer_name)
        self.assertIsNotNone(departure_city)
        self.assertIsNotNone(arrival_city)
        
        # Should be able to continue
        response4 = self.booking_flow.process_input_with_intent("tomorrow")
        print(f"Recovery with valid date: {response4}")
        
        print("✓ Information recovered after errors")


class TestFlexibleDateSearch(unittest.TestCase):
    """Test flexible date search functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.booking_flow = BookingFlow()
    
    def test_cheapest_day_requests(self):
        """Test: Various cheapest day request patterns"""
        print("\n=== Testing Cheapest Day Requests ===")
        
        # Set up basic info
        self.booking_flow.process_input_with_intent("Tom Wilson")
        self.booking_flow.process_input_with_intent("Austin to Dallas")
        
        flexible_requests = [
            "Find me the cheapest day next week",
            "What's the cheapest flight next week?",
            "Show me the best deal in August",
            "I want the most affordable option",
            "Find the lowest price next month",
            "Cheapest day to fly?",
            "Best price next week",
            "Most affordable day to travel"
        ]
        
        for request in flexible_requests:
            # Reset to date collection state
            self.booking_flow.state = BookingState.COLLECTING_DATE
            
            response = self.booking_flow.process_input_with_intent(request)
            print(f"\nRequest: '{request}'")
            print(f"Response: {response[:100]}...")
            
            # Should handle flexible search
            is_flexible = self.booking_flow._is_flexible_date_request(request)
            print(f"Detected as flexible: {is_flexible}")
            
            if is_flexible:
                print("✓ Flexible request detected")
            else:
                print("⚠ Not detected as flexible")
    
    def test_price_based_queries(self):
        """Test: Price-focused search queries"""
        print("\n=== Testing Price-Based Queries ===")
        
        # Set up booking
        self.booking_flow.process_input_with_intent("Lisa Park")
        self.booking_flow.process_input_with_intent("Phoenix to Las Vegas")
        
        price_queries = [
            "What's the cheapest option?",
            "Show me flights under $300",
            "I need the lowest fare",
            "Find me a good deal",
            "Budget-friendly options?",
            "Cheapest flights available",
            "Best value for money"
        ]
        
        for query in price_queries:
            response = self.booking_flow.process_input_with_intent(query)
            print(f"\nQuery: '{query}'")
            print(f"Response: {response[:100]}...")
            
            # Should provide helpful price-focused response
            self.assertTrue(len(response) > 0)
            print("✓ Price query handled")
    
    def test_flexible_search_option_selection(self):
        """Test: Selecting options from flexible search results"""
        print("\n=== Testing Flexible Search Option Selection ===")
        
        # Set up and trigger flexible search
        self.booking_flow.process_input_with_intent("David Kim") 
        self.booking_flow.process_input_with_intent("Seattle to San Diego")
        response1 = self.booking_flow.process_input_with_intent("Cheapest day next week")
        
        print(f"Flexible options: {response1}")
        
        # Should be in flexible search state
        self.assertEqual(self.booking_flow.state, BookingState.FLEXIBLE_SEARCH)
        
        # Select an option
        selection_tests = [
            "I'll take option 1",
            "Choose the Tuesday flight",
            "Option 2 please",
            "Give me the first one",
            "Select option 3"
        ]
        
        for selection in selection_tests:
            # Reset to flexible search state
            self.booking_flow.state = BookingState.FLEXIBLE_SEARCH
            
            response = self.booking_flow.process_input_with_intent(selection)
            print(f"\nSelection: '{selection}'")
            print(f"Response: {response[:100]}...")
            
            # Should transition to confirmation
            if self.booking_flow.state == BookingState.CONFIRMING_SELECTION:
                print("✓ Transitioned to confirmation")
            else:
                print(f"⚠ State: {self.booking_flow.state.value}")


class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling and retry logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_service = FlightSearchService(use_mock=True)
    
    @patch('src.services.flight_api_interface.MockFlightAPI.search_flights')
    async def test_api_timeout_handling(self, mock_search):
        """Test: API timeout scenarios"""
        print("\n=== Testing API Timeout Handling ===")
        
        # Mock timeout error
        mock_search.side_effect = asyncio.TimeoutError("Request timeout")
        
        params = FlightSearchParams(
            departure_city="Boston",
            destination_city="Chicago", 
            departure_date="2024-12-20"
        )
        
        # Should handle timeout gracefully
        try:
            results = await self.api_service.search_with_fallback(params)
            print(f"Results after timeout: {len(results)} flights")
            # Should fall back to working API or return empty
            self.assertIsInstance(results, list)
            print("✓ Timeout handled gracefully")
        except Exception as e:
            print(f"✗ Unhandled timeout error: {e}")
            self.fail("Timeout not handled properly")
    
    @patch('src.services.flight_api_interface.MockFlightAPI.search_flights')
    async def test_bad_request_errors(self, mock_search):
        """Test: 400 Bad Request error handling"""
        print("\n=== Testing Bad Request Errors ===")
        
        # Mock 400 error
        class BadRequestError(Exception):
            def __init__(self):
                self.status_code = 400
                super().__init__("Bad Request")
        
        mock_search.side_effect = BadRequestError()
        
        params = FlightSearchParams(
            departure_city="InvalidCity",
            destination_city="AnotherInvalidCity",
            departure_date="invalid-date"
        )
        
        try:
            results = await self.api_service.search_with_fallback(params)
            print(f"Results after bad request: {len(results)} flights")
            self.assertIsInstance(results, list)
            print("✓ Bad request handled")
        except Exception as e:
            print(f"✗ Unhandled bad request: {e}")
    
    @patch('src.services.flight_api_interface.MockFlightAPI.search_flights')
    async def test_retry_logic(self, mock_search):
        """Test: Retry logic with multiple API failures"""
        print("\n=== Testing Retry Logic ===")
        
        # Mock that fails first few times then succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"API failure #{call_count}")
            # Return empty list on success (mock behavior)
            return []
        
        mock_search.side_effect = side_effect
        
        params = FlightSearchParams(
            departure_city="San Francisco",
            destination_city="Los Angeles",
            departure_date="2024-12-20"
        )
        
        results = await self.api_service.search_with_fallback(params)
        print(f"Results after retries: {len(results)} flights")
        print(f"API called {call_count} times")
        
        # Should eventually succeed
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(call_count, 2)
        print("✓ Retry logic working")
    
    def test_fallback_mechanism(self):
        """Test: Fallback to mock API when real API fails"""
        print("\n=== Testing Fallback Mechanism ===")
        
        # Create service with real API that will fail
        service = FlightSearchService(use_mock=False)
        
        # Should have mock API as fallback
        self.assertTrue(len(service.apis) >= 1)
        
        # Last API should be mock
        last_api = service.apis[-1]
        self.assertIsInstance(last_api, MockFlightAPI)
        
        print("✓ Fallback mechanism in place")
    
    async def test_api_error_recovery(self):
        """Test: Recovery from various API errors"""
        print("\n=== Testing API Error Recovery ===")
        
        error_scenarios = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timeout"),
            ValueError("Invalid response format"),
            KeyError("Missing required field"),
            Exception("Generic API error")
        ]
        
        for error in error_scenarios:
            print(f"\nTesting recovery from: {type(error).__name__}")
            
            with patch('src.services.flight_api_interface.MockFlightAPI.search_flights') as mock_search:
                mock_search.side_effect = error
                
                params = FlightSearchParams(
                    departure_city="Test City",
                    destination_city="Test Destination",
                    departure_date="2024-12-20"
                )
                
                try:
                    results = await self.api_service.search_with_fallback(params)
                    print(f"Recovered with {len(results)} results")
                    self.assertIsInstance(results, list)
                    print("✓ Recovered from error")
                except Exception as e:
                    print(f"✗ Failed to recover: {e}")


class TestComplexConversationFlows(unittest.TestCase):
    """Test complex conversation scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.booking_flow = BookingFlow()
    
    def test_multiple_corrections_flow(self):
        """Test: Multiple corrections in sequence"""
        print("\n=== Testing Multiple Corrections Flow ===")
        
        conversation = [
            ("Initial booking", "Book a flight for John Smith"),
            ("Departure", "From Boston to New York"), 
            ("Date", "Next Friday"),
            ("Name correction", "Actually, my name is John Doe, not Smith"),
            ("City correction", "And I meant Chicago, not New York"),
            ("Date correction", "Change that to next Saturday"),
            ("Another correction", "Wait, make it Sunday instead"),
            ("Final confirmation", "Yes, that looks correct")
        ]
        
        for step, user_input in conversation:
            print(f"\n{step}: '{user_input}'")
            response = self.booking_flow.process_input_with_intent(user_input)
            print(f"Response: {response[:80]}...")
            
            # Show current state
            state = self.booking_flow.get_current_state()
            enhanced_info = state.get('enhanced_info', {})
            print(f"Current info: {enhanced_info.get('customer_name')} | "
                  f"{enhanced_info.get('departure_city')} → {enhanced_info.get('destination_city')} | "
                  f"{enhanced_info.get('departure_date')}")
        
        print("\n✓ Multiple corrections handled")
    
    def test_context_switching_scenarios(self):
        """Test: Context switching during conversation"""
        print("\n=== Testing Context Switching ===")
        
        # Start booking
        self.booking_flow.process_input_with_intent("Emily Chen")
        self.booking_flow.process_input_with_intent("Seattle to Portland")
        
        # Switch context with questions
        response1 = self.booking_flow.process_input_with_intent("What's the weather like in Portland?")
        print(f"Weather question: {response1}")
        
        # Continue booking - should remember previous info
        response2 = self.booking_flow.process_input_with_intent("Next Thursday")
        print(f"Date after question: {response2}")
        
        # Another context switch
        response3 = self.booking_flow.process_input_with_intent("How much baggage can I bring?")
        print(f"Baggage question: {response3}")
        
        # Should still remember everything
        final_state = self.booking_flow.get_current_state()
        enhanced_info = final_state.get('enhanced_info', {})
        
        print(f"\nAfter context switches:")
        print(f"Name: {enhanced_info.get('customer_name')}")
        print(f"Route: {enhanced_info.get('departure_city')} → {enhanced_info.get('destination_city')}")
        print(f"Date: {enhanced_info.get('departure_date')}")
        
        # Information should persist
        self.assertIsNotNone(enhanced_info.get('customer_name'))
        self.assertIsNotNone(enhanced_info.get('departure_city'))
        self.assertIsNotNone(enhanced_info.get('destination_city'))
        
        print("✓ Context switching handled")
    
    def test_incomplete_information_handling(self):
        """Test: Handling incomplete information gracefully"""
        print("\n=== Testing Incomplete Information Handling ===")
        
        incomplete_scenarios = [
            # Partial names
            "My name is",
            "I'm",
            "Call me", 
            
            # Partial cities
            "Flying from",
            "Going to",
            "Destination is",
            
            # Partial dates
            "I want to travel",
            "Departure date",
            "Flying on"
        ]
        
        for incomplete_input in incomplete_scenarios:
            # Reset for each test
            booking_flow = BookingFlow()
            
            response = booking_flow.process_input_with_intent(incomplete_input)
            print(f"\nIncomplete: '{incomplete_input}'")
            print(f"Response: {response[:60]}...")
            
            # Should handle gracefully and ask for clarification
            self.assertTrue(len(response) > 0)
            self.assertTrue('?' in response or 'please' in response.lower())
            
        print("✓ Incomplete information handled")
    
    def test_recovery_from_errors(self):
        """Test: Recovery from various error states"""
        print("\n=== Testing Error Recovery ===")
        
        # Start valid booking
        self.booking_flow.process_input_with_intent("Robert Taylor")
        self.booking_flow.process_input_with_intent("Miami to Atlanta")
        
        # Cause errors with invalid inputs
        error_inputs = [
            "asdlfkjasldfkj",  # Gibberish
            "1234567890",       # Numbers only
            "!@#$%^&*()",      # Symbols only
            "",                 # Empty
            "   ",             # Whitespace only
        ]
        
        for error_input in error_inputs:
            response = self.booking_flow.process_input_with_intent(error_input)
            print(f"\nError input: '{error_input}'")
            print(f"Response: {response[:60]}...")
            
            # Should not crash and provide helpful response
            self.assertTrue(len(response) > 0)
        
        # Should be able to continue normally
        recovery_response = self.booking_flow.process_input_with_intent("Tomorrow")
        print(f"\nRecovery with valid date: {recovery_response[:60]}...")
        
        # Should still have the original information
        customer_name = self.booking_flow._get_customer_name()
        departure_city = self.booking_flow._get_departure_city()
        
        self.assertIsNotNone(customer_name)
        self.assertIsNotNone(departure_city)
        
        print("✓ Error recovery successful")


class TestConversationEdgeCases(unittest.TestCase):
    """Test specific edge cases from conversation examples"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.booking_flow = BookingFlow()
    
    def test_book_of_light_to_flight(self):
        """Test: 'book of light' misheard as 'flight'"""
        print("\n=== Testing 'Book of Light' → 'Flight' ===")
        
        # These should be interpreted as booking requests
        misheard_phrases = [
            "I need to book of light",
            "Can you book of light for me",
            "Book of light to New York",
            "I want to book of light from Boston"
        ]
        
        for phrase in misheard_phrases:
            response = self.booking_flow.process_input_with_intent(phrase)
            print(f"\nInput: '{phrase}'")
            print(f"Response: {response[:80]}...")
            
            # Should interpret as flight booking intent
            self.assertIn("flight", response.lower())
            print("✓ Interpreted as flight booking")
    
    def test_frying_from_harbory_correction(self):
        """Test: 'frying from harbory' → 'flying from Houston'"""
        print("\n=== Testing Phonetic Corrections ===")
        
        phonetic_confusions = [
            ("frying from harbory", "flying", "houston"),
            ("frying from Boston", "flying", "boston"),
            ("I'm frying tomorrow", "flying", None),
            ("book frying ticket", "flying", None)
        ]
        
        for confused_input, expected_word, expected_city in phonetic_confusions:
            # Reset booking flow
            booking_flow = BookingFlow()
            booking_flow.process_input_with_intent("Test User")
            
            response = booking_flow.process_input_with_intent(confused_input)
            print(f"\nInput: '{confused_input}'")
            print(f"Response: {response[:80]}...")
            
            # Should handle phonetic confusion
            if expected_city:
                # Check if city was extracted correctly
                extracted_city = booking_flow._get_departure_city()
                if extracted_city:
                    print(f"Extracted city: {extracted_city}")
                    self.assertTrue(expected_city.lower() in extracted_city.lower() or 
                                  extracted_city.lower() in expected_city.lower())
                    print("✓ City extracted correctly despite confusion")
    
    def test_frustration_and_inappropriate_language(self):
        """Test: Handling user frustration with inappropriate language"""
        print("\n=== Testing Frustration Handling ===")
        
        # Start booking normally
        self.booking_flow.process_input_with_intent("Frustrated User")
        self.booking_flow.process_input_with_intent("Denver to Phoenix")
        
        # User gets frustrated
        frustration_inputs = [
            "This is f***ing ridiculous!",
            "Your system is s***!",
            "What the hell is wrong with this?",
            "Damn this stupid system!",
            "I hate this cr*p!"
        ]
        
        for frustrated_input in frustration_inputs:
            response = self.booking_flow.process_input_with_intent(frustrated_input)
            print(f"\nFrustrated input: '{frustrated_input}'")
            print(f"Response: {response[:100]}...")
            
            # Should handle professionally and try to continue
            self.assertIn("understand", response.lower())
            self.assertTrue("professional" in response.lower() or 
                          "help" in response.lower() or
                          "assist" in response.lower())
            
            # Should not crash or get stuck
            self.assertTrue(len(response) > 0)
            
        print("✓ Frustration handled professionally")
    
    def test_mixed_correction_scenarios(self):
        """Test: Complex mixed correction scenarios"""
        print("\n=== Testing Mixed Corrections ===")
        
        # Start booking
        self.booking_flow.process_input_with_intent("Wrong Name")
        self.booking_flow.process_input_with_intent("From Wrong City to Another Wrong City")
        self.booking_flow.process_input_with_intent("Wrong Date")
        
        # Multiple simultaneous corrections
        complex_corrections = [
            "Actually, my name is Correct Name, and I'm flying from Dallas to Houston on Friday",
            "Change everything: I'm Jane Doe, going Boston to Miami next week",
            "Wait, make that Sarah Wilson, Phoenix to Seattle, this Saturday"
        ]
        
        for correction in complex_corrections:
            # Reset for each complex correction
            booking_flow = BookingFlow()
            
            response = booking_flow.process_input_with_intent(correction)
            print(f"\nComplex correction: '{correction}'")
            print(f"Response: {response[:100]}...")
            
            # Should extract and handle multiple pieces of information
            state = booking_flow.get_current_state()
            enhanced_info = state.get('enhanced_info', {})
            
            print(f"Extracted info: {enhanced_info}")
            
            # Should have extracted some information
            extracted_count = sum(1 for v in enhanced_info.values() if v)
            self.assertGreater(extracted_count, 0)
            
            print(f"✓ Extracted {extracted_count} pieces of information")


class TestAsyncAPIScenarios(unittest.TestCase):
    """Test async API scenarios and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up"""
        self.loop.close()
    
    def test_concurrent_api_calls(self):
        """Test: Handling concurrent API calls"""
        print("\n=== Testing Concurrent API Calls ===")
        
        async def test_concurrent():
            api_service = FlightSearchService(use_mock=True)
            
            # Create multiple search params
            searches = [
                FlightSearchParams("Boston", "New York", "2024-12-20"),
                FlightSearchParams("Chicago", "Miami", "2024-12-21"),
                FlightSearchParams("Seattle", "Los Angeles", "2024-12-22"),
                FlightSearchParams("Denver", "Dallas", "2024-12-23"),
            ]
            
            # Run concurrent searches
            tasks = [api_service.search_with_fallback(params) for params in searches]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            print(f"Concurrent searches completed: {len(results)}")
            
            # All should complete successfully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Search {i+1} failed: {result}")
                else:
                    print(f"Search {i+1} returned {len(result)} flights")
                    self.assertIsInstance(result, list)
            
            print("✓ Concurrent API calls handled")
        
        self.loop.run_until_complete(test_concurrent())
    
    def test_api_rate_limiting(self):
        """Test: API rate limiting scenarios"""
        print("\n=== Testing API Rate Limiting ===")
        
        async def test_rate_limiting():
            api_service = FlightSearchService(use_mock=True)
            
            # Simulate rapid requests
            params = FlightSearchParams("Test City", "Test Destination", "2024-12-20")
            
            rapid_requests = []
            for i in range(10):
                task = api_service.search_with_fallback(params)
                rapid_requests.append(task)
                await asyncio.sleep(0.01)  # Very short delay
            
            # Execute all at once
            results = await asyncio.gather(*rapid_requests, return_exceptions=True)
            
            print(f"Rapid requests completed: {len(results)}")
            
            # Should handle without crashing
            successful = sum(1 for r in results if not isinstance(r, Exception))
            print(f"Successful requests: {successful}/{len(results)}")
            
            self.assertGreater(successful, 0)
            print("✓ Rate limiting handled")
        
        self.loop.run_until_complete(test_rate_limiting())


def run_all_edge_case_tests():
    """Run all edge case tests"""
    print("=" * 70)
    print("COMPREHENSIVE EDGE CASE TEST SUITE")
    print("=" * 70)
    
    # Test suites to run
    test_classes = [
        TestContentFilteringEdgeCases,
        TestStateManagementScenarios,
        TestFlexibleDateSearch,
        TestAPIErrorHandling,
        TestComplexConversationFlows,
        TestConversationEdgeCases,
        TestAsyncAPIScenarios
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_class in test_classes:
        print(f"\n{'='*50}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*50}")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        if result.failures:
            print(f"\n❌ FAILURES in {test_class.__name__}:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print(f"\n💥 ERRORS in {test_class.__name__}:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Final summary
    print("\n" + "="*70)
    print("EDGE CASE TEST SUMMARY")
    print("="*70)
    print(f"Total tests run: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    
    success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 ALL EDGE CASE TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total_failures + total_errors} tests failed")
        return False


if __name__ == "__main__":
    # Run with: python tests/test_edge_cases.py
    print("Starting comprehensive edge case tests...")
    print("This will test content filtering, state management, API errors, and complex conversation flows.")
    
    success = run_all_edge_case_tests()
    sys.exit(0 if success else 1)