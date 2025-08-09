#!/usr/bin/env python3
"""
Booking Flow State Machine
Manages the conversation flow for United Airlines flight booking
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import re
import json
import difflib
import logging
from src.utils.date_parser import DateParser
from src.core.intent_recognizer import IntentRecognizer
from src.models.enhanced_booking_info import EnhancedBookingInfo
from src.core.booking_validator import BookingValidator
# from simple_correction_handler import SimpleCorrectionHandler  # Removed - not used


class BookingState(Enum):
    """States in the booking flow"""
    IDLE = "idle"  # Waiting for user to initiate conversation
    GREETING = "greeting"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_DEPARTURE = "collecting_departure"
    COLLECTING_DESTINATION = "collecting_destination"
    COLLECTING_TRIP_TYPE = "collecting_trip_type"
    COLLECTING_DATE = "collecting_date"
    COLLECTING_RETURN_DATE = "collecting_return_date"
    FLEXIBLE_SEARCH = "flexible_search"
    PRESENTING_OPTIONS = "presenting_options"
    CONFIRMING_SELECTION = "confirming_selection"
    BOOKING_COMPLETE = "booking_complete"
    ERROR = "error"


# Using EnhancedBookingInfo from models - no need for basic BookingInfo


class BookingFlow:
    """Manages the booking conversation flow"""
    
    def __init__(self):
        self.state = BookingState.IDLE
        self.booking_info = EnhancedBookingInfo()
        self.context = {}
        self.error_count = 0
        self.date_parser = DateParser()
        self.intent_recognizer = IntentRecognizer()
        self.validator = BookingValidator()
        self.logger = logging.getLogger(__name__)
        # self.simple_correction_handler = SimpleCorrectionHandler()  # Removed - not used
        
        # City name variations and airport codes
        self.city_airports = {
            "san francisco": ["SFO", "San Francisco International"],
            "san fran": ["SFO", "San Francisco International"],
            "sf": ["SFO", "San Francisco International"],
            "new york": ["JFK", "EWR", "LGA", "New York airports"],
            "ny": ["JFK", "EWR", "LGA", "New York airports"],
            "nyc": ["JFK", "EWR", "LGA", "New York airports"],
            "los angeles": ["LAX", "Los Angeles International"],
            "la": ["LAX", "Los Angeles International"],
            "lax": ["LAX", "Los Angeles International"],
            "chicago": ["ORD", "MDW", "Chicago airports"],
            "boston": ["BOS", "Boston Logan"],
            "miami": ["MIA", "Miami International"],
            "seattle": ["SEA", "Seattle-Tacoma"],
            "denver": ["DEN", "Denver International"],
            "dallas": ["DFW", "Dallas/Fort Worth"],
            "atlanta": ["ATL", "Hartsfield-Jackson"],
            "washington": ["DCA", "IAD", "BWI", "Washington area"],
            "dc": ["DCA", "IAD", "BWI", "Washington area"],
            "houston": ["IAH", "HOU", "Houston airports"],
            "phoenix": ["PHX", "Phoenix Sky Harbor"],
            "philadelphia": ["PHL", "Philadelphia International"],
            "philly": ["PHL", "Philadelphia International"],
            "detroit": ["DTW", "Detroit Metropolitan"],
            "minneapolis": ["MSP", "Minneapolis-St. Paul"],
            "orlando": ["MCO", "Orlando International"],
            "las vegas": ["LAS", "McCarran International"],
            "vegas": ["LAS", "McCarran International"],
            "nashville": ["BNA", "Nashville International"],
            "portland": ["PDX", "Portland International"],
            "salt lake city": ["SLC", "Salt Lake City International"],
            "charlotte": ["CLT", "Charlotte Douglas"],
            "pittsburgh": ["PIT", "Pittsburgh International"],
            "cincinnati": ["CVG", "Cincinnati/Northern Kentucky"],
            "cleveland": ["CLE", "Cleveland Hopkins"],
            "baltimore": ["BWI", "Baltimore/Washington"],
            "kansas city": ["MCI", "Kansas City International"],
            "san diego": ["SAN", "San Diego International"],
            "san antonio": ["SAT", "San Antonio International"],
            "austin": ["AUS", "Austin-Bergstrom"],
            "raleigh": ["RDU", "Raleigh-Durham"],
            "tampa": ["TPA", "Tampa International"],
            "jacksonville": ["JAX", "Jacksonville International"],
            "memphis": ["MEM", "Memphis International"],
            "milwaukee": ["MKE", "Milwaukee Mitchell"],
            "indianapolis": ["IND", "Indianapolis International"],
            "columbus": ["CMH", "John Glenn Columbus"],
            "albany": ["ALB", "Albany International"],
            "buffalo": ["BUF", "Buffalo Niagara"],
            "richmond": ["RIC", "Richmond International"],
            "norfolk": ["ORF", "Norfolk International"],
            # Common mishearings and phonetic variations
            "frying": ["Unknown", "Did you mean flying?"],
            "flying": ["Unknown", "Which city are you flying to?"],
            "houston texas": ["IAH", "HOU", "Houston airports"],
            "new orleans": ["MSY", "Louis Armstrong New Orleans"],
            "sacramento": ["SMF", "Sacramento International"],
            "fresno": ["FAT", "Fresno Yosemite"],
            "bakersfield": ["BFL", "Meadows Field"],
            "san jose": ["SJC", "Norman Y. Mineta San Jose"],
            "oakland": ["OAK", "Oakland International"],
            "burbank": ["BUR", "Hollywood Burbank"],
            "long beach": ["LGB", "Long Beach Airport"]
        }
    
    def get_current_state(self):
        """Get current state and booking info"""
        return {
            "state": self.state.value,
            "booking_info": self.booking_info.to_basic_booking_info(),
            "enhanced_info": self.booking_info.to_dict(),
            "context": self.context
        }
    
    def process_input(self, user_input: str) -> str:
        """Process user input and return appropriate response"""
        user_input_lower = user_input.lower().strip()
        
        # Skip correction detection for now - it's not working well
        # Just handle corrections in context of each state
        
        # Normal processing
        user_input = user_input_lower
        
        # Route to appropriate handler based on current state
        handlers = {
            BookingState.IDLE: self._handle_idle,
            BookingState.GREETING: self._handle_greeting,
            BookingState.COLLECTING_NAME: self._handle_name,
            BookingState.COLLECTING_DEPARTURE: self._handle_departure,
            BookingState.COLLECTING_DESTINATION: self._handle_destination,
            BookingState.COLLECTING_TRIP_TYPE: self._handle_trip_type,
            BookingState.COLLECTING_DATE: self._handle_date,
            BookingState.COLLECTING_RETURN_DATE: self._handle_return_date,
            BookingState.FLEXIBLE_SEARCH: self._handle_flexible_search,
            BookingState.PRESENTING_OPTIONS: self._handle_option_selection,
            BookingState.CONFIRMING_SELECTION: self._handle_confirmation,
            BookingState.BOOKING_COMPLETE: self._handle_complete,
            BookingState.ERROR: self._handle_error
        }
        
        handler = handlers.get(self.state, self._handle_error)
        return handler(user_input)
    
    def process_input_with_intent(self, user_input: str) -> str:
        """Process user input using intent recognition"""
        try:
            # Get intent and entities
            intent_result = self.intent_recognizer.recognize_intent(
                user_input, 
                self.state.value, 
                self.booking_info.to_basic_booking_info()
            )
            
            # Handle based on intent
            if intent_result.intent == "cancel":
                self.state = BookingState.GREETING
                self.booking_info = EnhancedBookingInfo()
                return "No problem, I've cancelled that. Want to start fresh with a new booking?"
            
            elif intent_result.intent == "question":
                return self._handle_question(user_input, intent_result)
            
            elif intent_result.intent == "correction":
                return self._handle_intent_correction(user_input, intent_result)
            
            elif intent_result.intent == "confirm_yes":
                return self._handle_yes_confirmation(intent_result)
            
            elif intent_result.intent == "confirm_no":
                return self._handle_no_confirmation(intent_result)
            
            elif intent_result.intent == "provide_name":
                return self._handle_name_intent(intent_result)
            
            elif intent_result.intent == "provide_city":
                # Special handling for GREETING state - skip name collection if trip details provided
                if self.state == BookingState.GREETING:
                    # User provided trip details instead of greeting, skip name for now
                    self.state = BookingState.COLLECTING_NAME  # Will be updated by _handle_city_intent
                return self._handle_city_intent(intent_result)
            
            elif intent_result.intent == "provide_date":
                return self._handle_date_intent(intent_result, user_input)
            
            elif intent_result.intent == "time_preference":
                # User is expressing time flexibility ("anytime is fine")
                if self.state == BookingState.PRESENTING_OPTIONS:
                    # They're responding to flight options, proceed with showing flights
                    return self._present_flight_options()
                elif self.state == BookingState.COLLECTING_DATE:
                    # They're flexible about date, use next week
                    self.booking_info.update_trip_info("departure_date", "next week", confidence=0.7)
                    self.state = BookingState.PRESENTING_OPTIONS
                    return self._present_flight_options()
                else:
                    return self._get_next_question()
            
            elif intent_result.intent == "select_option":
                return self._handle_option_selection_intent(intent_result, user_input)
            
            elif intent_result.intent == "flexible_search":
                return self._handle_flexible_date_request(user_input)
            
            elif intent_result.intent == "inappropriate_content":
                return self._handle_inappropriate_content(intent_result)
            
            else:
                # Fallback to original processing
                return self.process_input(user_input)
                
        except Exception as e:
            # Fallback to original processing on any error
            return self.process_input(user_input)
    
    def _handle_question(self, user_input: str, intent_result) -> str:
        """Handle user questions"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['options', 'flights', 'available']):
            if self._is_booking_complete():
                return self._present_flight_options()
            else:
                return "I'll find you some great flight options once I know all your travel details. " + self._get_next_question()
        
        elif any(word in user_lower for word in ['price', 'cost', 'how much']):
            return "Great question! Our flights usually run between $300-500 for domestic trips. I'll get you exact prices once I know where and when you're traveling."
        
        elif any(word in user_lower for word in ['baggage', 'bags', 'luggage']):
            return "Your personal item and carry-on are included with your ticket! Checked bags start at $35 if you need one. Should we keep going with your booking?"
        
        else:
            return "I'm here to make your travel planning easy! " + self._get_next_question()
    
    def _handle_intent_correction(self, user_input: str, intent_result) -> str:
        """Handle corrections identified by intent recognition"""
        entities = intent_result.entities
        user_lower = user_input.lower()
        
        # First apply fuzzy matching correction for trip type mishearings
        corrected_input = self._correct_trip_type_mishearings(user_lower)
        if corrected_input != user_lower:
            user_lower = corrected_input
            self.logger.info(f"Applied mishearing correction in intent handler: '{user_input}' -> '{corrected_input}'")
        
        # Check for trip type corrections first (round trip vs one way)
        if ("trip_type" in entities or 
            any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return flight', 'coming back', 'one way', 'one-way', 'oneway'])):
            
            if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return', 'coming back']):
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="correction")
                # Check if we need to collect return date
                if not self._get_return_date():
                    self.state = BookingState.COLLECTING_RETURN_DATE
                    arrival_city = self._get_arrival_city()
                    return f"Got it, making it a round trip! When would you like to return from {arrival_city}?"
                else:
                    # If we already have return date and we're in presenting options, refresh the search
                    if self.state == BookingState.PRESENTING_OPTIONS:
                        return "Perfect, I've updated it to a round trip flight. " + self._present_flight_options()
                    else:
                        return "Perfect, I've updated it to a round trip flight. " + self._get_next_question()
            elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'oneway', 'no return']):
                self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="correction")
                # Remove any existing return date since this is now one-way
                if self._get_return_date():
                    self.booking_info.update_trip_info("return_date", None, confidence=1.0, source="correction")
                # If we're in presenting options, refresh the search
                if self.state == BookingState.PRESENTING_OPTIONS:
                    return "Got it, making it a one-way flight. " + self._present_flight_options()
                else:
                    return "Got it, making it a one-way flight. " + self._get_next_question()
        
        # Apply corrections based on entities found - but only if they make contextual sense
        elif "name" in entities and self._is_likely_name_correction(user_input, entities["name"]):
            # Split name into first and last if possible
            name_parts = entities["name"].strip().split()
            if len(name_parts) >= 2:
                self.booking_info.update_customer_info("first_name", name_parts[0], confidence=0.9, source="correction")
                self.booking_info.update_customer_info("last_name", " ".join(name_parts[1:]), confidence=0.9, source="correction")
            else:
                self.booking_info.update_customer_info("first_name", entities["name"], confidence=0.9, source="correction")
            return f"Got it, {entities['name']}. " + self._get_next_question()
        
        elif "departure_city" in entities:
            self.booking_info.update_trip_info("departure_city", entities["departure_city"], confidence=0.9, source="correction")
            return f"Changed departure to {entities['departure_city']}. " + self._get_next_question()
        
        elif "destination_city" in entities:
            self.booking_info.update_trip_info("arrival_city", entities["destination_city"], confidence=0.9, source="correction")
            return f"Changed destination to {entities['destination_city']}. " + self._get_next_question()
        
        elif "date" in entities or "departure_date" in entities:
            date_str = entities.get("date") or entities.get("departure_date")
            parsed_date = self._parse_date(date_str)
            if parsed_date:
                self.booking_info.update_trip_info("departure_date", parsed_date, confidence=0.9, source="correction")
                return f"Changed departure date to {parsed_date}. " + self._get_next_question()
        
        elif "return_date" in entities:
            parsed_date = self._parse_date(entities["return_date"])
            if parsed_date:
                self.booking_info.update_trip_info("return_date", parsed_date, confidence=0.9, source="correction")
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="inference")
                return f"Changed return date to {parsed_date}. " + self._get_next_question()
        
        # If no specific correction found, handle as general input
        return self.process_input(user_input)
    
    def _handle_yes_confirmation(self, intent_result) -> str:
        """Handle yes confirmations based on current state"""
        if self.state == BookingState.CONFIRMING_SELECTION:
            customer_name = self._get_customer_name()
            departure_city = self._get_departure_city()
            
            # Generate more realistic confirmation number
            import random
            import string
            date_code = datetime.now().strftime('%m%d')
            name_code = customer_name[:2].upper() if customer_name else 'UA'
            city_code = departure_city[:3].upper() if departure_city else 'XXX'
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            confirmation_num = f"{name_code}{date_code}{city_code}{random_chars}"
            
            # Store confirmation number in enhanced booking info
            self.booking_info.update_trip_info("confirmation_number", confirmation_num, confidence=1.0, source="booking_confirmation")
            
            self._transition_state(BookingState.BOOKING_COMPLETE, "User confirmed booking")
            
            # Get selected flight details for confirmation message
            selected_flight = self.booking_info.get_selected_outbound_flight()
            flight_details = ""
            if selected_flight:
                airline = selected_flight.get('airline', '')
                flight_number = selected_flight.get('flight_number', '')
                if airline and flight_number:
                    flight_details = f" for {airline} flight {flight_number}"
                elif airline:
                    flight_details = f" with {airline}"
            
            return f"Excellent! I've booked your flight{flight_details}. Your confirmation number is {confirmation_num}. You'll receive an email confirmation shortly. Is there anything else I can help you with?"
        else:
            return "Great! " + self._determine_next_step()
    
    def _handle_no_confirmation(self, intent_result) -> str:
        """Handle no confirmations and corrections"""
        if self.state == BookingState.CONFIRMING_SELECTION:
            self._transition_state(BookingState.PRESENTING_OPTIONS, "User declined confirmation")
            return "No problem. Let me show you the options again. " + self._present_flight_options()
        else:
            return "Got it. " + self._get_next_question()
    
    def _handle_name_intent(self, intent_result) -> str:
        """Handle name provision"""
        entities = intent_result.entities
        
        # Store trip_type if present
        if "trip_type" in entities:
            if entities["trip_type"] == "round_trip":
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="entity_extraction")
            elif entities["trip_type"] == "one_way":
                self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="entity_extraction")
        
        if "name" in entities:
            # Split name into first and last if possible
            name_parts = entities["name"].strip().split()
            if len(name_parts) >= 2:
                self.booking_info.update_customer_info("first_name", name_parts[0], confidence=1.0)
                self.booking_info.update_customer_info("last_name", " ".join(name_parts[1:]), confidence=1.0)
            else:
                self.booking_info.update_customer_info("first_name", entities["name"], confidence=0.8)
            
            # Don't hardcode next state - check what we already have
            self.error_count = 0
            greeting = f"Nice to meet you, {entities['name']}!"
            
            # Use _get_next_question to determine what to ask based on existing data
            next_question = self._get_next_question()
            if next_question:
                return f"{greeting} {next_question}"
            else:
                return greeting
        else:
            return "Sorry, I missed that. What's your name?"
    
    def _handle_city_intent(self, intent_result) -> str:
        """Handle city provision"""
        entities = intent_result.entities
        
        # First, check and store trip_type if present
        if "trip_type" in entities:
            if entities["trip_type"] == "round_trip":
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="entity_extraction")
            elif entities["trip_type"] == "one_way":
                self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="entity_extraction")
        
        # Store date if present
        if "departure_date" in entities:
            self.booking_info.update_trip_info("departure_date", entities["departure_date"], confidence=0.9, source="entity_extraction")
        
        # Check if BOTH cities are provided (common in initial trip planning statements)
        if "departure_city" in entities and "destination_city" in entities:
            self.booking_info.update_trip_info("departure_city", entities["departure_city"], confidence=1.0)
            self.booking_info.update_trip_info("arrival_city", entities["destination_city"], confidence=1.0)
            
            dep_city = entities["departure_city"]
            dest_city = entities["destination_city"]
            
            # Coming from greeting state - acknowledge the trip planning
            if self.state == BookingState.COLLECTING_NAME:
                # Don't stay in COLLECTING_NAME - let _get_next_question determine the next state
                pass
                greeting = f"Perfect! I can help you with your trip from {dep_city} to {dest_city}. "
                
                # If we have all the info we need, skip ahead
                if self._get_trip_type() and self._get_departure_date():
                    return greeting + self._get_next_question()
                elif self._get_trip_type():
                    trip_type = "one-way" if self.booking_info.trip.trip_type and self.booking_info.trip.trip_type.value == "oneway" else "round trip"
                    return greeting + f"A {trip_type} trip sounds great! May I have your name?"
                else:
                    return greeting + "May I have your name?"
            
            # Otherwise handle normally
            elif self._get_trip_type() and self._get_departure_date():
                # We have everything for one-way, or need return date for round trip
                return self._get_next_question()
            elif self._get_trip_type():
                self.state = BookingState.COLLECTING_DATE
                trip_type = "one-way" if self.booking_info.trip.trip_type and self.booking_info.trip.trip_type.value == "oneway" else "round trip"
                return f"Perfect! A {trip_type} trip from {dep_city} to {dest_city}. When would you like to travel?"
            else:
                # Still need trip type
                self.state = BookingState.COLLECTING_TRIP_TYPE
                return f"Great! {dep_city} to {dest_city}. Would you like a one-way or round trip?"
        
        elif "departure_city" in entities:
            self.booking_info.update_trip_info("departure_city", entities["departure_city"], confidence=1.0)
            if self.state in [BookingState.COLLECTING_DEPARTURE, BookingState.GREETING]:
                self.state = BookingState.COLLECTING_DESTINATION
                return f"Great! Flying from {entities['departure_city']}. And where would you like to go?"
        
        elif "destination_city" in entities:
            self.booking_info.update_trip_info("arrival_city", entities["destination_city"], confidence=1.0)
            if self.state == BookingState.COLLECTING_DESTINATION:
                departure_city = self._get_departure_city()
                # Check if trip type is already provided (e.g., at greeting)
                if self._get_trip_type():
                    # Skip trip type collection, go to next step
                    return f"Awesome! {departure_city} to {entities['destination_city']} - sounds like a great trip! " + self._get_next_question()
                else:
                    # Need to collect trip type
                    self.state = BookingState.COLLECTING_TRIP_TYPE
                    return f"Awesome! {departure_city} to {entities['destination_city']} - sounds like a great trip! Would you like a one-way or round trip flight?"
        
        elif "city" in entities:
            # Generic city - determine based on current state
            city = entities["city"]
            if self.state == BookingState.COLLECTING_DEPARTURE or not self._get_departure_city():
                self.booking_info.update_trip_info("departure_city", city, confidence=0.9)
                self.state = BookingState.COLLECTING_DESTINATION
                return f"Great! Flying from {city}. And where would you like to go?"
            elif self.state == BookingState.COLLECTING_DESTINATION or not self._get_arrival_city():
                self.booking_info.update_trip_info("arrival_city", city, confidence=0.9)
                departure_city = self._get_departure_city()
                # Check if trip type is already provided (e.g., at greeting)
                if self._get_trip_type():
                    # Skip trip type collection, go to next step
                    return f"Excellent! {departure_city} to {city} it is. " + self._get_next_question()
                else:
                    # Need to collect trip type
                    self.state = BookingState.COLLECTING_TRIP_TYPE
                    return f"Excellent! {departure_city} to {city} it is. Would you like a one-way or round trip flight?"
        
        return self._get_next_question()
    
    def _handle_date_intent(self, intent_result, user_input: str) -> str:
        """Handle date provision"""
        entities = intent_result.entities
        
        # Store trip_type if present
        if "trip_type" in entities:
            if entities["trip_type"] == "round_trip":
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="entity_extraction")
            elif entities["trip_type"] == "one_way":
                self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="entity_extraction")
        
        if "departure_date" in entities:
            parsed_date = self._parse_date(entities["departure_date"])
            if parsed_date:
                self.booking_info.update_trip_info("departure_date", parsed_date, confidence=1.0)
                
                # Check if return date also mentioned
                if "return_date" in entities:
                    return_parsed = self._parse_date(entities["return_date"])
                    if return_parsed:
                        self.booking_info.update_trip_info("return_date", return_parsed, confidence=1.0)
                        self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                        self.state = BookingState.PRESENTING_OPTIONS
                        return self._present_flight_options()
                
                # Check if trip is round trip (either from entities or previously stored)
                if entities.get("trip_type") == "round_trip" or self._is_roundtrip():
                    if not self._is_roundtrip():  # Only set if not already set
                        self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                    
                    # Check if we already have a return date - don't ask again
                    if self._get_return_date():
                        self.state = BookingState.PRESENTING_OPTIONS
                        return self._present_flight_options()
                    else:
                        self.state = BookingState.COLLECTING_RETURN_DATE
                        arrival_city = self._get_arrival_city()
                        return f"And when would you like to return from {arrival_city}?"
                else:
                    self.state = BookingState.PRESENTING_OPTIONS
                    return self._present_flight_options()
        
        elif "return_date" in entities:
            # Specific return date entity - check if we already have it
            existing_return_date = self._get_return_date()
            if existing_return_date:
                # User is repeating return date information
                self.logger.info(f"User repeated return date. Already have: {existing_return_date}")
                return f"Right, you mentioned {existing_return_date} for your return. " + self._get_next_question()
            
            parsed_date = self._parse_date(entities["return_date"])
            if parsed_date and (self.state == BookingState.COLLECTING_RETURN_DATE or not self._get_return_date()):
                # Validate the return date against departure date if available
                departure_date = self._get_departure_date()
                if departure_date:
                    # Validate date order (return after departure)
                    order_validation = self.validator.validate_date_order(departure_date, parsed_date)
                    if not order_validation.is_valid:
                        self.error_count += 1
                        error_msg = order_validation.error_message
                        if order_validation.suggestions:
                            error_msg += " " + " ".join(order_validation.suggestions)
                        return error_msg + " Please try a different return date."
                    
                    # Use the validated return date
                    validated_return_date = order_validation.normalized_value["return_date"]
                    self.booking_info.update_trip_info("return_date", str(validated_return_date), confidence=order_validation.confidence)
                else:
                    # Just validate the return date if no departure date available
                    date_validation = self.validator.validate_date(parsed_date, "return date")
                    if not date_validation.is_valid:
                        self.error_count += 1
                        return date_validation.error_message + " Please try again."
                    
                    self.booking_info.update_trip_info("return_date", str(date_validation.normalized_value), confidence=date_validation.confidence)
                
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                self.error_count = 0
                self._transition_state(BookingState.PRESENTING_OPTIONS, "Return date collected via return_date entity")
                return self._present_flight_options()
        
        elif "date" in entities:
            # Generic date - could be parsed or raw string
            parsed_date = entities["date"]
            
            # If the entity contains a raw string, try parsing it
            if isinstance(parsed_date, str):
                parsed_date = self._parse_date(parsed_date)
            
            # If parsing failed, try parsing the original input as fallback
            if not parsed_date:
                parsed_date = self._parse_date(user_input)
            
            if parsed_date:
                if self.state == BookingState.COLLECTING_DATE or not self._get_departure_date():
                    # Validate departure date
                    date_validation = self.validator.validate_date(parsed_date, "departure date")
                    if not date_validation.is_valid:
                        self.error_count += 1
                        return date_validation.error_message + " Please try again."
                    
                    self.booking_info.update_trip_info("departure_date", date_validation.normalized_value, confidence=date_validation.confidence)
                    self.error_count = 0
                    
                    # Check if this is a round trip and we need to collect return date
                    if self._is_roundtrip():
                        self._transition_state(BookingState.COLLECTING_RETURN_DATE, "Departure date collected via intent, collecting return")
                        arrival_city = self._get_arrival_city()
                        return f"And when would you like to return from {arrival_city}?"
                    else:
                        self._transition_state(BookingState.PRESENTING_OPTIONS, "Departure date collected via intent")
                        return self._present_flight_options()
                        
                elif self.state == BookingState.COLLECTING_RETURN_DATE:
                    # Validate the return date against departure date if available
                    departure_date = self._get_departure_date()
                    if departure_date:
                        # Validate date order (return after departure)
                        order_validation = self.validator.validate_date_order(departure_date, parsed_date)
                        if not order_validation.is_valid:
                            self.error_count += 1
                            error_msg = order_validation.error_message
                            if order_validation.suggestions:
                                error_msg += " " + " ".join(order_validation.suggestions)
                            return error_msg + " Please try a different return date."
                        
                        # Use the validated return date
                        validated_return_date = order_validation.normalized_value["return_date"]
                        self.booking_info.update_trip_info("return_date", str(validated_return_date), confidence=order_validation.confidence)
                    else:
                        # Just validate the return date if no departure date available
                        date_validation = self.validator.validate_date(parsed_date, "return date")
                        if not date_validation.is_valid:
                            self.error_count += 1
                            return date_validation.error_message + " Please try again."
                        
                        self.booking_info.update_trip_info("return_date", str(date_validation.normalized_value), confidence=date_validation.confidence)
                    
                    self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                    self.error_count = 0
                    self._transition_state(BookingState.PRESENTING_OPTIONS, "Return date collected via intent")
                    return self._present_flight_options()
        
        # Provide a helpful error message based on current state
        if self.state == BookingState.COLLECTING_RETURN_DATE:
            return "I didn't catch that return date. You can say something like 'August 15th', '8/15', or 'next Friday'. When would you like to return?"
        elif self.state == BookingState.COLLECTING_DATE:
            return "I didn't catch that departure date. You can say something like 'tomorrow', 'next Monday', or 'August 10th'. When would you like to travel?"
        else:
            return "I didn't catch that date. " + self._get_next_question()
    
    def _handle_inappropriate_content(self, intent_result) -> str:
        """Handle inappropriate content detected by the content filter"""
        from src.core.content_filter import ContentFilter, InappropriateType
        
        # Get the filter reason from entities
        filter_reason = intent_result.entities.get("filter_reason", "inappropriate content")
        
        # Determine the type of inappropriate content and respond appropriately
        if "profanity" in filter_reason.lower():
            response = ContentFilter().get_appropriate_response(InappropriateType.PROFANITY)
        elif "spam" in filter_reason.lower():
            response = ContentFilter().get_appropriate_response(InappropriateType.SPAM)
        elif "personal" in filter_reason.lower():
            response = ContentFilter().get_appropriate_response(InappropriateType.PERSONAL_INFO)
        elif "name" in filter_reason.lower():
            response = ContentFilter().get_appropriate_response(InappropriateType.INAPPROPRIATE_NAME)
        else:
            response = "I'm here to make your travel planning easy! How can I help you?"
        
        # Add the next question to keep the conversation moving
        return response + " " + self._get_next_question()
    
    def _handle_option_selection_intent(self, intent_result, user_input: str) -> str:
        """Handle flight option selection via intent recognition"""
        # Only handle if we're in the correct state
        if self.state != BookingState.PRESENTING_OPTIONS:
            # Fallback to regular processing if not in the right state
            return self.process_input(user_input)
        
        # Extract option number from entities or parse from input
        option_number = intent_result.entities.get("option_number")
        
        # If no option_number entity, try to extract from input
        if not option_number:
            user_lower = user_input.lower()
            if any(word in user_lower for word in ['1', 'one', 'first', 'cheapest', 'earliest']):
                option_number = 1
            elif any(word in user_lower for word in ['2', 'two', 'second', 'middle']):
                option_number = 2
            elif any(word in user_lower for word in ['3', 'three', 'third', 'latest']):
                option_number = 3
            else:
                return "Which one looks good to you? You can say 'option 1', 'the cheapest one', or 'the morning flight'."
        
        # Convert to int if it's a string
        if isinstance(option_number, str):
            try:
                option_number = int(option_number)
            except ValueError:
                # Handle word numbers
                word_to_num = {"one": 1, "two": 2, "three": 3, "first": 1, "second": 2, "third": 3}
                option_number = word_to_num.get(option_number.lower(), 1)
        
        # Use the stored flight data instead of hardcoded options
        available_flights = self.context.get('available_flights', [])
        if not available_flights:
            return "I need to search for flights first. Let me do that for you."
        
        if option_number < 1 or option_number > len(available_flights):
            return f"I've got options 1 through {len(available_flights)} available. Which one works best for you?"
        
        # Get the selected flight from stored data
        selected_flight = available_flights[option_number - 1]
        
        # Store selected flight in enhanced booking info
        self.booking_info.store_selected_flight(selected_flight, is_return=False)
        
        # Also keep in context for backward compatibility
        self.context['selected_flight'] = selected_flight
        self._transition_state(BookingState.CONFIRMING_SELECTION, "Flight option selected via intent")
        
        departure_city = self._get_departure_city()
        arrival_city = self._get_arrival_city()
        departure_date = self._get_departure_date()
        trip_type = "round trip" if self._is_roundtrip() else "one-way"
        
        # Create detailed confirmation message with flight info
        airline = selected_flight.get('airline', 'the airline')
        flight_number = selected_flight.get('flight_number', '')
        departure_time = selected_flight.get('departure_time', selected_flight.get('time', 'the scheduled time'))
        duration = selected_flight.get('duration', '')
        flight_type = selected_flight.get('type', '')
        price = selected_flight.get('price', 0)
        
        confirmation_parts = [
            f"Great choice! Let me confirm: {trip_type} from {departure_city} to {arrival_city} on {departure_date}"
        ]
        
        if flight_number:
            confirmation_parts.append(f"on {airline} flight {flight_number}")
        else:
            confirmation_parts.append(f"on {airline}")
            
        confirmation_parts.append(f"departing at {departure_time}")
        
        if duration:
            confirmation_parts.append(f"with a {duration} {flight_type} flight")
        elif flight_type:
            confirmation_parts.append(f"({flight_type})")
            
        confirmation_parts.append(f"for ${price}")
        
        if self._is_roundtrip():
            return_date = self._get_return_date()
            if return_date:
                confirmation_parts.append(f"and returning {return_date}")
        
        confirmation_parts.append("Shall I book this for you?")
        
        return " ".join(confirmation_parts)
    
    def _get_customer_name(self) -> Optional[str]:
        """Get customer name from enhanced booking info (handles single names too)"""
        # Try full name first (first + last)
        full_name = self.booking_info.customer.get_full_name()
        if full_name:
            return full_name
        
        # If no full name, check if we have at least a first name
        if self.booking_info.customer.first_name and self.booking_info.customer.first_name.value:
            return self.booking_info.customer.first_name.value
        
        # No name available
        return None
    
    def _get_departure_city(self) -> Optional[str]:
        """Get departure city from enhanced booking info"""
        return self.booking_info.trip.departure_city.value if self.booking_info.trip.departure_city else None
    
    def _get_arrival_city(self) -> Optional[str]:
        """Get arrival city from enhanced booking info"""
        return self.booking_info.trip.arrival_city.value if self.booking_info.trip.arrival_city else None
    
    def _get_departure_date(self) -> Optional[str]:
        """Get departure date from enhanced booking info"""
        return self.booking_info.trip.departure_date.value if self.booking_info.trip.departure_date else None
    
    def _get_return_date(self) -> Optional[str]:
        """Get return date from enhanced booking info"""
        return self.booking_info.trip.return_date.value if self.booking_info.trip.return_date else None
    
    def _get_trip_type(self) -> Optional[str]:
        """Get trip type from enhanced booking info"""
        return self.booking_info.trip.trip_type.value if self.booking_info.trip.trip_type else None
    
    def _is_roundtrip(self) -> bool:
        """Check if this is a roundtrip booking"""
        return self.booking_info.trip.is_roundtrip()
    
    def _is_booking_complete(self) -> bool:
        """Check if we have minimum info for booking"""
        missing = self.booking_info.get_missing_required_fields()
        return len(missing) == 0
    
    def _get_next_question(self) -> str:
        """Get the next question based on missing information"""
        if not self._get_customer_name():
            if self.state != BookingState.COLLECTING_NAME:
                self._transition_state(BookingState.COLLECTING_NAME, "Missing customer name")
            return "May I have your name please?"
        elif not self._get_departure_city():
            if self.state != BookingState.COLLECTING_DEPARTURE:
                self._transition_state(BookingState.COLLECTING_DEPARTURE, "Missing departure city")
            return "Which city are you flying from?"
        elif not self._get_arrival_city():
            if self.state != BookingState.COLLECTING_DESTINATION:
                self._transition_state(BookingState.COLLECTING_DESTINATION, "Missing destination city")
            return "Where are you headed?"
        elif not self._get_trip_type():
            if self.state != BookingState.COLLECTING_TRIP_TYPE:
                self._transition_state(BookingState.COLLECTING_TRIP_TYPE, "Missing trip type")
            return "Would you like a one-way or round trip flight?"
        elif not self._get_departure_date():
            if self.state != BookingState.COLLECTING_DATE:
                self._transition_state(BookingState.COLLECTING_DATE, "Missing departure date")
            return "When are you looking to travel?"
        elif self._is_roundtrip() and not self._get_return_date():
            if self.state != BookingState.COLLECTING_RETURN_DATE:
                self._transition_state(BookingState.COLLECTING_RETURN_DATE, "Missing return date")
            arrival_city = self._get_arrival_city()
            return f"When would you like to return from {arrival_city}?"
        else:
            if self.state != BookingState.PRESENTING_OPTIONS:
                self._transition_state(BookingState.PRESENTING_OPTIONS, "All information collected")
            return self._present_flight_options()
    
    def _handle_idle(self, user_input: str) -> str:
        """Handle initial user input when in idle state - transition to greeting"""
        # When user first speaks, transition to greeting state and let greeting handler take over
        self._transition_state(BookingState.GREETING, "User initiated conversation")
        return self._handle_greeting(user_input)
    
    def _handle_greeting(self, user_input: str) -> str:
        """Handle initial greeting with trip type detection"""
        user_lower = user_input.lower()
        
        # Check for trip type keywords in greeting response
        if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return flight', 'coming back']):
            self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="greeting")
            self._transition_state(BookingState.COLLECTING_NAME, "Round trip mentioned at greeting")
            return "Perfect! Round trip it is. What's your name?"
        elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'oneway', 'no return']):
            self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="greeting")
            self._transition_state(BookingState.COLLECTING_NAME, "One-way mentioned at greeting")
            return "Got it! One-way trip. What's your name?"
        else:
            # Generic greeting response when no trip type is mentioned
            self._transition_state(BookingState.COLLECTING_NAME, "Initial greeting")
            return "Hi! I'm Alex from United Airlines. I'd love to help you book your trip today. What's your name?"
    
    def _handle_name(self, user_input: str) -> str:
        """Extract and store customer name"""
        # Simple name extraction - just use the input
        name = user_input.title()
        
        # Remove common phrases
        name = re.sub(r'\b(my name is|i am|im|i\'m|this is|it\'s|its)\b', '', name, flags=re.IGNORECASE)
        name = name.strip()
        
        # Validate the name
        validation_result = self.validator.validate_name(name, "name")
        
        if not validation_result.is_valid:
            self.error_count += 1
            if self.error_count > 2:
                self.state = BookingState.ERROR
                return "I'm having trouble understanding. Let me transfer you to an agent."
            return validation_result.error_message or "I didn't catch your name. Could you please tell me your name?"
        
        # Split name into first and last if possible
        name_parts = validation_result.normalized_value.strip().split()
        if len(name_parts) >= 2:
            self.booking_info.update_customer_info("first_name", name_parts[0], confidence=validation_result.confidence)
            self.booking_info.update_customer_info("last_name", " ".join(name_parts[1:]), confidence=validation_result.confidence)
        else:
            self.booking_info.update_customer_info("first_name", validation_result.normalized_value, confidence=validation_result.confidence * 0.8)
        
        self._transition_state(BookingState.COLLECTING_DEPARTURE, "Name collected")
        self.error_count = 0
        
        return f"Great to meet you, {validation_result.normalized_value}! So, where are you starting your journey from?"
    
    def _handle_departure(self, user_input: str) -> str:
        """Extract departure city"""
        city = self._extract_city(user_input)
        
        if not city:
            self.error_count += 1
            if self.error_count > 2:
                return "I'm having a hard time catching that. Could you tell me which city you're leaving from?"
            return "I missed that - which city are you leaving from?"
        
        # Validate the city using the new validator
        validation_result = self.validator._normalize_city(city)
        
        if not validation_result.is_valid:
            self.error_count += 1
            if self.error_count > 2 or not validation_result.suggestions:
                return "Hmm, I didn't quite get that city name. Could you try saying it again?"
            return f"I didn't recognize '{city}'. Did you mean: {', '.join(validation_result.suggestions[:3])}?"
        
        self.booking_info.update_trip_info("departure_city", validation_result.normalized_value, confidence=validation_result.confidence)
        self.state = BookingState.COLLECTING_DESTINATION
        self.error_count = 0
        
        return f"Perfect! So you're flying from {city}. Where's your destination?"
    
    def _handle_destination(self, user_input: str) -> str:
        """Extract destination city"""
        city = self._extract_city(user_input)
        
        if not city:
            self.error_count += 1
            if self.error_count > 2:
                return "I'm having trouble catching that. Which city are you flying to?"
            return "And where are you headed?"
        
        # Validate the city using the new validator
        validation_result = self.validator._normalize_city(city)
        
        if not validation_result.is_valid:
            self.error_count += 1
            if self.error_count > 2 or not validation_result.suggestions:
                return "I missed that destination. Could you say it one more time?"
            return f"I didn't recognize '{city}'. Did you mean: {', '.join(validation_result.suggestions[:3])}?"
        
        # Check if same as departure
        departure_city = self._get_departure_city()
        if departure_city and validation_result.normalized_value == departure_city:
            return f"You're already in {city}! Where else would you like to go?"
        
        # Validate city pair
        if departure_city:
            pair_validation = self.validator.validate_city_pair(departure_city, validation_result.normalized_value)
            if not pair_validation.is_valid:
                return pair_validation.error_message
        
        self.booking_info.update_trip_info("arrival_city", validation_result.normalized_value, confidence=validation_result.confidence)
        self.error_count = 0
        
        # Check if trip type is already provided (e.g., at greeting)
        if self._get_trip_type():
            # Skip trip type collection, go to next step
            return f"Great! {departure_city} to {city} - I can definitely help with that. " + self._get_next_question()
        else:
            # Need to collect trip type
            self.state = BookingState.COLLECTING_TRIP_TYPE
            return f"Great! {departure_city} to {city} - I can definitely help with that. Would you like a one-way or round trip flight?"
    
    def _handle_trip_type(self, user_input: str) -> str:
        """Handle trip type selection (one-way vs round trip) with fuzzy matching for mishearings"""
        user_lower = user_input.lower().strip()
        
        # First, try fuzzy matching for common mishearings
        corrected_input = self._correct_trip_type_mishearings(user_lower)
        if corrected_input != user_lower:
            user_lower = corrected_input
            self.logger.info(f"Applied speech correction: '{user_input.strip()}' -> '{corrected_input}'")
        
        # Check for round trip indicators
        round_trip_keywords = [
            'round trip', 'roundtrip', 'round-trip', 'return flight', 'return ticket',
            'coming back', 'go and return', 'there and back', 'both ways', 
            'round', 'return', 'back'
        ]
        
        # Check for one-way indicators  
        one_way_keywords = [
            'one way', 'one-way', 'oneway', 'one direction', 'just going',
            'no return', 'not coming back', 'stay there', 'moving there',
            'one', 'single'
        ]
        
        # Determine trip type
        is_round_trip = any(keyword in user_lower for keyword in round_trip_keywords)
        is_one_way = any(keyword in user_lower for keyword in one_way_keywords)
        
        # Handle explicit responses
        if is_round_trip and not is_one_way:
            self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="user_selection")
            self.state = BookingState.COLLECTING_DATE
            self.error_count = 0
            return "Perfect! Round trip it is. When are you planning to travel?"
            
        elif is_one_way and not is_round_trip:
            self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="user_selection")
            self.state = BookingState.COLLECTING_DATE
            self.error_count = 0
            return "Got it! One-way flight. When would you like to depart?"
            
        else:
            # Handle unclear or invalid responses
            self.error_count += 1
            if self.error_count > 2:
                return "I'm having trouble understanding. Let me transfer you to an agent who can help you better."
            
            # Provide helpful examples with fuzzy match suggestions
            examples = [
                "Would you like a one-way or round trip flight?",
                "You can say 'round trip' if you're coming back, or 'one-way' if you're just going.",
                "Are you planning to return, or is this just a one-way trip?"
            ]
            
            return examples[min(self.error_count - 1, len(examples) - 1)]
    
    def _handle_date(self, user_input: str) -> str:
        """Extract departure date"""
        # Check if both departure and return dates are mentioned
        if any(word in user_input.lower() for word in ['return', 'coming back', 'and back', 'round trip']):
            # Try to extract both dates
            parts = re.split(r'\b(?:and|return|coming back|back)\b', user_input.lower())
            
            if len(parts) >= 2:
                # Parse departure date from first part
                dep_date = self._parse_date(parts[0])
                if dep_date:
                    dep_validation = self.validator.validate_date(dep_date, "departure date")
                    if dep_validation.is_valid:
                        self.booking_info.update_trip_info("departure_date", dep_validation.normalized_value, confidence=dep_validation.confidence)
                        
                        # Parse return date from second part
                        ret_date = self._parse_date(parts[1])
                        if ret_date:
                            ret_validation = self.validator.validate_date(ret_date, "return date")
                            if ret_validation.is_valid:
                                self.booking_info.update_trip_info("return_date", ret_validation.normalized_value, confidence=ret_validation.confidence)
                                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                                self._transition_state(BookingState.PRESENTING_OPTIONS, "Both dates collected")
                                return self._present_flight_options()
            
            # If we couldn't parse both, just get departure and ask for return
            date_str = self._parse_date(user_input)
            if date_str:
                date_validation = self.validator.validate_date(date_str, "departure date")
                if date_validation.is_valid:
                    self.booking_info.update_trip_info("departure_date", date_validation.normalized_value, confidence=date_validation.confidence)
                    self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
                    self._transition_state(BookingState.COLLECTING_RETURN_DATE, "Departure date collected, roundtrip")
                    arrival_city = self._get_arrival_city()
                    return f"And when would you like to return from {arrival_city}?"
        
        # Single date parsing
        date_str = self._parse_date(user_input)
        
        if not date_str:
            self.error_count += 1
            if self.error_count > 2:
                return "I'm having trouble with that date. Could you try something like 'next Friday' or 'December 15th'?"
            return "When would you like to leave? You can say something like 'tomorrow', 'next Monday', or any specific date that works for you."
        
        # Validate the date
        date_validation = self.validator.validate_date(date_str, "departure date")
        if not date_validation.is_valid:
            self.error_count += 1
            return date_validation.error_message + " Please try again."
        
        self.booking_info.update_trip_info("departure_date", date_validation.normalized_value, confidence=date_validation.confidence)
        self._transition_state(BookingState.PRESENTING_OPTIONS, "Departure date collected")
        return self._present_flight_options()
    
    def _handle_return_date(self, user_input: str) -> str:
        """Extract return date"""
        # First check if user wants one-way instead
        if any(word in user_input.lower() for word in ['one way', 'one-way', 'no return', "don't need return"]):
            self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0)
            self._transition_state(BookingState.PRESENTING_OPTIONS, "Changed to one-way")
            return self._present_flight_options()
        
        date_str = self._parse_date(user_input)
        
        if not date_str:
            self.error_count += 1
            if self.error_count > 2:
                return "I didn't catch that return date. When are you planning to come back?"
            return "When would you like to return? You can say a specific date or 'one way' if you don't need a return flight."
        
        # Validate the return date and check order with departure date
        departure_date = self._get_departure_date()
        if departure_date:
            # Validate date order (return after departure)
            order_validation = self.validator.validate_date_order(departure_date, date_str)
            if not order_validation.is_valid:
                self.error_count += 1
                error_msg = order_validation.error_message
                if order_validation.suggestions:
                    error_msg += " " + " ".join(order_validation.suggestions)
                return error_msg + " Please try a different return date."
            
            # Use the validated return date
            validated_return_date = order_validation.normalized_value["return_date"]
            self.booking_info.update_trip_info("return_date", validated_return_date, confidence=order_validation.confidence)
        else:
            # Just validate the return date if no departure date available
            date_validation = self.validator.validate_date(date_str, "return date")
            if not date_validation.is_valid:
                self.error_count += 1
                return date_validation.error_message + " Please try again."
            
            self.booking_info.update_trip_info("return_date", date_validation.normalized_value, confidence=date_validation.confidence)
        
        self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0)
        self._transition_state(BookingState.PRESENTING_OPTIONS, "Return date collected")
        
        return self._present_flight_options()
    
    def _handle_option_selection(self, user_input: str) -> str:
        """Handle flight option selection"""
        # Check for trip type corrections first
        user_lower = user_input.lower()
        if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return flight', 'coming back']):
            self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="correction")
            # Check if we need to collect return date
            if not self._get_return_date():
                self.state = BookingState.COLLECTING_RETURN_DATE
                arrival_city = self._get_arrival_city()
                return f"Got it, making it a round trip! When would you like to return from {arrival_city}?"
            else:
                # Return date already exists, go back to presenting options with updated trip type
                return self._present_flight_options()
        elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'oneway', 'no return']):
            self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="correction")
            # Remove any existing return date since this is now one-way
            if self._get_return_date():
                self.booking_info.update_trip_info("return_date", None, confidence=1.0, source="correction")
            return self._present_flight_options()
        
        # Use the stored flight data instead of hardcoded options
        available_flights = self.context.get('available_flights', [])
        if not available_flights:
            # If we're in presenting options but don't have flights yet, 
            # return a specific message that voice_agent will intercept
            return self._present_flight_options()
        
        # Look for option numbers or keywords
        option_number = 0
        if any(word in user_input.lower() for word in ['1', 'one', 'first', 'cheapest', 'earliest']):
            option_number = 1
        elif any(word in user_input.lower() for word in ['2', 'two', 'second', 'middle']):
            option_number = 2
        elif any(word in user_input.lower() for word in ['3', 'three', 'third', 'latest']):
            option_number = 3
        else:
            # Check if this is a generic positive response when no flights are available yet
            user_lower = user_input.lower().strip()
            positive_responses = ['ok', 'okay', 'yes', 'sure', 'sounds good', 'go ahead', 'please', 'alright']
            if any(resp in user_lower for resp in positive_responses) and not available_flights:
                # Return a message that will trigger flight search in voice_agent
                return self._present_flight_options()
            else:
                return "Which one looks good to you? You can say 'option 1', 'the cheapest one', or 'the morning flight'."
        
        if option_number < 1 or option_number > len(available_flights):
            return f"I've got options 1 through {len(available_flights)} available. Which one works best for you?"
        
        # Get the selected flight from stored data
        selected_flight = available_flights[option_number - 1]
        
        # Store selected flight in enhanced booking info
        self.booking_info.store_selected_flight(selected_flight, is_return=False)
        
        # Also keep in context for backward compatibility
        self.context['selected_flight'] = selected_flight
        
        self._transition_state(BookingState.CONFIRMING_SELECTION, "Flight option selected")
        departure_city = self._get_departure_city()
        arrival_city = self._get_arrival_city()
        departure_date = self._get_departure_date()
        trip_type = "round trip" if self._is_roundtrip() else "one-way"
        
        # Create detailed confirmation message with flight info
        airline = selected_flight.get('airline', 'the airline')
        flight_number = selected_flight.get('flight_number', '')
        departure_time = selected_flight.get('departure_time', selected_flight.get('time', 'the scheduled time'))
        duration = selected_flight.get('duration', '')
        flight_type = selected_flight.get('type', '')
        price = selected_flight.get('price', 0)
        
        confirmation_parts = [
            f"Great choice! Let me confirm: {trip_type} from {departure_city} to {arrival_city} on {departure_date}"
        ]
        
        if flight_number:
            confirmation_parts.append(f"on {airline} flight {flight_number}")
        else:
            confirmation_parts.append(f"on {airline}")
            
        confirmation_parts.append(f"departing at {departure_time}")
        
        if duration:
            confirmation_parts.append(f"with a {duration} {flight_type} flight")
        elif flight_type:
            confirmation_parts.append(f"({flight_type})")
            
        confirmation_parts.append(f"for ${price}")
        
        if self._is_roundtrip():
            return_date = self._get_return_date()
            if return_date:
                confirmation_parts.append(f"and returning {return_date}")
        
        confirmation_parts.append("Shall I book this for you?")
        
        return " ".join(confirmation_parts)
    
    def _handle_confirmation(self, user_input: str) -> str:
        """Handle booking confirmation"""
        if any(word in user_input.lower() for word in ['yes', 'yeah', 'sure', 'correct', 'book', 'confirm']):
            customer_name = self._get_customer_name()
            departure_city = self._get_departure_city()
            
            # Generate more realistic confirmation number
            import random
            import string
            date_code = datetime.now().strftime('%m%d')
            name_code = customer_name[:2].upper() if customer_name else 'UA'
            city_code = departure_city[:3].upper() if departure_city else 'XXX'
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            confirmation_num = f"{name_code}{date_code}{city_code}{random_chars}"
            
            # Store confirmation number in enhanced booking info
            self.booking_info.update_trip_info("confirmation_number", confirmation_num, confidence=1.0, source="booking_confirmation")
            
            # Also keep in context for backward compatibility
            self.context['confirmation_number'] = confirmation_num
            self._transition_state(BookingState.BOOKING_COMPLETE, "Booking confirmed")
            
            # Get selected flight details for confirmation message
            selected_flight = self.booking_info.get_selected_outbound_flight()
            flight_details = ""
            if selected_flight:
                airline = selected_flight.get('airline', '')
                flight_number = selected_flight.get('flight_number', '')
                if airline and flight_number:
                    flight_details = f" for {airline} flight {flight_number}"
                elif airline:
                    flight_details = f" with {airline}"
            
            return f"Excellent! I've booked your flight{flight_details}. Your confirmation number is {confirmation_num}. You'll receive an email confirmation shortly. Is there anything else I can help you with?"
        
        elif any(word in user_input.lower() for word in ['no', 'cancel', 'wrong', 'change', 'wait', 'actually']):
            # Check if they're trying to correct something specific
            user_lower = user_input.lower()
            
            # Check for departure city corrections - multiple patterns
            if any(phrase in user_lower for phrase in ['from', 'leaving from', 'departing from']):
                # Look for city names after "from"
                for city_name in self.city_airports.keys():
                    if city_name in user_lower:
                        # Check context - is this the departure city?
                        if f"from {city_name}" in user_lower or f"leaving from {city_name}" in user_lower:
                            extracted_city = self._extract_city(city_name) or city_name.title()
                            self.booking_info.update_trip_info("departure_city", extracted_city, confidence=0.8, source="correction")
                            self._transition_state(BookingState.PRESENTING_OPTIONS, "Departure corrected")
                            return f"Got it, changing departure to {extracted_city}. " + self._present_flight_options()
            
            # Check for destination corrections
            if 'to' in user_lower and 'not' in user_lower:
                # Pattern like "to miami not new york"
                for city_name in self.city_airports.keys():
                    if city_name in user_lower and f"to {city_name}" in user_lower:
                        extracted_city = self._extract_city(city_name) or city_name.title()
                        self.booking_info.update_trip_info("arrival_city", extracted_city, confidence=0.8, source="correction")
                        self._transition_state(BookingState.PRESENTING_OPTIONS, "Destination corrected")
                        return f"Got it, changing destination to {extracted_city}. " + self._present_flight_options()
            
            # Default: just show options again
            self._transition_state(BookingState.PRESENTING_OPTIONS, "User said no, showing options again")
            return "No problem. Let me show you the options again. " + self._present_flight_options()
        
        else:
            return "Should I go ahead and book this for you? Just say 'yes' to confirm or 'no' to look at other options."
    
    def _handle_complete(self, user_input: str) -> str:
        """Handle post-booking interaction"""
        return "Thanks so much for choosing United! Have an amazing trip and safe travels. Take care!"
    
    def _handle_error(self, user_input: str) -> str:
        """Handle error state"""
        return "I'm sorry I couldn't help you better. Let me connect you with one of our customer service agents who can take great care of you."
    
    def _extract_city(self, text: str) -> Optional[str]:
        """Extract city name from text with enhanced fuzzy matching"""
        text = text.lower().strip()
        
        # Remove common phrases
        text = re.sub(r'\b(from|to|in|at|flying from|going to|departing|leaving|i want to go|i need to go)\b', '', text)
        text = text.strip()
        
        # First, check for exact matches in known cities
        for city, airports in self.city_airports.items():
            if city in text:
                return city.title()
        
        # Second, use fuzzy matching for common mishearings
        # Get all individual words from the input
        words = text.split()
        
        for word in words:
            if len(word) > 2:  # Only consider words longer than 2 characters
                # Find the best fuzzy match from our known cities
                city_names = list(self.city_airports.keys())
                matches = difflib.get_close_matches(word, city_names, n=1, cutoff=0.6)
                
                if matches:
                    matched_city = matches[0]
                    return matched_city.title()
                
                # Also check for fuzzy matches in multi-word city names
                for city in city_names:
                    city_words = city.split()
                    for city_word in city_words:
                        if len(city_word) > 2:
                            similarity = difflib.SequenceMatcher(None, word, city_word).ratio()
                            if similarity > 0.7:  # High threshold for multi-word matches
                                return city.title()
        
        # Third, check for multi-word phrases with fuzzy matching
        if len(words) >= 2:
            phrase = ' '.join(words)
            city_names = list(self.city_airports.keys())
            matches = difflib.get_close_matches(phrase, city_names, n=1, cutoff=0.7)
            
            if matches:
                matched_city = matches[0]
                return matched_city.title()
        
        # NEVER return unvalidated words - if we can't match to a known city, return None
        return None
    
    def _correct_trip_type_mishearings(self, user_input: str) -> str:
        """Apply fuzzy matching and phonetic similarity to correct common trip type mishearings"""
        import re  # Ensure re is available in this scope
        
        # Common speech recognition mishearings for "round trip"
        round_trip_mishearings = {
            'phone trip': 'round trip',
            'found trip': 'round trip', 
            'round trip': 'round trip',  # Keep correct version
            'run trip': 'round trip',
            'road trip': 'round trip',  # Context-dependent but likely
            'ground trip': 'round trip',
            'brown trip': 'round trip',
            'sound trip': 'round trip',
            'bound trip': 'round trip',
            'pound trip': 'round trip',
            'round chip': 'round trip',
            'round dip': 'round trip', 
            'round grip': 'round trip',
            'around trip': 'round trip',
            'round strip': 'round trip'
        }
        
        # Common speech recognition mishearings for "one way"
        one_way_mishearings = {
            'one day': 'one way',
            'one we': 'one way', 
            'one way': 'one way',  # Keep correct version
            'won way': 'one way',
            'when way': 'one way',
            'on way': 'one way',
            'own way': 'one way',
            'one weigh': 'one way',
            'one whey': 'one way',
            'juan way': 'one way',
            'one bay': 'one way',
            'one may': 'one way'
        }
        
        # Combine all mishearing patterns
        all_mishearings = {**round_trip_mishearings, **one_way_mishearings}
        
        # First check for exact mishearing matches (word boundaries to avoid substring issues)
        for mishearing, correction in all_mishearings.items():
            # Use word boundary regex to avoid partial matches like "round trip" in "ground trip"
            pattern = r'\b' + re.escape(mishearing) + r'\b'
            if re.search(pattern, user_input, re.IGNORECASE):
                return re.sub(pattern, correction, user_input, flags=re.IGNORECASE)
        
        # Apply fuzzy matching for partial matches
        words = user_input.split()
        corrected_words = []
        
        for word in words:
            best_match = word
            best_score = 0.0
            
            # Check against all mishearing keys (but be selective)
            for mishearing in all_mishearings.keys():
                mishearing_words = mishearing.split()
                
                # For single word mishearings - only correct if context is appropriate
                if len(mishearing_words) == 1:
                    similarity = difflib.SequenceMatcher(None, word, mishearing_words[0]).ratio()
                    if similarity > 0.8 and similarity > best_score:  # Higher threshold for single words to avoid false positives
                        # Only apply single-word corrections for very close matches
                        correction = all_mishearings[mishearing]
                        if ' ' not in correction:  # Single word correction only
                            best_match = correction
                            best_score = similarity
            
            corrected_words.append(best_match)
        
        corrected_input = ' '.join(corrected_words)
        
        # Handle multi-word phrase fuzzy matching 
        for mishearing, correction in all_mishearings.items():
            if len(mishearing.split()) > 1:  # Multi-word phrases
                # Use fuzzy matching for the entire phrase, but be more restrictive
                similarity = difflib.SequenceMatcher(None, user_input, mishearing).ratio()
                if similarity > 0.8:  # Higher threshold to reduce false positives like "phone chip" -> "phone trip"
                    return correction
        
        # Special case: handle phonetically similar patterns
        phonetic_patterns = [
            # "phone trip" and similar variations
            (r'\b(?:phone|fo+ne?|found?|run|ground|brown|sound|bound|pound)\s+trip\b', 'round trip'),
            (r'\bround\s+(?:chip|dip|grip|strip)\b', 'round trip'),
            # "one day" and similar variations  
            (r'\b(?:one|won|when|on|own)\s+(?:day|wa[wy]|weigh|whey|bay|may)\b', 'one way'),
        ]
        
        import re
        for pattern, correction in phonetic_patterns:
            if re.search(pattern, corrected_input, re.IGNORECASE):
                corrected_input = re.sub(pattern, correction, corrected_input, flags=re.IGNORECASE)
                break
        
        return corrected_input
    
    def _parse_date(self, text: str) -> Optional[str]:
        """Parse date from natural language using enhanced parser"""
        result = self.date_parser.parse(text)
        
        if result:
            date_obj, formatted = result
            # Return the formatted date string
            return formatted
        
        return None
    
    def _handle_simple_correction(self, correction_type: str, new_value: str) -> str:
        """Handle simple corrections without LLM"""
        response = ""
        
        if correction_type == 'name':
            name_parts = new_value.title().split()
            if len(name_parts) >= 2:
                self.booking_info.update_customer_info("first_name", name_parts[0], confidence=1.0, source="simple_correction")
                self.booking_info.update_customer_info("last_name", " ".join(name_parts[1:]), confidence=1.0, source="simple_correction")
            else:
                self.booking_info.update_customer_info("first_name", new_value.title(), confidence=0.9, source="simple_correction")
            response = f"Got it, {new_value.title()}."
            
        elif correction_type == 'departure':
            city = self._extract_city(new_value) or new_value.title()
            self.booking_info.update_trip_info("departure_city", city, confidence=1.0, source="simple_correction")
            response = f"Okay, flying from {city}."
            
        elif correction_type == 'destination':
            city = self._extract_city(new_value) or new_value.title()
            self.booking_info.update_trip_info("arrival_city", city, confidence=1.0, source="simple_correction")
            response = f"Got it, going to {city}."
            
        elif correction_type == 'date':
            parsed_date = self._parse_date(new_value)
            if parsed_date:
                self.booking_info.update_trip_info("departure_date", parsed_date, confidence=1.0, source="simple_correction")
                response = f"Changed to {parsed_date}."
            else:
                response = "I couldn't understand that date. "
        
        # Continue with flow using the new method
        response += " " + self._determine_next_step()
            
        return response
    
    def _handle_llm_correction(self, correction_result) -> str:
        """Handle corrections identified by LLM"""
        
        # Get old value for response generation
        old_value = "not set"  # Enhanced booking info doesn't have direct attributes
        
        # Apply the correction using enhanced booking info
        if correction_result.correction_type == 'customer_name':
            name_parts = correction_result.new_value.title().split()
            if len(name_parts) >= 2:
                self.booking_info.update_customer_info("first_name", name_parts[0], confidence=0.9, source="llm_correction")
                self.booking_info.update_customer_info("last_name", " ".join(name_parts[1:]), confidence=0.9, source="llm_correction")
            else:
                self.booking_info.update_customer_info("first_name", correction_result.new_value.title(), confidence=0.8, source="llm_correction")
            
        elif correction_result.correction_type == 'departure_city':
            city = self._extract_city(correction_result.new_value) or correction_result.new_value.title()
            self.booking_info.update_trip_info("departure_city", city, confidence=0.9, source="llm_correction")
            
        elif correction_result.correction_type == 'destination_city':
            city = self._extract_city(correction_result.new_value) or correction_result.new_value.title()
            self.booking_info.update_trip_info("arrival_city", city, confidence=0.9, source="llm_correction")
            
        elif correction_result.correction_type == 'departure_date':
            parsed_date = self._parse_date(correction_result.new_value)
            if parsed_date:
                self.booking_info.update_trip_info("departure_date", parsed_date, confidence=0.9, source="llm_correction")
                correction_result.new_value = parsed_date  # Update for response
                
        elif correction_result.correction_type == 'return_date':
            parsed_date = self._parse_date(correction_result.new_value)
            if parsed_date:
                self.booking_info.update_trip_info("return_date", parsed_date, confidence=0.9, source="llm_correction")
                correction_result.new_value = parsed_date
                
        elif correction_result.correction_type == 'trip_type':
            if 'round' in correction_result.new_value.lower():
                self.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="llm_correction")
                if not self._get_return_date() and self._get_departure_date():
                    # Need to collect return date
                    self.state = BookingState.COLLECTING_RETURN_DATE
                    response = self.llm_correction_handler.generate_correction_response(
                        correction_result.correction_type, 
                        old_value, 
                        "round trip"
                    )
                    return f"{response} When would you like to return?"
            else:
                self.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="llm_correction")
        
        # Generate response
        response = self.llm_correction_handler.generate_correction_response(
            correction_result.correction_type,
            str(old_value) if old_value else "not set",
            correction_result.new_value
        )
        
        # Continue with the flow using the new method
        response += " " + self._determine_next_step()
        
        return response
    
    def _is_likely_name_correction(self, user_input: str, extracted_name: str) -> bool:
        """Check if the user input is likely correcting their name"""
        user_lower = user_input.lower()
        
        # If the extracted name contains obvious trip-related words, it's not a name
        trip_keywords = ['trip', 'round', 'one way', 'flight', 'travel', 'going', 'return', 'coming', 'back']
        if any(keyword in extracted_name.lower() for keyword in trip_keywords):
            return False
        
        # If the input contains explicit name correction phrases, it's likely a name
        name_correction_phrases = ['my name is', 'name is actually', 'call me', 'actually my name', 'i am', "i'm"]
        if any(phrase in user_lower for phrase in name_correction_phrases):
            return True
        
        # If the extracted name is very long (more than 4 words), it's probably not a name
        if len(extracted_name.split()) > 4:
            return False
        
        # If the input mentions trip type, it's not a name correction
        if any(phrase in user_lower for phrase in ['round trip', 'one way', 'return', 'flight']):
            return False
        
        # If we already have a name and this doesn't look like a name correction, skip it
        existing_name = self._get_customer_name()
        if existing_name and not any(phrase in user_lower for phrase in ['actually', 'correction', 'wrong']):
            return False
        
        return True
    
    def _transition_state(self, new_state: BookingState, reason: str = ""):
        """Transition to a new state with logging"""
        old_state = self.state
        self.state = new_state
        self.logger.info(f"State transition: {old_state.value} -> {new_state.value} ({reason})")
    
    def _determine_next_step(self) -> str:
        """Determine the next step based on missing information without forcing state changes"""
        if not self._get_customer_name():
            if self.state != BookingState.COLLECTING_NAME:
                self._transition_state(BookingState.COLLECTING_NAME, "Missing customer name")
            return "May I have your name please?"
        elif not self._get_departure_city():
            if self.state != BookingState.COLLECTING_DEPARTURE:
                self._transition_state(BookingState.COLLECTING_DEPARTURE, "Missing departure city")
            return "Which city are you flying from?"
        elif not self._get_arrival_city():
            if self.state != BookingState.COLLECTING_DESTINATION:
                self._transition_state(BookingState.COLLECTING_DESTINATION, "Missing destination city")
            return "Where are you headed?"
        elif not self._get_trip_type():
            if self.state != BookingState.COLLECTING_TRIP_TYPE:
                self._transition_state(BookingState.COLLECTING_TRIP_TYPE, "Missing trip type")
            return "Would you like a one-way or round trip flight?"
        elif not self._get_departure_date():
            if self.state != BookingState.COLLECTING_DATE:
                self._transition_state(BookingState.COLLECTING_DATE, "Missing departure date")
            return "When are you looking to travel?"
        elif self._is_roundtrip() and not self._get_return_date():
            if self.state != BookingState.COLLECTING_RETURN_DATE:
                self._transition_state(BookingState.COLLECTING_RETURN_DATE, "Missing return date")
            return "And when do you want to come back?"
        else:
            if self.state != BookingState.PRESENTING_OPTIONS:
                self._transition_state(BookingState.PRESENTING_OPTIONS, "All information collected")
            return self._present_flight_options()
    
    def _is_flexible_date_request(self, user_input: str) -> bool:
        """Check if user is asking for flexible date options"""
        user_lower = user_input.lower()
        
        # Don't trigger flexible search if we're already presenting options
        if self.state == BookingState.PRESENTING_OPTIONS:
            # Only trigger if explicitly asking for cheaper options
            price_keywords = ['cheapest', 'cheaper', 'lowest price', 'best deal', 'best price']
            return any(keyword in user_lower for keyword in price_keywords)
        
        flexible_keywords = [
            'cheapest', 'cheapest day', 'cheapest flight', 'lowest price',
            'best deal', 'best price', 'most affordable',
            'flexible', 'flexible date', 'flexible dates',
            'any day', 'whenever', 'anytime',
            'cheapest day next week', 'cheapest in', 'best price next',
            'most affordable day', 'lowest fare'
        ]
        
        return any(keyword in user_lower for keyword in flexible_keywords)
    
    def _handle_flexible_date_request(self, user_input: str) -> str:
        """Handle flexible date search requests"""
        self._transition_state(BookingState.FLEXIBLE_SEARCH, "User requested flexible search")
        
        # Check if we have departure and destination
        departure = self._get_departure_city()
        destination = self._get_arrival_city()
        
        if not departure or not destination:
            return "I'd love to find you the best deals! Let me just get a few details first. " + self._determine_next_step()
        
        # Parse the flexible request
        user_lower = user_input.lower()
        
        if 'next week' in user_lower:
            time_frame = 'next week'
        elif 'next month' in user_lower:
            time_frame = 'next month'
        elif 'this month' in user_lower:
            time_frame = 'this month'
        else:
            time_frame = 'next 30 days'
        
        # Store flexible search preferences
        self.context['flexible_search'] = {
            'criteria': 'cheapest' if 'cheap' in user_lower else 'best_deal',
            'time_frame': time_frame,
            'flexible_dates': True
        }
        
        return self._present_flexible_options()
    
    def _handle_flexible_search(self, user_input: str) -> str:
        """Handle input in flexible search state"""
        user_lower = user_input.lower()
        
        # Check if user is selecting a specific option
        if any(word in user_lower for word in ['1', 'one', 'first', 'tuesday']):
            # User selected Tuesday option
            self.booking_info.update_trip_info('departure_date', 'Tuesday, August 6th', confidence=1.0)
            selected_flight = {'option': 1, 'price': 295, 'time': '8:30 AM', 'date': 'Tuesday, August 6th'}
        elif any(word in user_lower for word in ['2', 'two', 'second', 'wednesday']):
            # User selected Wednesday option
            self.booking_info.update_trip_info('departure_date', 'Wednesday, August 7th', confidence=1.0)
            selected_flight = {'option': 2, 'price': 320, 'time': '2:15 PM', 'date': 'Wednesday, August 7th'}
        elif any(word in user_lower for word in ['3', 'three', 'third', 'friday']):
            # User selected Friday option
            self.booking_info.update_trip_info('departure_date', 'Friday, August 9th', confidence=1.0)
            selected_flight = {'option': 3, 'price': 340, 'time': '6:45 PM', 'date': 'Friday, August 9th'}
        else:
            return "Which of those flexible options works for you? Just say 1, 2, or 3, or tell me a specific day."
        
        # Store the selected flight and transition to confirmation
        self.context['selected_flight'] = selected_flight
        self._transition_state(BookingState.CONFIRMING_SELECTION, "Flexible option selected")
        
        departure_city = self._get_departure_city()
        arrival_city = self._get_arrival_city()
        
        return f"Perfect! I got you an amazing deal: {departure_city} to {arrival_city} on {selected_flight['date']}, leaving at {selected_flight['time']} for ${selected_flight['price']}. That's $45 less than the regular price! Ready to book it?"
    
    def _present_flexible_options(self) -> str:
        """Present flexible date options with best prices"""
        departure = self._get_departure_city()
        destination = self._get_arrival_city()
        time_frame = self.context.get('flexible_search', {}).get('time_frame', 'next week')
        
        return f"""Awesome! I found some great deals from {departure} to {destination} for {time_frame}:

Here are your flexible options:
1. Tuesday, Aug 6th - $295 (Save $45!) - Departs 8:30 AM
2. Wednesday, Aug 7th - $320 (Save $20!) - Departs 2:15 PM  
3. Friday, Aug 9th - $340 (Regular price) - Departs 6:45 PM

Which one works best for your schedule?"""
    
    def _present_flight_options(self) -> str:
        """Present available flight options"""
        # This method returns a placeholder that voice_agent.py will replace with real flights
        trip_type = "one-way" if not self._is_roundtrip() else "round trip"
        dep_date = self._get_departure_date()
        departure_city = self._get_departure_city()
        arrival_city = self._get_arrival_city()
        
        # Include return date info if round trip
        date_info = f"on {dep_date}"
        if self._is_roundtrip():
            return_date = self._get_return_date()
            if return_date:
                date_info = f"departing {dep_date}, returning {return_date}"
        
        # Return a search message that will trigger flight search in voice_agent
        # This ensures the state is correct for the voice_agent to intercept
        return f"Let me find you some great {trip_type} flights from {departure_city} to {arrival_city} {date_info}..."


# Test the booking flow
if __name__ == "__main__":
    print("Testing Booking Flow State Machine\n")
    
    flow = BookingFlow()
    
    # Simulate a conversation
    test_inputs = [
        "Hi there",
        "My name is John Smith",
        "I'm flying from San Francisco", 
        "I need to go to New York",
        "Next Friday, and I'll need a return flight",
        "Sunday evening",
        "I'll take option 1",
        "Yes, book it"
    ]
    
    for user_input in test_inputs:
        print(f"User: {user_input}")
        response = flow.process_input(user_input)
        print(f"Alex: {response}")
        print(f"State: {flow.state.value}\n")
    
    print("\nFinal enhanced booking info:")
    print(json.dumps(flow.booking_info.to_dict(), indent=2))
    
    print("\nBasic booking info (for compatibility):")
    print(json.dumps(flow.booking_info.to_basic_booking_info(), indent=2))