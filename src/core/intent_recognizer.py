#!/usr/bin/env python3
"""
Intent Recognition System
Uses Groq LLM to classify user intent and extract entities for the United Airlines booking flow
"""

import json
import re
import time
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from groq import Groq
import os
from src.core.content_filter import ContentFilter, InappropriateType

@dataclass
class IntentResult:
    """Structured result from intent recognition"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    raw_response: str
    
    def to_dict(self):
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "raw_response": self.raw_response
        }


class IntentRecognizer:
    """Intent recognition system using Groq LLM"""
    
    def __init__(self):
        """Initialize the intent recognizer with Groq client"""
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.content_filter = ContentFilter()
        self.logger = logging.getLogger(__name__)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        
        # Define intent types
        self.intent_types = [
            "provide_name",
            "provide_city", 
            "provide_date",
            "time_preference",  # For "anytime", "flexible about time"
            "confirm_yes",
            "confirm_no",
            "correction",
            "question",
            "cancel",
            "flexible_search",
            "select_option",  # For selecting flight options: "one", "first", "option 1"
            "inappropriate_content"  # New intent for filtered content
        ]
        
        # Common city variations for entity extraction
        self.city_variations = {
            "san francisco": ["sf", "san fran", "sfo"],
            "new york": ["ny", "nyc", "new york city"],
            "los angeles": ["la", "lax"],
            "chicago": ["chi", "chitown"],
            "boston": ["bos"],
            "miami": ["mia"],
            "seattle": ["sea"],
            "denver": ["den"],
            "dallas": ["dfw"],
            "atlanta": ["atl"],
            "washington": ["dc", "washington dc"],
            "houston": ["hou"],
            "phoenix": ["phx"],
            "philadelphia": ["philly", "phl"],
            "detroit": ["det"],
            "minneapolis": ["minn", "twin cities"],
            "orlando": ["orl"],
            "las vegas": ["vegas", "las", "sin city"],
            "nashville": ["nash"],
            "portland": ["pdx"],
            "salt lake city": ["slc"],
            "charlotte": ["clt"],
            "pittsburgh": ["pitt"],
            "cincinnati": ["cincy"],
            "cleveland": ["cle"],
            "baltimore": ["balt"],
            "kansas city": ["kc"],
            "san diego": ["sd"],
            "san antonio": ["sa"],
            "austin": ["atx"],
            "raleigh": ["rdu"],
            "tampa": ["tpa"],
            "jacksonville": ["jax"],
            "memphis": ["mem"],
            "milwaukee": ["mil"],
            "indianapolis": ["indy"],
            "columbus": ["col"]
        }
    
    def recognize_intent(self, user_input: str, current_state: str, booking_info: Dict = None) -> IntentResult:
        """
        Recognize user intent and extract entities from the input
        
        Args:
            user_input: The user's spoken/typed input
            current_state: Current state in the booking flow
            booking_info: Current booking information for context
        
        Returns:
            IntentResult with intent classification and extracted entities
        """
        # First, filter and sanitize the input
        is_appropriate, filtered_input, filter_reason = self.content_filter.filter_inappropriate_content(user_input)
        
        if not is_appropriate:
            self.logger.warning(f"Filtered inappropriate content: {filter_reason}")
            # Return a special intent for inappropriate content
            return IntentResult(
                intent="inappropriate_content",
                confidence=1.0,
                entities={"filter_reason": filter_reason, "original_input": user_input},
                raw_response=f"Content filtered: {filter_reason}"
            )
        
        # Sanitize input for API call
        sanitized_input = self.content_filter.sanitize_for_api(filtered_input)
        
        # Try LLM recognition with retry logic
        for attempt in range(self.max_retries):
            try:
                return self._call_llm_with_retry(sanitized_input, current_state, booking_info, attempt)
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"All LLM attempts failed, falling back to rule-based classification")
                    break
                
                # Exponential backoff
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
        
        # Fallback to rule-based classification
        return self._fallback_classification(sanitized_input, current_state)
    
    def _call_llm_with_retry(self, user_input: str, current_state: str, booking_info: Dict, attempt: int) -> IntentResult:
        """Call LLM API with proper error handling"""
        try:
            # Build concise prompt
            prompt = self._build_intent_prompt(user_input, current_state, booking_info)
            
            # Call Groq API with correct model name
            response = self.client.chat.completions.create(
                model="gemma2-9b-it",  # Using Gemma 2 9B for tool calling
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent classifier for airline bookings. Always respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=300  # Reduced token limit
            )
            
            # Parse the LLM response
            raw_response = response.choices[0].message.content.strip()
            intent_data = self._parse_llm_response(raw_response)
            
            # Extract and normalize entities
            entities = self._extract_entities(user_input, intent_data.get("entities", {}))
            
            return IntentResult(
                intent=intent_data.get("intent", "question"),
                confidence=intent_data.get("confidence", 0.5),
                entities=entities,
                raw_response=raw_response
            )
            
        except Exception as e:
            self._log_api_error(e, attempt, user_input)
            raise e
    
    def _build_intent_prompt(self, user_input: str, current_state: str, booking_info: Dict = None) -> str:
        """Build a concise prompt for intent classification"""
        
        # Keep context minimal to avoid prompt size issues
        context = f"State: {current_state}"
        if booking_info and len(str(booking_info)) < 200:  # Only include if small
            context += f"\nBooking: {json.dumps(booking_info)}"
        
        prompt = f"""Classify intent and extract entities.

{context}
Input: "{user_input}"

Intents: provide_name, provide_city, provide_date, time_preference, confirm_yes, confirm_no, correction, question, cancel, flexible_search, select_option

Entities: name, departure_city, destination_city, departure_date, return_date, trip_type, option_number

CRITICAL RULES:
- NEVER extract names from phrases like "I'm planning", "I want to", "I need", "I'd like to" - these are trip descriptions
- In state "GREETING" or "COLLECTING_NAME": Only extract actual personal names, not trip descriptions
- "I'm planning a one-way trip from X to Y" = provide_city intent with departure_city: X, destination_city: Y, trip_type: one_way
- If user provides trip details when greeting, extract cities and trip type but NOT a name

IMPORTANT: 
- If state is "presenting_options" and user says words like "one", "first", "option 1", use "select_option" intent
- If state is "collecting_trip_type": classify as "provide_city" intent and extract trip_type entity
- Always detect trip type: "round trip", "roundtrip" = trip_type: "round_trip". "One way", "one-way", "one" = trip_type: "one_way"
- Only extract cities when explicitly mentioned as locations
- For names, only extract if user says "My name is X" or "I'm X" (where X is clearly a personal name)
- Trip planning phrases should be classified as provide_city or provide_date, NOT provide_name

JSON format:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "entities": {{}}
}}"""
        
        return prompt
    
    def _parse_llm_response(self, raw_response: str) -> Dict:
        """Parse the LLM JSON response"""
        try:
            # Clean up the response - remove markdown formatting if present
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON
            result = json.loads(cleaned)
            
            # Validate required fields
            if "intent" not in result:
                result["intent"] = "question"
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "entities" not in result:
                result["entities"] = {}
                
            return result
            
        except json.JSONDecodeError:
            # Try to extract JSON from the response using regex
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Return default structure
            return {
                "intent": "question",
                "confidence": 0.3,
                "entities": {}
            }
    
    def _extract_entities(self, user_input: str, llm_entities: Dict) -> Dict[str, Any]:
        """Extract and normalize entities from user input"""
        entities = llm_entities.copy()
        user_lower = user_input.lower()
        
        # Handle "I'm from [city]" pattern - it's ambiguous and context-dependent
        # Don't automatically assign it as departure city
        im_from_pattern = r"i['']m from ([a-zA-Z\s]+)"
        if re.search(im_from_pattern, user_lower):
            # If LLM already classified it, trust that classification
            # Otherwise, let the booking flow determine based on state
            pass
        
        # Additional rule-based entity extraction to supplement LLM
        
        # Extract names if not already found
        if "name" not in entities:
            # First check if this is a trip planning statement
            trip_planning_patterns = [
                r"i['']m planning",
                r"i want to",
                r"i need to",
                r"i['']d like to",
                r"looking for",
                r"searching for",
                r"booking a",
                r"need a flight"
            ]
            
            # If user is describing trip plans, don't extract name
            if any(re.search(pattern, user_input, re.IGNORECASE) for pattern in trip_planning_patterns):
                pass  # Skip name extraction
            else:
                name_patterns = [
                    r'\b(?:my name is|i am|i\'m)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b',  # More specific pattern
                    r'\b(?:this is|it\'s|its)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b',
                    r'^([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s*$'  # Simple name at start
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, user_input, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip().title()
                        name_lower = name.lower()
                        
                        # Enhanced filtering to avoid extracting trip-related phrases as names
                        trip_related_words = ['planning', 'from', 'to', 'flying', 'going', 'trip', 
                                            'round', 'one way', 'way', 'flight', 'travel', 'return', 
                                            'coming', 'back', 'said', 'want', 'need', 'book', 'looking']
                        
                        # Don't extract as name if it contains trip-related words or is too long
                        if (len(name) > 1 and len(name.split()) <= 3 and 
                            not any(word in name_lower for word in trip_related_words)):
                            entities["name"] = name
                            break
        
        # Extract cities if not already found
        if "departure_city" not in entities and "destination_city" not in entities:
            city = self._extract_city_entity(user_input)
            if city:
                # Determine if it's departure or destination based on context
                # Be more careful with "from" - "I'm from X" is ambiguous
                if re.search(r"\b(leaving from|departing from|flying from)\b", user_lower):
                    entities["departure_city"] = city
                elif any(word in user_lower for word in ['to', 'going', 'destination']):
                    entities["destination_city"] = city
                elif re.search(r"\bi['']m from\b", user_lower):
                    # "I'm from" is ambiguous - let booking flow determine based on state
                    entities["city"] = city
                else:
                    # Default to providing as generic city
                    entities["city"] = city
        
        # Extract trip type
        if "trip_type" not in entities:
            if any(phrase in user_lower for phrase in ['round trip', 'return', 'coming back', 'and back']):
                entities["trip_type"] = "round_trip"
            elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'no return']):
                entities["trip_type"] = "one_way"
        
        # Extract dates (keep original date strings for date parser to handle)
        if "departure_date" not in entities and "return_date" not in entities:
            date_patterns = [
                r'\b(tomorrow|today|yesterday)\b',
                r'\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b',
                r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b',
                r'\b\d{1,2}-\d{1,2}(?:-\d{2,4})?\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    entities["date"] = match.group()
                    break
        
        return entities
    
    def _is_valid_city(self, city_name: str) -> bool:
        """Check if a string is a valid city name"""
        city_lower = city_name.lower().strip()
        
        # Check against known cities
        for city, variations in self.city_variations.items():
            if city_lower == city or city_lower in variations:
                return True
            # Check partial matches
            if city in city_lower or city_lower in city:
                return True
        
        # Basic validation - at least 2 chars, not a number
        if len(city_lower) >= 2 and not city_lower.isdigit():
            return True
            
        return False
    
    def _extract_city_entity(self, text: str) -> Optional[str]:
        """Extract city name from text"""
        text_lower = text.lower()
        
        # Remove common phrases
        cleaned = re.sub(r'\b(from|to|in|at|flying|going|departing|leaving|i want to go|i need to go)\b', '', text_lower)
        cleaned = cleaned.strip()
        
        # Check for known cities and their variations using word boundaries
        for city, variations in self.city_variations.items():
            # Use word boundaries to avoid false matches like "ny" in "anytime"
            if re.search(r'\b' + re.escape(city) + r'\b', cleaned):
                return city.title()
            
            for variation in variations:
                # Use word boundaries for variations too
                if re.search(r'\b' + re.escape(variation) + r'\b', cleaned):
                    return city.title()
        
        # Check for airport codes (3 letters)
        airport_match = re.search(r'\b([A-Z]{3})\b', text.upper())
        if airport_match:
            # Map common airport codes to cities
            airport_codes = {
                'SFO': 'San Francisco',
                'JFK': 'New York', 'LGA': 'New York', 'EWR': 'New York',
                'LAX': 'Los Angeles',
                'ORD': 'Chicago', 'MDW': 'Chicago',
                'BOS': 'Boston',
                'MIA': 'Miami',
                'SEA': 'Seattle',
                'DEN': 'Denver',
                'DFW': 'Dallas',
                'ATL': 'Atlanta',
                'IAH': 'Houston', 'HOU': 'Houston',
                'PHX': 'Phoenix',
                'PHL': 'Philadelphia',
                'DTW': 'Detroit',
                'MSP': 'Minneapolis',
                'MCO': 'Orlando',
                'LAS': 'Las Vegas',
                'BNA': 'Nashville',
                'PDX': 'Portland',
                'SLC': 'Salt Lake City',
                'CLT': 'Charlotte'
            }
            
            code = airport_match.group(1)
            if code in airport_codes:
                return airport_codes[code]
        
        return None
    
    def _log_api_error(self, error: Exception, attempt: int, user_input: str):
        """Log API errors with specific details"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Extract specific error details from Groq API errors
        if hasattr(error, 'response') and error.response:
            try:
                error_details = error.response.json() if hasattr(error.response, 'json') else {}
                status_code = getattr(error.response, 'status_code', 'unknown')
                self.logger.error(
                    f"Groq API Error - Attempt {attempt + 1}: "
                    f"Status: {status_code}, "
                    f"Type: {error_type}, "
                    f"Message: {error_msg}, "
                    f"Details: {error_details}, "
                    f"Input length: {len(user_input)}"
                )
            except:
                self.logger.error(
                    f"Groq API Error - Attempt {attempt + 1}: "
                    f"Type: {error_type}, "
                    f"Message: {error_msg}, "
                    f"Input length: {len(user_input)}"
                )
        else:
            self.logger.error(
                f"API Error - Attempt {attempt + 1}: "
                f"Type: {error_type}, "
                f"Message: {error_msg}, "
                f"Input: {user_input[:100]}..."
            )
    
    def _fallback_classification(self, user_input: str, current_state: str) -> IntentResult:
        """Enhanced fallback rule-based intent classification when LLM fails"""
        user_lower = user_input.lower()
        entities = {}
        
        # Simple rule-based intent classification - CHECK TRIP PLANNING FIRST
        if any(word in user_lower for word in ['from', 'to', 'flying', 'going', 'trip', 'planning', 'book']):
            # Handle complex trip planning sentences BEFORE name extraction
            intent = "provide_city"
            confidence = 0.7
            
            # Extract departure city (from pattern)
            from_pattern = r'\b(?:from|leaving from|departing from)\s+([A-Za-z\s]+?)(?:\s+(?:to|for|,)|$)'
            from_match = re.search(from_pattern, user_input, re.IGNORECASE)
            if from_match:
                dep_city = from_match.group(1).strip()
                if self._is_valid_city(dep_city):
                    entities["departure_city"] = dep_city
            
            # Extract destination city (to pattern) - improved to stop at common end words
            to_pattern = r'\b(?:to|going to|headed to|destination)\s+([A-Za-z\s]+?)(?:\s+(?:from|on|in|for|next|tomorrow|today|,)|$)'
            to_match = re.search(to_pattern, user_input, re.IGNORECASE)
            if to_match:
                dest_city = to_match.group(1).strip()
                if self._is_valid_city(dest_city):
                    entities["destination_city"] = dest_city
            
            # Extract trip type
            if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return']):
                entities["trip_type"] = "round_trip"
            elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'oneway']):
                entities["trip_type"] = "one_way"
            
            # Extract date if mentioned
            if 'october' in user_lower:
                entities["departure_date"] = "October"
            elif any(month in user_lower for month in ['january', 'february', 'march', 'april', 'may', 'june', 
                                                       'july', 'august', 'september', 'november', 'december']):
                for month in ['january', 'february', 'march', 'april', 'may', 'june', 
                             'july', 'august', 'september', 'november', 'december']:
                    if month in user_lower:
                        entities["departure_date"] = month.capitalize()
                        break
        elif any(word in user_lower for word in ['yes', 'yeah', 'sure', 'correct', 'book', 'confirm', 'ok', 'okay']):
            intent = "confirm_yes"
            confidence = 0.8
        elif any(word in user_lower for word in ['no', 'nope', 'cancel', 'wrong', 'wait', 'actually']):
            intent = "confirm_no" 
            confidence = 0.8
        elif current_state == "collecting_trip_type":
            # In trip type collection state, specifically look for trip type indicators
            intent = "provide_city"  # The booking flow expects provide_city with trip_type entity
            confidence = 0.9
            
            # Check for trip type patterns
            if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'return', 'coming back', 'both ways', 'round', 'back']):
                entities["trip_type"] = "round_trip"
            elif any(phrase in user_lower for phrase in ['one way', 'one-way', 'oneway', 'one direction', 'just going', 'no return', 'one', 'single']):
                entities["trip_type"] = "one_way"
            else:
                # If no clear trip type detected, still use provide_city but lower confidence
                confidence = 0.5
        elif current_state == "collecting_name" and len(user_input.split()) <= 3 and re.match(r'^[A-Za-z\s]+$', user_input):
            # In name collection state, treat simple 1-3 word inputs as names
            intent = "provide_name"
            confidence = 0.8
            entities["name"] = user_input.strip().title()
        elif any(phrase in user_lower for phrase in ['my name is', 'i am', "i'm", 'this is']) and not any(word in user_lower for word in ['planning', 'trip', 'from', 'to']):
            # Only extract name if NOT talking about trip planning
            intent = "provide_name"
            confidence = 0.7
            # Try to extract name and validate it
            name_match = re.search(r'(?:my name is|i am|i\'m|this is)\s+([a-zA-Z\s]+)', user_input, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip().title()
                if self.content_filter.is_valid_name(extracted_name):
                    entities["name"] = extracted_name
                else:
                    intent = "inappropriate_content"
                    entities["filter_reason"] = "Invalid name provided"
        elif any(phrase in user_lower for phrase in ['anytime', 'any time', 'flexible about', 'no preference', 'whenever', 'doesn\'t matter']) and current_state == "collecting_date":
            intent = "time_preference"
            confidence = 0.8
        elif current_state == "presenting_options" and any(word in user_lower for word in ['1', 'one', 'first', '2', 'two', 'second', '3', 'three', 'third', 'option', 'cheapest', 'earliest', 'latest']):
            intent = "select_option"
            confidence = 0.8
            # Extract option number - be more specific about matching
            if any(word in user_lower for word in ['2', 'two']) or 'second' in user_lower:
                entities["option_number"] = 2
            elif any(word in user_lower for word in ['3', 'three']) or 'third' in user_lower or 'latest' in user_lower:
                entities["option_number"] = 3
            else:  # Default to option 1 for 'one', 'first', 'cheapest', 'earliest', etc.
                entities["option_number"] = 1
        elif any(word in user_lower for word in ['cheapest', 'cheapest day', 'flexible date', 'best deal', 'best price', 'most affordable', 'lowest price']):
            intent = "flexible_search"
            confidence = 0.8
        elif any(word in user_lower for word in ['tomorrow', 'today', 'next', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']) or re.search(r'\d+[/-]\d+', user_input):
            intent = "provide_date"
            confidence = 0.7
        elif user_input.endswith('?') or any(word in user_lower for word in ['what', 'when', 'where', 'how', 'why', 'which']):
            intent = "question"
            confidence = 0.6
        else:
            intent = "question"
            confidence = 0.4
        
        self.logger.info(f"Using fallback classification: {intent} (confidence: {confidence})")
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_response=f"Fallback classification: {intent}"
        )


# Test the intent recognizer
if __name__ == "__main__":
    print("Testing Intent Recognizer\n")
    
    recognizer = IntentRecognizer()
    
    test_inputs = [
        ("My name is John Smith", "collecting_name"),
        ("I'm flying from San Francisco", "collecting_departure"),
        ("I need to go to New York", "collecting_destination"), 
        ("Next Friday", "collecting_date"),
        ("Yes, book it", "confirming_selection"),
        ("No, actually I want to go to Miami", "confirming_selection"),
        ("What options do you have?", "presenting_options"),
        ("Cancel my booking", "any_state")
    ]
    
    for user_input, state in test_inputs:
        print(f"Input: '{user_input}' (State: {state})")
        result = recognizer.recognize_intent(user_input, state)
        print(f"Intent: {result.intent} (confidence: {result.confidence})")
        print(f"Entities: {result.entities}")
        print("---")