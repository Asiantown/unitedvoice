#!/usr/bin/env python3
"""
Flight data model
Represents flight information from various sources
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Flight:
    """Represents a single flight"""
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
    type: str  # nonstop, 1 stop, 2 stops, etc.
    seats_available: Optional[int] = None
    cabin_class: str = "economy"
    airline_logo: Optional[str] = None
    aircraft: Optional[str] = None
    segments: int = 1
    layovers: Optional[List[Dict[str, Any]]] = None
    booking_token: Optional[str] = None
    carbon_emissions: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert flight to dictionary"""
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
            "layovers": self.layovers,
            "booking_token": self.booking_token,
            "carbon_emissions": self.carbon_emissions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Flight":
        """Create flight from dictionary"""
        return cls(**data)
    
    def format_for_voice(self) -> str:
        """Format flight information for voice output"""
        output = f"{self.airline} flight {self.flight_number}, "
        output += f"departing at {self.departure_time}, "
        
        if self.type == "nonstop":
            output += "nonstop flight"
        else:
            output += self.type
        
        output += f" ({self.duration})"
        
        if self.price > 0:
            output += f", ${self.price:.0f}"
        
        return output