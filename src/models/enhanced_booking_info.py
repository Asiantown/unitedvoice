"""
Enhanced Booking Information Model

Advanced booking data structure with confidence tracking, conversation history,
and comprehensive field validation. Supports complex booking scenarios with
multiple confidence levels and data source attribution.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import json


@dataclass
class ConfidenceScore:
    """
    Represents a value with metadata about its reliability and source.
    
    This class tracks not only the data value but also confidence metrics
    and provenance information for better decision making.
    
    Attributes:
        value: The actual data value
        confidence: Confidence score from 0.0 to 1.0
        source: Data source identifier
        timestamp: When this value was recorded
    """
    value: Any
    confidence: float = 0.0  # Range: 0.0 (no confidence) to 1.0 (full confidence)
    source: str = "user_input"  # Sources: user_input, inference, validation, api, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate confidence score is within valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class CustomerDetails:
    """
    Customer information with confidence-based field tracking.
    
    Maintains customer data with associated confidence scores for each field,
    enabling intelligent handling of uncertain or partial information.
    
    Attributes:
        first_name: Customer's first name with confidence
        last_name: Customer's last name with confidence
        email: Customer's email address with confidence
        phone: Customer's phone number with confidence
        frequent_flyer_number: Loyalty program number with confidence
    """
    first_name: Optional[ConfidenceScore] = None
    last_name: Optional[ConfidenceScore] = None
    email: Optional[ConfidenceScore] = None
    phone: Optional[ConfidenceScore] = None
    frequent_flyer_number: Optional[ConfidenceScore] = None
    
    def get_full_name(self) -> Optional[str]:
        """
        Get full name if both first and last name are available.
        
        Returns:
            Formatted full name string or None if incomplete
        """
        if self.first_name and self.last_name:
            return f"{self.first_name.value} {self.last_name.value}"
        return None
    
    def get_name_confidence(self) -> float:
        """
        Get the minimum confidence between first and last name.
        
        Returns:
            Lowest confidence score between name components (0.0-1.0)
        """
        if self.first_name and self.last_name:
            return min(self.first_name.confidence, self.last_name.confidence)
        elif self.first_name:
            return self.first_name.confidence * 0.5  # Partial name penalty
        elif self.last_name:
            return self.last_name.confidence * 0.5  # Partial name penalty
        return 0.0
    
    def has_complete_name(self, min_confidence: float = 0.7) -> bool:
        """
        Check if customer has a complete name with sufficient confidence.
        
        Args:
            min_confidence: Minimum required confidence level
            
        Returns:
            True if both names exist with sufficient confidence
        """
        return (self.first_name is not None and 
                self.last_name is not None and
                self.get_name_confidence() >= min_confidence)


@dataclass
class FlightDetails:
    """Detailed flight information with confidence tracking."""
    flight_number: Optional[ConfidenceScore] = None
    airline: Optional[ConfidenceScore] = None
    departure_time: Optional[ConfidenceScore] = None
    arrival_time: Optional[ConfidenceScore] = None
    duration: Optional[ConfidenceScore] = None
    flight_type: Optional[ConfidenceScore] = None  # nonstop, 1 stop, etc.
    price: Optional[ConfidenceScore] = None
    aircraft_type: Optional[ConfidenceScore] = None
    departure_airport: Optional[ConfidenceScore] = None
    arrival_airport: Optional[ConfidenceScore] = None


@dataclass
class TripDetails:
    """Trip information with confidence tracking."""
    departure_city: Optional[ConfidenceScore] = None
    arrival_city: Optional[ConfidenceScore] = None
    departure_date: Optional[ConfidenceScore] = None
    return_date: Optional[ConfidenceScore] = None
    departure_time: Optional[ConfidenceScore] = None
    return_time: Optional[ConfidenceScore] = None
    passenger_count: Optional[ConfidenceScore] = None
    cabin_class: Optional[ConfidenceScore] = None
    trip_type: Optional[ConfidenceScore] = None  # roundtrip, oneway, multicity
    
    # Selected flight details
    outbound_flight: Optional[FlightDetails] = None
    return_flight: Optional[FlightDetails] = None
    confirmation_number: Optional[ConfidenceScore] = None
    
    def get_city_pair_confidence(self) -> float:
        """Get the minimum confidence between departure and arrival cities."""
        if self.departure_city and self.arrival_city:
            return min(self.departure_city.confidence, self.arrival_city.confidence)
        return 0.0
    
    def is_roundtrip(self) -> bool:
        """Check if this is a roundtrip booking."""
        return (self.trip_type and 
                self.trip_type.value and 
                self.trip_type.value.lower() == "roundtrip")


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    timestamp: datetime
    user_input: str
    agent_response: str
    extracted_info: Dict[str, Any] = field(default_factory=dict)
    confidence_updates: Dict[str, float] = field(default_factory=dict)


@dataclass
class EnhancedBookingInfo:
    """Enhanced booking information with confidence tracking and conversation history."""
    
    customer: CustomerDetails = field(default_factory=CustomerDetails)
    trip: TripDetails = field(default_factory=TripDetails)
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_conversation_turn(self, user_input: str, agent_response: str, 
                            extracted_info: Optional[Dict[str, Any]] = None,
                            confidence_updates: Optional[Dict[str, float]] = None) -> None:
        """Add a new conversation turn to the history."""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            agent_response=agent_response,
            extracted_info=extracted_info or {},
            confidence_updates=confidence_updates or {}
        )
        self.conversation_history.append(turn)
        self.last_updated = datetime.now()
    
    def update_customer_info(self, field: str, value: Any, confidence: float = 1.0, 
                           source: str = "user_input") -> None:
        """Update customer information with confidence tracking."""
        confidence_score = ConfidenceScore(
            value=value,
            confidence=confidence,
            source=source,
            timestamp=datetime.now()
        )
        
        if hasattr(self.customer, field):
            setattr(self.customer, field, confidence_score)
            self.last_updated = datetime.now()
    
    def update_trip_info(self, field: str, value: Any, confidence: float = 1.0,
                        source: str = "user_input") -> None:
        """Update trip information with confidence tracking."""
        confidence_score = ConfidenceScore(
            value=value,
            confidence=confidence,
            source=source,
            timestamp=datetime.now()
        )
        
        if hasattr(self.trip, field):
            setattr(self.trip, field, confidence_score)
            self.last_updated = datetime.now()
    
    def store_selected_flight(self, flight_data: Dict[str, Any], is_return: bool = False,
                            confidence: float = 1.0, source: str = "flight_selection") -> None:
        """Store selected flight details in the booking info."""
        flight_details = FlightDetails()
        
        # Map flight data to flight details with confidence tracking
        if "airline" in flight_data:
            flight_details.airline = ConfidenceScore(flight_data["airline"], confidence, source)
        if "flight_number" in flight_data:
            flight_details.flight_number = ConfidenceScore(flight_data["flight_number"], confidence, source)
        if "departure_time" in flight_data:
            flight_details.departure_time = ConfidenceScore(flight_data["departure_time"], confidence, source)
        if "arrival_time" in flight_data:
            flight_details.arrival_time = ConfidenceScore(flight_data["arrival_time"], confidence, source)
        if "duration" in flight_data:
            flight_details.duration = ConfidenceScore(flight_data["duration"], confidence, source)
        if "type" in flight_data:
            flight_details.flight_type = ConfidenceScore(flight_data["type"], confidence, source)
        if "price" in flight_data:
            flight_details.price = ConfidenceScore(flight_data["price"], confidence, source)
        if "aircraft" in flight_data:
            flight_details.aircraft_type = ConfidenceScore(flight_data["aircraft"], confidence, source)
        if "departure_airport" in flight_data:
            flight_details.departure_airport = ConfidenceScore(flight_data["departure_airport"], confidence, source)
        if "arrival_airport" in flight_data:
            flight_details.arrival_airport = ConfidenceScore(flight_data["arrival_airport"], confidence, source)
        
        # Store as outbound or return flight
        if is_return:
            self.trip.return_flight = flight_details
        else:
            self.trip.outbound_flight = flight_details
        
        self.last_updated = datetime.now()
    
    def get_selected_outbound_flight(self) -> Optional[Dict[str, Any]]:
        """Get selected outbound flight as dictionary."""
        if not self.trip.outbound_flight:
            return None
        
        flight = {}
        if self.trip.outbound_flight.airline:
            flight["airline"] = self.trip.outbound_flight.airline.value
        if self.trip.outbound_flight.flight_number:
            flight["flight_number"] = self.trip.outbound_flight.flight_number.value
        if self.trip.outbound_flight.departure_time:
            flight["departure_time"] = self.trip.outbound_flight.departure_time.value
        if self.trip.outbound_flight.arrival_time:
            flight["arrival_time"] = self.trip.outbound_flight.arrival_time.value
        if self.trip.outbound_flight.duration:
            flight["duration"] = self.trip.outbound_flight.duration.value
        if self.trip.outbound_flight.flight_type:
            flight["type"] = self.trip.outbound_flight.flight_type.value
        if self.trip.outbound_flight.price:
            flight["price"] = self.trip.outbound_flight.price.value
        
        return flight if flight else None
    
    def get_selected_return_flight(self) -> Optional[Dict[str, Any]]:
        """Get selected return flight as dictionary."""
        if not self.trip.return_flight:
            return None
        
        flight = {}
        if self.trip.return_flight.airline:
            flight["airline"] = self.trip.return_flight.airline.value
        if self.trip.return_flight.flight_number:
            flight["flight_number"] = self.trip.return_flight.flight_number.value
        if self.trip.return_flight.departure_time:
            flight["departure_time"] = self.trip.return_flight.departure_time.value
        if self.trip.return_flight.arrival_time:
            flight["arrival_time"] = self.trip.return_flight.arrival_time.value
        if self.trip.return_flight.duration:
            flight["duration"] = self.trip.return_flight.duration.value
        if self.trip.return_flight.flight_type:
            flight["type"] = self.trip.return_flight.flight_type.value
        if self.trip.return_flight.price:
            flight["price"] = self.trip.return_flight.price.value
        
        return flight if flight else None
    
    def get_missing_required_fields(self) -> List[str]:
        """Get list of required fields that are still missing or have low confidence."""
        missing = []
        
        # Check customer required fields
        if not self.customer.first_name or self.customer.first_name.confidence < 0.7:
            missing.append("customer_first_name")
        if not self.customer.last_name or self.customer.last_name.confidence < 0.7:
            missing.append("customer_last_name")
        
        # Check trip required fields
        if not self.trip.departure_city or self.trip.departure_city.confidence < 0.7:
            missing.append("departure_city")
        if not self.trip.arrival_city or self.trip.arrival_city.confidence < 0.7:
            missing.append("arrival_city")
        if not self.trip.departure_date or self.trip.departure_date.confidence < 0.7:
            missing.append("departure_date")
        
        return missing
    
    def get_completion_percentage(self) -> float:
        """Calculate the completion percentage of the booking information."""
        total_fields = 5  # first_name, last_name, departure_city, arrival_city, departure_date
        completed_fields = 0
        
        # Check customer fields
        if self.customer.first_name and self.customer.first_name.confidence >= 0.7:
            completed_fields += 1
        if self.customer.last_name and self.customer.last_name.confidence >= 0.7:
            completed_fields += 1
            
        # Check trip fields
        if self.trip.departure_city and self.trip.departure_city.confidence >= 0.7:
            completed_fields += 1
        if self.trip.arrival_city and self.trip.arrival_city.confidence >= 0.7:
            completed_fields += 1
        if self.trip.departure_date and self.trip.departure_date.confidence >= 0.7:
            completed_fields += 1
            
        return completed_fields / total_fields
    
    def to_basic_booking_info(self) -> Dict[str, Any]:
        """Convert to basic booking info format for compatibility."""
        result = {}
        
        # Customer info
        if self.customer.first_name:
            result["first_name"] = self.customer.first_name.value
        if self.customer.last_name:
            result["last_name"] = self.customer.last_name.value
        if self.customer.email:
            result["email"] = self.customer.email.value
        if self.customer.phone:
            result["phone"] = self.customer.phone.value
        if self.customer.frequent_flyer_number:
            result["frequent_flyer_number"] = self.customer.frequent_flyer_number.value
            
        # Trip info
        if self.trip.departure_city:
            result["departure_city"] = self.trip.departure_city.value
        if self.trip.arrival_city:
            result["arrival_city"] = self.trip.arrival_city.value
        if self.trip.departure_date:
            result["departure_date"] = self.trip.departure_date.value
        if self.trip.return_date:
            result["return_date"] = self.trip.return_date.value
        if self.trip.departure_time:
            result["departure_time"] = self.trip.departure_time.value
        if self.trip.return_time:
            result["return_time"] = self.trip.return_time.value
        if self.trip.passenger_count:
            result["passenger_count"] = self.trip.passenger_count.value
        if self.trip.cabin_class:
            result["cabin_class"] = self.trip.cabin_class.value
        if self.trip.trip_type:
            result["trip_type"] = self.trip.trip_type.value
        if self.trip.confirmation_number:
            result["confirmation_number"] = self.trip.confirmation_number.value
            
        # Add selected flight details
        if self.trip.outbound_flight:
            outbound = {}
            if self.trip.outbound_flight.airline:
                outbound["airline"] = self.trip.outbound_flight.airline.value
            if self.trip.outbound_flight.flight_number:
                outbound["flight_number"] = self.trip.outbound_flight.flight_number.value
            if self.trip.outbound_flight.departure_time:
                outbound["departure_time"] = self.trip.outbound_flight.departure_time.value
            if self.trip.outbound_flight.arrival_time:
                outbound["arrival_time"] = self.trip.outbound_flight.arrival_time.value
            if self.trip.outbound_flight.duration:
                outbound["duration"] = self.trip.outbound_flight.duration.value
            if self.trip.outbound_flight.flight_type:
                outbound["type"] = self.trip.outbound_flight.flight_type.value
            if self.trip.outbound_flight.price:
                outbound["price"] = self.trip.outbound_flight.price.value
            if outbound:
                result["outbound_flight"] = outbound
                
        if self.trip.return_flight:
            return_flight = {}
            if self.trip.return_flight.airline:
                return_flight["airline"] = self.trip.return_flight.airline.value
            if self.trip.return_flight.flight_number:
                return_flight["flight_number"] = self.trip.return_flight.flight_number.value
            if self.trip.return_flight.departure_time:
                return_flight["departure_time"] = self.trip.return_flight.departure_time.value
            if self.trip.return_flight.arrival_time:
                return_flight["arrival_time"] = self.trip.return_flight.arrival_time.value
            if self.trip.return_flight.duration:
                return_flight["duration"] = self.trip.return_flight.duration.value
            if self.trip.return_flight.flight_type:
                return_flight["type"] = self.trip.return_flight.flight_type.value
            if self.trip.return_flight.price:
                return_flight["price"] = self.trip.return_flight.price.value
            if return_flight:
                result["return_flight"] = return_flight
                
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format including confidence scores."""
        def confidence_score_to_dict(cs: Optional[ConfidenceScore]) -> Optional[Dict[str, Any]]:
            if cs is None:
                return None
            return {
                "value": cs.value,
                "confidence": cs.confidence,
                "source": cs.source,
                "timestamp": cs.timestamp.isoformat()
            }
        
        def flight_details_to_dict(flight: Optional[FlightDetails]) -> Optional[Dict[str, Any]]:
            if flight is None:
                return None
            return {
                "flight_number": confidence_score_to_dict(flight.flight_number),
                "airline": confidence_score_to_dict(flight.airline),
                "departure_time": confidence_score_to_dict(flight.departure_time),
                "arrival_time": confidence_score_to_dict(flight.arrival_time),
                "duration": confidence_score_to_dict(flight.duration),
                "flight_type": confidence_score_to_dict(flight.flight_type),
                "price": confidence_score_to_dict(flight.price),
                "aircraft_type": confidence_score_to_dict(flight.aircraft_type),
                "departure_airport": confidence_score_to_dict(flight.departure_airport),
                "arrival_airport": confidence_score_to_dict(flight.arrival_airport),
            }
        
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "customer": {
                "first_name": confidence_score_to_dict(self.customer.first_name),
                "last_name": confidence_score_to_dict(self.customer.last_name),
                "email": confidence_score_to_dict(self.customer.email),
                "phone": confidence_score_to_dict(self.customer.phone),
                "frequent_flyer_number": confidence_score_to_dict(self.customer.frequent_flyer_number),
            },
            "trip": {
                "departure_city": confidence_score_to_dict(self.trip.departure_city),
                "arrival_city": confidence_score_to_dict(self.trip.arrival_city),
                "departure_date": confidence_score_to_dict(self.trip.departure_date),
                "return_date": confidence_score_to_dict(self.trip.return_date),
                "departure_time": confidence_score_to_dict(self.trip.departure_time),
                "return_time": confidence_score_to_dict(self.trip.return_time),
                "passenger_count": confidence_score_to_dict(self.trip.passenger_count),
                "cabin_class": confidence_score_to_dict(self.trip.cabin_class),
                "trip_type": confidence_score_to_dict(self.trip.trip_type),
                "confirmation_number": confidence_score_to_dict(self.trip.confirmation_number),
                "outbound_flight": flight_details_to_dict(self.trip.outbound_flight),
                "return_flight": flight_details_to_dict(self.trip.return_flight),
            },
            "conversation_history": [
                {
                    "timestamp": turn.timestamp.isoformat(),
                    "user_input": turn.user_input,
                    "agent_response": turn.agent_response,
                    "extracted_info": turn.extracted_info,
                    "confidence_updates": turn.confidence_updates
                }
                for turn in self.conversation_history
            ]
        }
    
    def to_json(self) -> str:
        """
        Convert to JSON string representation.
        
        Returns:
            Formatted JSON string with all booking information
        """
        return json.dumps(self.to_dict(), indent=2, default=str)  # Handle datetime serialization