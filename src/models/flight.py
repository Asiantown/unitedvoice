#!/usr/bin/env python3
"""
Flight Data Model

Defines the core Flight class for representing flight information from various
sources including APIs, mock data, and user selections. Provides methods for
data conversion, validation, and voice-friendly formatting.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class Flight:
    """
    Represents a single flight with comprehensive information.
    
    This class encapsulates all relevant flight data including scheduling,
    pricing, routing, and booking information. Provides methods for data
    conversion and voice-friendly formatting.
    
    Attributes:
        flight_number: Airline flight identifier (e.g., "UA123")
        airline: Airline name (e.g., "United Airlines")
        departure_airport: IATA departure airport code (e.g., "SFO")
        arrival_airport: IATA arrival airport code (e.g., "JFK")
        departure_city: Departure city name
        arrival_city: Arrival city name
        departure_time: Departure time string
        arrival_time: Arrival time string
        departure_date: Date of departure
        duration: Flight duration (e.g., "3h 45m")
        price: Flight price in USD
        type: Flight type ("nonstop", "1 stop", "2 stops", etc.)
        seats_available: Number of seats available (if known)
        cabin_class: Cabin class ("economy", "business", "first")
        airline_logo: URL to airline logo image
        aircraft: Aircraft type (e.g., "Boeing 777")
        segments: Number of flight segments
        layovers: List of layover information
        booking_token: Token for booking this flight
        carbon_emissions: Environmental impact data
    """
    flight_number: str
    airline: str
    departure_airport: str
    arrival_airport: str
    departure_city: str
    arrival_city: str
    departure_time: str
    arrival_time: str
    departure_date: str
    duration: str
    price: float
    type: str
    
    # Optional attributes with defaults
    seats_available: Optional[int] = None
    cabin_class: str = "economy"
    airline_logo: Optional[str] = None
    aircraft: Optional[str] = None
    segments: int = 1
    layovers: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    booking_token: Optional[str] = None
    carbon_emissions: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate flight data after initialization."""
        self._validate_flight_data()
    
    def _validate_flight_data(self) -> None:
        """
        Validate flight data integrity.
        
        Raises:
            ValueError: If required data is invalid
        """
        # Validate required string fields
        required_fields = [
            ('flight_number', self.flight_number),
            ('airline', self.airline),
            ('departure_airport', self.departure_airport),
            ('arrival_airport', self.arrival_airport),
            ('departure_city', self.departure_city),
            ('arrival_city', self.arrival_city)
        ]
        
        for field_name, field_value in required_fields:
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        
        # Validate price
        if not isinstance(self.price, (int, float)) or self.price < 0:
            raise ValueError("Price must be a non-negative number")
        
        # Validate segments
        if not isinstance(self.segments, int) or self.segments < 1:
            raise ValueError("Segments must be a positive integer")
        
        # Validate seats available if provided
        if self.seats_available is not None:
            if not isinstance(self.seats_available, int) or self.seats_available < 0:
                raise ValueError("Seats available must be a non-negative integer")
        
        # Validate cabin class
        valid_cabin_classes = {"economy", "premium_economy", "business", "first"}
        if self.cabin_class.lower() not in valid_cabin_classes:
            logger.warning(f"Unusual cabin class: {self.cabin_class}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert flight to dictionary representation.
        
        Returns:
            Dictionary containing all flight attributes
        """
        return {
            "flight_number": self.flight_number,
            "airline": self.airline,
            "departure_airport": self.departure_airport,
            "arrival_airport": self.arrival_airport,
            "departure_city": self.departure_city,
            "arrival_city": self.arrival_city,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "departure_date": self.departure_date,
            "duration": self.duration,
            "price": self.price,
            "type": self.type,
            "seats_available": self.seats_available,
            "cabin_class": self.cabin_class,
            "airline_logo": self.airline_logo,
            "aircraft": self.aircraft,
            "segments": self.segments,
            "layovers": self.layovers or [],
            "booking_token": self.booking_token,
            "carbon_emissions": self.carbon_emissions or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Flight":
        """
        Create Flight instance from dictionary data.
        
        Args:
            data: Dictionary containing flight data
            
        Returns:
            Flight instance
            
        Raises:
            ValueError: If required data is missing or invalid
            TypeError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")
        
        # Check for required fields
        required_fields = {
            'flight_number', 'airline', 'departure_airport', 'arrival_airport',
            'departure_city', 'arrival_city', 'departure_time', 'arrival_time',
            'departure_date', 'duration', 'price', 'type'
        }
        
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        try:
            return cls(**data)
        except Exception as e:
            logger.error(f"Error creating Flight from data: {e}")
            raise ValueError(f"Invalid flight data: {e}")
    
    def format_for_voice(self, include_price: bool = True, include_aircraft: bool = False) -> str:
        """
        Format flight information for text-to-speech output.
        
        Args:
            include_price: Whether to include price in output
            include_aircraft: Whether to include aircraft type
            
        Returns:
            Voice-friendly flight description string
        """
        parts = []
        
        # Basic flight info
        parts.append(f"{self.airline} flight {self.flight_number}")
        parts.append(f"departing at {self.departure_time}")
        
        # Flight type and duration
        if self.type == "nonstop":
            parts.append(f"nonstop flight, {self.duration}")
        else:
            parts.append(f"{self.type}, {self.duration}")
        
        # Aircraft type if requested
        if include_aircraft and self.aircraft:
            parts.append(f"on {self.aircraft}")
        
        # Price if requested and available
        if include_price and self.price > 0:
            parts.append(f"for ${self.price:.0f}")
        
        # Seats availability
        if self.seats_available is not None and self.seats_available <= 10:
            parts.append(f"{self.seats_available} seats remaining")
        
        return ", ".join(parts)
    
    def get_route_description(self) -> str:
        """
        Get human-readable route description.
        
        Returns:
            Route description string
        """
        return f"{self.departure_city} ({self.departure_airport}) to {self.arrival_city} ({self.arrival_airport})"
    
    def is_nonstop(self) -> bool:
        """
        Check if this is a nonstop flight.
        
        Returns:
            True if flight is nonstop
        """
        return self.type.lower() == "nonstop" or self.segments == 1
    
    def get_layover_count(self) -> int:
        """
        Get the number of layovers for this flight.
        
        Returns:
            Number of layovers
        """
        if self.is_nonstop():
            return 0
        return max(0, self.segments - 1)
    
    def format_duration_readable(self) -> str:
        """
        Format duration in a more readable way.
        
        Returns:
            Readable duration string
        """
        # Handle various duration formats
        duration = self.duration.lower()
        
        # Convert common formats to more readable versions
        if 'h' in duration and 'm' in duration:
            return duration.replace('h', ' hours').replace('m', ' minutes')
        elif 'h' in duration:
            return duration.replace('h', ' hours')
        elif 'm' in duration:
            return duration.replace('m', ' minutes')
        else:
            return duration
    
    def __str__(self) -> str:
        """String representation of flight."""
        return f"Flight {self.flight_number}: {self.get_route_description()} at {self.departure_time}"
    
    def __repr__(self) -> str:
        """Developer representation of flight."""
        return f"Flight(flight_number='{self.flight_number}', airline='{self.airline}', price={self.price})"