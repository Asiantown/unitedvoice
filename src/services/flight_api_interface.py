#!/usr/bin/env python3
"""
Flight API Interface
Abstract interface for flight search APIs
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FlightSearchParams:
    """Parameters for flight search"""
    departure_city: str
    arrival_city: str
    departure_date: str
    return_date: Optional[str] = None
    trip_type: str = "one_way"  # one_way, round_trip
    passengers: int = 1
    cabin_class: str = "economy"  # economy, premium, business, first
    max_stops: Optional[int] = None
    max_price: Optional[float] = None
    preferred_airlines: Optional[List[str]] = None
    excluded_airlines: Optional[List[str]] = None


class FlightAPIInterface(ABC):
    """Abstract interface for flight search APIs"""
    
    @abstractmethod
    def search_flights(
        self,
        departure_city: str,
        arrival_city: str,
        departure_date: str,
        return_date: Optional[str] = None,
        trip_type: str = "one_way",
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> List[Dict[str, Any]]:
        """
        Search for flights between two cities
        
        Args:
            departure_city: Departure city name
            arrival_city: Arrival city name
            departure_date: Departure date
            return_date: Return date for round trips
            trip_type: Type of trip (one_way, round_trip)
            passengers: Number of passengers
            cabin_class: Cabin class preference
            
        Returns:
            List of flight options
        """
        pass
    
    @abstractmethod
    def format_flight_options(self, flights: List[Dict[str, Any]]) -> str:
        """
        Format flight options for voice output
        
        Args:
            flights: List of flight options
            
        Returns:
            Formatted string for voice output
        """
        pass