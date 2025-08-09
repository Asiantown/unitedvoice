#!/usr/bin/env python3
"""
United Airlines Voice Agent with Booking Flow
Complete voice-enabled flight booking system
"""

import os
import sys
import time
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None
    np = None
from elevenlabs.client import ElevenLabs
try:
    from elevenlabs import play as elevenlabs_play
except ImportError:
    elevenlabs_play = None
from src.services.groq_client import GroqClient
from src.services.groq_whisper import GroqWhisperClient
from src.config.settings import settings
from dotenv import load_dotenv
import json
import wave
import logging
import re

# Import our booking components
from src.core.booking_flow import BookingFlow, BookingState
from src.services.google_flights_api import GoogleFlightsAPI

# Load environment variables
load_dotenv()


class UnitedVoiceAgent:
    """Complete voice agent with booking capabilities"""
    
    def __init__(self):
        """Initialize voice agent with all components"""
        print("United Airlines AI Voice Agent")
        print("="*50)
        
        # Clear any persistent data on startup
        self._clear_persistent_data()
        
        # Initialize components
        self.setup_stt()
        self.setup_llm()
        self.setup_tts()
        
        # Setup logging for debugging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize booking system
        self.booking_flow = BookingFlow()
        
        # Initialize flight API (Google Flights via SerpApi)
        try:
            self.flight_api = GoogleFlightsAPI()
            self.logger.info("Google Flights API initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Google Flights API: {e}")
            self.logger.warning("Flight search functionality will be limited")
            self.flight_api = None
        
        # Conversation state
        self.conversation_history = []
        
        print("\nUnited Airlines Voice Agent Ready!")
        print("="*50)
    
    def _clean_markdown_for_voice(self, text):
        """Clean markdown formatting from text for voice output"""
        if not text:
            return text
        
        # Remove markdown bold formatting (**text** and __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Remove markdown italic formatting (*text* and _text_) - simpler approach
        # Handle single asterisks that aren't part of double asterisks
        text = re.sub(r'\*([^*]+?)\*', r'\1', text)
        text = re.sub(r'\b_([^_]+?)_\b', r'\1', text)
        
        # Remove markdown headers (# text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove markdown list markers (- text, * text, + text)
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown numbered list markers (1. text, 2. text, etc.)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown code formatting (`code` and ```code```)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'```(.+?)```', r'\1', text, flags=re.DOTALL)
        
        # Remove markdown links [text](url) - keep just the text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # Clean up any double spaces created by removals
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _clear_persistent_data(self):
        """Clear any persistent data from previous sessions"""
        # Clear any temporary files
        import glob
        temp_files = glob.glob("temp_audio*.wav")
        for f in temp_files:
            try:
                os.remove(f)
            except:
                pass
    
    def setup_stt(self):
        """Initialize Speech-to-Text with Groq Whisper Turbo"""
        print("Setting up Speech-to-Text...")
        try:
            groq_api_key = settings.groq.api_key or os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise Exception("Missing GROQ_API_KEY for Whisper")
            
            self.whisper_client = GroqWhisperClient(api_key=groq_api_key)
            
            # Test connection
            if self.whisper_client.test_connection():
                print("✓ STT ready (Groq Whisper Turbo)")
            else:
                raise Exception("Groq Whisper connection failed")
                
            # Audio settings remain the same
            self.sample_rate = settings.whisper.sample_rate
            self.channels = settings.whisper.channels
            
        except Exception as e:
            print(f"❌ STT error: {e}")
            sys.exit(1)
    
    def setup_llm(self):
        """Initialize Language Model with Groq"""
        print("Setting up Language Model...")
        try:
            groq_api_key = settings.groq.api_key or os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise Exception("Missing GROQ_API_KEY")
            
            print("   Creating Groq client...")
            self.groq_client = GroqClient(api_key=groq_api_key)
            
            print("   Testing connection...")
            success, message = self.groq_client.test_connection()
            
            if success:
                print("✓ LLM ready (Groq)")
            else:
                raise Exception(f"Groq connection failed: {message}")
        except Exception as e:
            print(f"LLM error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def setup_tts(self):
        """Initialize Text-to-Speech"""
        print("Setting up Text-to-Speech...")
        api_key = settings.elevenlabs.api_key or os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("Missing ELEVENLABS_API_KEY!")
            sys.exit(1)
        
        self.elevenlabs_client = ElevenLabs(api_key=api_key)
        self.tts_voice_id = self.get_voice_id(settings.elevenlabs.voice_name)
        print("✓ TTS ready")
    
    def get_voice_id(self, voice_name="Eric"):
        """Get ElevenLabs voice ID"""
        try:
            response = self.elevenlabs_client.voices.get_all()
            for voice in response.voices:
                if voice.name == voice_name:
                    return voice.voice_id
            # If voice not found, use first available voice
            if response.voices:
                print(f"Voice '{voice_name}' not found, using '{response.voices[0].name}'")
                return response.voices[0].voice_id
            else:
                raise Exception("No voices available")
        except Exception as e:
            print(f"Warning: Could not fetch voices: {e}")
            # Try to use default voice ID from settings
            default_id = getattr(settings.elevenlabs, 'voice_id', None)
            if default_id:
                return default_id
            # Use a common default voice ID as last resort
            return "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    
    def _store_mock_flights(self):
        """Store mock flight data for selection"""
        mock_flights = [
            {
                "airline": "United Airlines",
                "flight_number": "UA523",
                "departure_time": "7:15 AM",
                "arrival_time": "10:00 AM",
                "duration": "3 hours 45 minutes",
                "type": "nonstop",
                "price": 289,
                "departure_city": "San Francisco",
                "arrival_city": "New York",
                "seats_available": 15,
                "cabin_class": "economy"
            },
            {
                "airline": "United Airlines",
                "flight_number": "UA1247", 
                "departure_time": "12:30 PM",
                "arrival_time": "6:15 PM",
                "duration": "5 hours 45 minutes",
                "type": "1 stop",
                "price": 245,
                "departure_city": "San Francisco",
                "arrival_city": "New York",
                "seats_available": 8,
                "cabin_class": "economy"
            },
            {
                "airline": "American Airlines",
                "flight_number": "AA2156",
                "departure_time": "2:45 PM", 
                "arrival_time": "8:05 PM",
                "duration": "5 hours 20 minutes",
                "type": "1 stop",
                "price": 198,
                "departure_city": "San Francisco",
                "arrival_city": "New York",
                "seats_available": 12,
                "cabin_class": "economy"
            }
        ]
        self.booking_flow.context['available_flights'] = mock_flights

    def _get_mock_flight_options(self, departure_city: str, destination_city: str, departure_date: str) -> str:
        """Provide mock flight options when API is unavailable"""
        return f"""Great! I found 3 flights from {departure_city} to {destination_city} on {departure_date}:

Option 1: Morning departure at 7:15 AM on United Airlines flight UA523 - nonstop flight, 3 hours 45 minutes, for $289

Option 2: Afternoon at 12:30 PM on United Airlines flight UA1247 - with one stop, 5 hours 45 minutes, for $245

Option 3: Alternative at 2:45 PM on American Airlines flight AA2156 - 1 stop, 5 hours 20 minutes, for $198

Which one catches your eye?"""
    
    def record_audio(self, duration=None):
        """Record audio from microphone"""
        if duration is None:
            duration = settings.default_recording_duration
        print(f"\nListening for {duration} seconds...")
        print("Speak now!")
        
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32
        )
        sd.wait()
        
        print("✓ Recording complete")
        return audio_data
    
    def transcribe_audio(self, audio_data):
        """Convert audio to text using Groq Whisper Turbo"""
        print("Transcribing...")
        
        # Save audio temporarily
        temp_file = "temp_audio.wav"
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(temp_file, 'w') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        try:
            # Transcribe using Groq Whisper Turbo
            transcription = self.whisper_client.transcribe_audio_file(
                temp_file,
                language="en"
            )
            
            print(f"✓ Heard: '{transcription}'")
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            transcription = ""
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return transcription
    
    def get_response(self, user_input):
        """Get response using intent-based booking flow and LLM"""
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Check if user is changing trip type while in presenting options (clear cached flights)
        if (self.booking_flow.state == BookingState.PRESENTING_OPTIONS and 
            any(phrase in user_input.lower() for phrase in ['round trip', 'roundtrip', 'round-trip', 'one way', 'one-way', 'oneway'])):
            # Clear cached flights to force new search
            if 'available_flights' in self.booking_flow.context:
                del self.booking_flow.context['available_flights']
                self.logger.info("Cleared cached flights due to trip type change")
        
        # Process through intent-based booking flow
        booking_response = self.booking_flow.process_input_with_intent(user_input)
        
        # Get current state with enhanced information
        state_info = self.booking_flow.get_current_state()
        
        # Log intent recognition for debugging
        try:
            intent_result = self.booking_flow.intent_recognizer.recognize_intent(
                user_input, 
                self.booking_flow.state.value, 
                self.booking_flow.booking_info.to_basic_booking_info()
            )
            self.logger.info(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
            self.logger.info(f"Entities: {intent_result.entities}")
            self.logger.info(f"Current state: {self.booking_flow.state.value}")
        except Exception as e:
            self.logger.warning(f"Intent logging failed: {e}")
        
        # If we're in presenting options state and need flight data
        if self.booking_flow.state == BookingState.PRESENTING_OPTIONS:
            booking_info = self.booking_flow.booking_info
            # Access departure and destination through trip object
            departure_city = booking_info.trip.departure_city.value if booking_info.trip.departure_city else None
            destination_city = booking_info.trip.arrival_city.value if booking_info.trip.arrival_city else None
            departure_date = booking_info.trip.departure_date.value if booking_info.trip.departure_date else None
            return_date = booking_info.trip.return_date.value if booking_info.trip.return_date else None
            
            # Log current state for debugging
            self.logger.info(f"PRESENTING_OPTIONS - From: {departure_city}, To: {destination_city}, Date: {departure_date}")
            self.logger.info(f"Flight API available: {self.flight_api is not None}")
            
            # Only search if we don't have cached flights or if the booking response indicates we need to search
            needs_flight_search = (
                not self.booking_flow.context.get('available_flights') or 
                "Let me find you" in booking_response or
                "I need to search" in booking_response
            )
            
            # Also check if user is giving a generic positive response when no flights are cached
            if not self.booking_flow.context.get('available_flights'):
                user_lower = user_input.lower().strip()
                positive_responses = ['ok', 'okay', 'yes', 'sure', 'sounds good', 'go ahead', 'please', 'alright']
                if any(resp in user_lower for resp in positive_responses):
                    needs_flight_search = True
                    self.logger.info("User gave positive response with no cached flights - triggering search")
            
            if departure_city and destination_city and needs_flight_search:
                if self.flight_api:
                    # Search for real flights using Google Flights API
                    try:
                        self.logger.info(f"Searching flights: {departure_city} to {destination_city}")
                        
                        # Determine trip type - use the stored trip_type if available, otherwise fallback to return_date check
                        stored_trip_type = booking_info.trip.trip_type.value if booking_info.trip.trip_type else None
                        if stored_trip_type:
                            # Use the stored trip type (convert "roundtrip" to "round_trip" for API compatibility)
                            trip_type = "round_trip" if stored_trip_type.lower() == "roundtrip" else "one_way"
                        else:
                            # Fallback to checking return date presence
                            trip_type = "round_trip" if return_date else "one_way"
                        
                        # Call Google Flights API
                        flight_results = self.flight_api.search_flights(
                            departure_city=departure_city,
                            arrival_city=destination_city,
                            departure_date=departure_date if departure_date else "next week",
                            return_date=return_date,
                            trip_type=trip_type,
                            passengers=1,
                            cabin_class="economy"
                        )
                        
                        # Format flight options
                        if flight_results:
                            # Store flight options in booking flow context for selection
                            self.booking_flow.context['available_flights'] = flight_results[:3]  # Store top 3 options
                            
                            # Prepare trip info for better formatting
                            trip_info = {
                                "is_roundtrip": booking_info.trip.is_roundtrip(),
                                "departure_date": departure_date,
                                "return_date": return_date,
                                "departure_city": departure_city,
                                "arrival_city": destination_city
                            }
                            
                            flight_options = self.flight_api.format_flight_options(flight_results, trip_info)
                            booking_response = flight_options
                            self.logger.info(f"Found {len(flight_results)} flights, stored top 3 for selection")
                        else:
                            booking_response = "I couldn't find any flights for that route. Would you like to try different cities or dates?"
                            self.logger.warning("No flights found in search results")
                            
                    except Exception as e:
                        self.logger.error(f"Flight search error: {e}")
                        # Provide mock fallback data and store mock flights
                        self._store_mock_flights()
                        booking_response = self._get_mock_flight_options(departure_city, destination_city, departure_date)
                else:
                    # Flight API not available - use mock data
                    self.logger.warning("Flight API not available, using mock data")
                    self._store_mock_flights()
                    booking_response = self._get_mock_flight_options(departure_city, destination_city, departure_date)
            elif self.booking_flow.context.get('available_flights'):
                # We have flights but user gave a generic response like "ok" - present the available flights
                user_lower = user_input.lower().strip()
                positive_responses = ['ok', 'okay', 'yes', 'sure', 'sounds good', 'go ahead', 'please', 'alright']
                if any(resp in user_lower for resp in positive_responses):
                    available_flights = self.booking_flow.context.get('available_flights')
                    if available_flights and len(available_flights) > 0:
                        # Format and present the cached flights
                        trip_info = {
                            "is_roundtrip": booking_info.trip.is_roundtrip(),
                            "departure_date": departure_date,
                            "return_date": return_date,
                            "departure_city": departure_city,
                            "arrival_city": destination_city
                        }
                        
                        if self.flight_api:
                            booking_response = self.flight_api.format_flight_options(available_flights, trip_info)
                        else:
                            # Use mock format if no API
                            booking_response = self._get_mock_flight_options(departure_city, destination_city, departure_date)
                        
                        self.logger.info("Presented cached flights to user")
            else:
                # Missing city information
                self.logger.error(f"Missing cities - Departure: {departure_city}, Destination: {destination_city}")
                booking_response = "I need both departure and destination cities to search for flights. " + booking_response
        
        # Build comprehensive conversation context for LLM
        conversation_context = ""
        if len(self.conversation_history) > 2:  # Include recent history
            recent_history = self.conversation_history[-6:]  # Last 3 exchanges for better context
            conversation_context = "\n\nRecent conversation:\n"
            for i, msg in enumerate(recent_history):
                role = "Customer" if msg["role"] == "user" else "Alex"
                conversation_context += f"{role}: {msg['content']}\n"
        
        # Add comprehensive booking information context
        booking_info = self.booking_flow.booking_info
        booking_context = self._build_booking_context(booking_info)
        if booking_context:
            conversation_context += f"\n\nCurrent booking information:\n{booking_context}"
        
        # Check if user is repeating information already collected
        repeated_info = self._detect_repeated_information(user_input, booking_info)
        
        # Use LLM to make response more natural with enhanced context
        # Special handling for presenting flight options
        if self.booking_flow.state == BookingState.PRESENTING_OPTIONS and "Option" in booking_response:
            # Get trip type context
            is_roundtrip = booking_info.trip.is_roundtrip()
            trip_type_text = "round trip" if is_roundtrip else "one-way"
            
            system_prompt = f"""You are Alex, a friendly United Airlines booking assistant who sounds like a real person.
            
IMPORTANT: Present the flight options EXACTLY as provided below. Do not add extra options or modify the details.

CRITICAL: This response will be spoken aloud via text-to-speech. DO NOT use any markdown formatting (**, *, _, #, etc.) or special characters that would sound awkward when spoken. Respond in plain text only.

Flight information:
{booking_response}

CONTEXT: This is a {trip_type_text} trip booking.{conversation_context}

Your response should:
1. Start with a natural, enthusiastic transition like "Great! I found some {trip_type_text} flights for you" or "Alright, let me show you what I found for your {trip_type_text} trip"
2. Present ONLY the options shown above with ALL their details in a conversational way
3. End with a friendly question like "Which one catches your eye?" or "What do you think?"

Speak like a friendly human agent, not a computer. Use natural transitions, but include ALL flight details. Be enthusiastic about helping!"""
        else:
            # Regular prompt for other states
            repeated_context = ""
            if repeated_info:
                repeated_context = f"\n\nIMPORTANT: The customer just repeated information they already provided: {repeated_info}. Acknowledge this politely with phrases like 'As you mentioned', 'Right, you said', or 'Yes, I have that'. Don't ask for the same information again."
            
            system_prompt = f"""You are Alex, a friendly United Airlines booking assistant who sounds like a real person, not a robot.

CRITICAL: This response will be spoken aloud via text-to-speech. DO NOT use any markdown formatting (**, *, _, #, etc.) or special characters that would sound awkward when spoken. Respond in plain text only.
            
Current booking state: {state_info['state']}{conversation_context}
Your response should be based on: {booking_response}{repeated_context}

Be conversational and human-like:
- Use natural transitions like "Alright", "Great!", "Perfect!", "Let me help you with that"
- Show enthusiasm and personality - you enjoy helping people travel
- Vary your language - don't always say the same phrases
- Sound like you're having a real conversation, not reading a script
- Keep it friendly but professional
- Keep responses under 3 sentences for voice interaction
- If the customer repeats information you already have, acknowledge it warmly

You're not just an assistant - you're a helpful human who loves making travel easy!"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # Get LLM response from Groq (fast!)
        response = self.groq_client.chat(
            messages=messages,
            model=settings.groq.model,
            temperature=settings.groq.temperature
        )
        
        response_text = response['message']['content']
        
        # Add assistant response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep conversation history manageable (last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response_text
    
    def _build_booking_context(self, booking_info) -> str:
        """Build a comprehensive context string of current booking information"""
        context_parts = []
        
        # Customer information
        if booking_info.customer.first_name:
            name = booking_info.customer.get_full_name() or booking_info.customer.first_name.value
            context_parts.append(f"Customer: {name}")
        
        # Trip information
        if booking_info.trip.departure_city:
            context_parts.append(f"From: {booking_info.trip.departure_city.value}")
        
        if booking_info.trip.arrival_city:
            context_parts.append(f"To: {booking_info.trip.arrival_city.value}")
        
        if booking_info.trip.departure_date:
            context_parts.append(f"Departure: {booking_info.trip.departure_date.value}")
        
        if booking_info.trip.return_date:
            context_parts.append(f"Return: {booking_info.trip.return_date.value}")
        
        if booking_info.trip.trip_type:
            trip_type = "round trip" if booking_info.trip.is_roundtrip() else "one-way"
            context_parts.append(f"Trip type: {trip_type}")
        
        return "; ".join(context_parts)
    
    def _detect_repeated_information(self, user_input: str, booking_info) -> str:
        """Detect if user is repeating information already collected"""
        user_lower = user_input.lower()
        repeated = []
        
        # Check for repeated return date
        if booking_info.trip.return_date and booking_info.trip.return_date.value:
            stored_date = booking_info.trip.return_date.value.lower()
            # Check various date formats that might match
            if ("august 15" in user_lower and "august 15" in stored_date) or \
               ("15th" in user_lower and "15" in stored_date) or \
               ("august" in user_lower and "august" in stored_date and "15" in user_lower):
                repeated.append(f"return date ({booking_info.trip.return_date.value})")
        
        # Check for repeated departure date
        if booking_info.trip.departure_date and booking_info.trip.departure_date.value:
            stored_date = booking_info.trip.departure_date.value.lower()
            if stored_date in user_lower or any(word in stored_date for word in user_lower.split() if len(word) > 3):
                repeated.append(f"departure date ({booking_info.trip.departure_date.value})")
        
        # Check for repeated cities
        if booking_info.trip.departure_city and booking_info.trip.departure_city.value:
            stored_city = booking_info.trip.departure_city.value.lower()
            if stored_city in user_lower or any(word in stored_city.split() for word in user_lower.split()):
                repeated.append(f"departure city ({booking_info.trip.departure_city.value})")
        
        if booking_info.trip.arrival_city and booking_info.trip.arrival_city.value:
            stored_city = booking_info.trip.arrival_city.value.lower()
            if stored_city in user_lower or any(word in stored_city.split() for word in user_lower.split()):
                repeated.append(f"destination ({booking_info.trip.arrival_city.value})")
        
        # Check for repeated trip type
        if booking_info.trip.trip_type and booking_info.trip.trip_type.value:
            trip_type = booking_info.trip.trip_type.value.lower()
            if (trip_type == "roundtrip" and any(phrase in user_lower for phrase in ["round trip", "roundtrip", "return"])) or \
               (trip_type == "oneway" and any(phrase in user_lower for phrase in ["one way", "one-way", "oneway"])):
                repeated.append("trip type")
        
        return "; ".join(repeated) if repeated else None
    
    def speak_response(self, text):
        """Convert text to speech"""
        print("Speaking...")
        
        try:
            # Clean markdown formatting before TTS
            clean_text = self._clean_markdown_for_voice(text)
            
            # Generate audio using the correct API method
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=clean_text,
                voice_id=self.tts_voice_id,
                model_id=settings.elevenlabs.model
            )
            
            # Play the audio
            elevenlabs_play(audio)
            
            print("✓ Response delivered")
            
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def run_booking_conversation(self):
        """Run a complete booking conversation"""
        print("\n" + "="*50)
        print("BOOKING CONVERSATION")
        print("="*50)
        
        # Initial greeting
        greeting = "Hi there! Thanks for calling United Airlines. I'm Alex, and I'm here to help you find the perfect flight. What trip are you planning today?"
        print(f"\nAlex: {greeting}")
        self.speak_response(greeting)
        
        # Reset booking flow and conversation history
        self.booking_flow = BookingFlow()
        self.conversation_history = []
        
        # Special handling for the first user input to detect trip information at greeting
        first_response = True
        
        while self.booking_flow.state != BookingState.BOOKING_COMPLETE:
            # Record user input
            audio_data = self.record_audio()
            user_input = self.transcribe_audio(audio_data)
            
            if not user_input or user_input.strip() == "":
                self.speak_response("Sorry, I didn't quite catch that. Could you say that again for me?")
                continue
            
            print(f"\nYou: {user_input}")
            
            # Process all responses through intent-based system
            response = self.get_response(user_input)
            
            # Mark first response as processed
            if first_response:
                first_response = False
            
            print(f"Alex: {response}")
            
            # Speak response
            self.speak_response(response)
            
            # Check for exit commands
            if any(word in user_input.lower() for word in ["goodbye", "bye", "cancel", "exit"]):
                farewell = "Thanks so much for calling United! Have an amazing day and safe travels!"
                print(f"\nAlex: {farewell}")
                self.speak_response(farewell)
                break
            
            # Brief pause
            time.sleep(0.5)
        
        # Show final booking info
        if self.booking_flow.state == BookingState.BOOKING_COMPLETE:
            print("\nBooking Complete!")
            print(json.dumps(self.booking_flow.booking_info.to_dict(), indent=2))
    
    def demo_booking(self):
        """Demo booking showcasing intent-based system with enhanced capabilities"""
        print("\n" + "="*50)
        print("DEMO BOOKING - Intent-Based System")
        print("="*50)
        
        # Enhanced demo inputs showing various capabilities including greeting with trip type
        demo_inputs = [
            "Round trip",  # Trip type at greeting - should avoid double greeting
            "My name is Sarah Johnson",
            "I'm flying from San Francisco",
            "Actually, let me correct that - I'm flying from SFO",  # Correction intent
            "I want to go to New York",
            "Next Friday please",
            "Yes, I need a return flight on Sunday",
            "What's the weather like in New York?",  # Question intent
            "I'll take the first option",
            "Yes, please book it"
        ]
        
        # Reset booking flow and conversation history
        self.booking_flow = BookingFlow()
        self.conversation_history = []
        
        print("Running enhanced demo booking flow with intent recognition...")
        print("This demo showcases greeting with trip type, corrections, questions, and natural conversation.")
        input("Press Enter to start...")
        
        # Simulate initial greeting
        greeting = "Hi there! Thanks for calling United Airlines. I'm Alex, and I'm here to help you find the perfect flight. What trip are you planning today?"
        print(f"\n--- Initial Greeting ---")
        print(f"🤖 Alex: {greeting}")
        self.speak_response(greeting)
        time.sleep(1)
        
        first_response = True
        for i, user_input in enumerate(demo_inputs, 1):
            print(f"\n--- Step {i} ---")
            print(f"👤 You: {user_input}")
            
            # Show intent recognition in demo
            try:
                intent_result = self.booking_flow.intent_recognizer.recognize_intent(
                    user_input, 
                    self.booking_flow.state.value, 
                    self.booking_flow.booking_info.to_basic_booking_info()
                )
                print(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
                if intent_result.entities:
                    print(f"Entities: {intent_result.entities}")
            except Exception as e:
                print(f"Intent recognition error: {e}")
            
            # Apply the same special handling for first response as in run_booking_conversation
            if first_response:
                first_response = False
                user_lower = user_input.lower()
                trip_type_mentioned = any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip', 'one way', 'one-way', 'oneway'])
                
                if trip_type_mentioned:
                    # User provided trip type at greeting - acknowledge it and ask for name
                    if any(phrase in user_lower for phrase in ['round trip', 'roundtrip', 'round-trip']):
                        self.booking_flow.booking_info.update_trip_info("trip_type", "roundtrip", confidence=1.0, source="greeting")
                        response = "Perfect! Round trip it is. What's your name?"
                    else:
                        self.booking_flow.booking_info.update_trip_info("trip_type", "oneway", confidence=1.0, source="greeting")
                        response = "Got it! One-way trip. What's your name?"
                    
                    self.booking_flow.state = BookingState.COLLECTING_NAME
                    print(f"ℹ️  Special handling: Trip type detected at greeting, skipping double greeting")
                else:
                    response = self.get_response(user_input)
            else:
                response = self.get_response(user_input)
                
            print(f"🤖 Alex: {response}")
            print(f"📊 State: {self.booking_flow.state.value}")
            
            self.speak_response(response)
            time.sleep(2)
        
        print("\nEnhanced Demo Complete!")
        print("\nFinal booking details:")
        print(json.dumps(self.booking_flow.booking_info.to_dict(), indent=2))
        print(f"\nConversation length: {len(self.conversation_history)} messages")
        print(f"Final state: {self.booking_flow.state.value}")


def main():
    """Main function"""
    print("United Airlines Voice Booking Agent")
    print("="*50)
    
    # Check prerequisites
    if not os.getenv('ELEVENLABS_API_KEY'):
        print("Missing ELEVENLABS_API_KEY in .env")
        return
    
    try:
        agent = UnitedVoiceAgent()
        
        while True:
            print("\n" + "="*50)
            print("MAIN MENU")
            print("="*50)
            print("1. Start booking conversation")
            print("2. Demo booking (no mic needed)")
            print("3. Test booking flow")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                agent.run_booking_conversation()
            elif choice == "2":
                agent.demo_booking()
            elif choice == "3":
                # Test intent-based booking flow directly
                from src.core.booking_flow import BookingFlow
                flow = BookingFlow()
                print("\nTesting intent-based booking flow (type 'exit' to quit)...")
                print("This will show intent recognition and confidence scores.")
                while True:
                    user_input = input("\nYou: ")
                    if user_input.lower() == 'exit':
                        break
                    
                    # Show intent recognition
                    try:
                        intent_result = flow.intent_recognizer.recognize_intent(
                            user_input, 
                            flow.state.value, 
                            flow.booking_info.to_basic_booking_info()
                        )
                        print(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
                        if intent_result.entities:
                            print(f"Entities: {intent_result.entities}")
                    except Exception as e:
                        print(f"Intent recognition error: {e}")
                    
                    response = flow.process_input_with_intent(user_input)
                    print(f"Alex: {response}")
                    print(f"[State: {flow.state.value}]")
            elif choice == "4":
                print("\nThank you for using United Airlines!")
                break
            else:
                print("Invalid option")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()