#!/usr/bin/env python3
"""
Mock Flight Database
Simulates United Airlines flight data for demo purposes
"""

from datetime import datetime, timedelta
import random
from typing import List, Dict, Optional


class FlightDatabase:
    """Mock database of United Airlines flights"""
    
    def __init__(self):
        # Airport codes and cities
        self.airports = {
            "san francisco": "SFO",
            "new york": ["JFK", "EWR", "LGA"],
            "los angeles": "LAX",
            "chicago": "ORD",
            "boston": "BOS",
            "miami": "MIA",
            "seattle": "SEA",
            "denver": "DEN",
            "dallas": "DFW",
            "atlanta": "ATL",
            "washington": "DCA",
            "las vegas": "LAS",
            "phoenix": "PHX",
            "houston": "IAH"
        }
        
        # Flight templates
        self.flight_times = [
            {"depart": "6:00 AM", "duration": 5.5, "type": "nonstop"},
            {"depart": "7:15 AM", "duration": 5.5, "type": "nonstop"},
            {"depart": "9:30 AM", "duration": 6.5, "type": "1 stop"},
            {"depart": "12:30 PM", "duration": 5.5, "type": "nonstop"},
            {"depart": "2:45 PM", "duration": 7.0, "type": "1 stop"},
            {"depart": "6:45 PM", "duration": 5.5, "type": "nonstop"},
            {"depart": "9:00 PM", "duration": 6.0, "type": "red-eye"}
        ]
    
    def search_flights(self, departure: str, destination: str, date: str, 
                      return_date: Optional[str] = None) -> List[Dict]:
        """Search for available flights"""
        
        # Normalize city names
        departure = departure.lower()
        destination = destination.lower()
        
        # Get airport codes
        dep_code = self._get_airport_code(departure)
        dest_code = self._get_airport_code(destination)
        
        if not dep_code or not dest_code:
            return []
        
        # Generate flight options
        flights = []
        base_price = self._calculate_base_price(departure, destination)
        
        # Create 3-5 flight options
        num_options = random.randint(3, 5)
        available_times = random.sample(self.flight_times, num_options)
        
        for i, flight_template in enumerate(sorted(available_times, key=lambda x: x["depart"])):
            # Calculate arrival time
            depart_time = datetime.strptime(flight_template["depart"], "%I:%M %p")
            arrive_time = depart_time + timedelta(hours=flight_template["duration"])
            
            # Price variation
            price_modifier = random.uniform(0.8, 1.3)
            if flight_template["type"] == "red-eye":
                price_modifier *= 0.9
            elif flight_template["type"] == "1 stop":
                price_modifier *= 0.95
            
            price = int(base_price * price_modifier)
            
            flight = {
                "flight_number": f"UA{random.randint(100, 999)}",
                "departure_airport": dep_code,
                "arrival_airport": dest_code,
                "departure_time": flight_template["depart"],
                "arrival_time": arrive_time.strftime("%I:%M %p"),
                "duration": self._format_duration_voice_friendly(flight_template['duration']),
                "type": flight_template["type"],
                "price": price,
                "seats_available": random.randint(3, 25)
            }
            
            flights.append(flight)
        
        # If round trip, generate return flights
        if return_date:
            return_flights = []
            for flight in flights:
                return_flight = {
                    "flight_number": f"UA{random.randint(100, 999)}",
                    "departure_airport": dest_code,
                    "arrival_airport": dep_code,
                    "departure_time": flight["departure_time"],
                    "arrival_time": flight["arrival_time"],
                    "duration": flight["duration"],
                    "type": flight["type"],
                    "price": flight["price"],
                    "seats_available": random.randint(3, 25)
                }
                return_flights.append(return_flight)
            
            # Combine outbound and return
            return {
                "outbound": flights,
                "return": return_flights,
                "total_price": sum(f["price"] for f in flights[:1]) + sum(f["price"] for f in return_flights[:1])
            }
        
        return {"outbound": flights, "return": None, "total_price": flights[0]["price"] if flights else 0}
    
    def _get_airport_code(self, city: str) -> Optional[str]:
        """Get airport code for a city"""
        city = city.lower()
        
        if city in self.airports:
            code = self.airports[city]
            # For cities with multiple airports, pick the first one
            if isinstance(code, list):
                return code[0]
            return code
        
        # Try partial matching
        for city_name, code in self.airports.items():
            if city in city_name or city_name in city:
                if isinstance(code, list):
                    return code[0]
                return code
        
        return None
    
    def _calculate_base_price(self, departure: str, destination: str) -> int:
        """Calculate base price based on route"""
        # Simple distance-based pricing
        route_prices = {
            ("san francisco", "new york"): 350,
            ("san francisco", "los angeles"): 120,
            ("san francisco", "chicago"): 280,
            ("new york", "miami"): 250,
            ("chicago", "denver"): 180,
            ("los angeles", "seattle"): 150,
            ("boston", "atlanta"): 200
        }
        
        # Check both directions
        for (city1, city2), price in route_prices.items():
            if (departure in city1 and destination in city2) or \
               (departure in city2 and destination in city1):
                return price
        
        # Default pricing based on assumed distance
        return 300
    
    def _format_duration_voice_friendly(self, duration_hours: float) -> str:
        """Format duration from hours to voice-friendly format"""
        hours = int(duration_hours)
        minutes = int((duration_hours % 1) * 60)
        
        if hours > 0 and minutes > 0:
            hour_text = "hour" if hours == 1 else "hours"
            minute_text = "minute" if minutes == 1 else "minutes"
            return f"{hours} {hour_text} {minutes} {minute_text}"
        elif hours > 0:
            hour_text = "hour" if hours == 1 else "hours"
            return f"{hours} {hour_text}"
        else:
            minute_text = "minute" if minutes == 1 else "minutes"
            return f"{minutes} {minute_text}"
    
    def format_flight_options(self, search_results: Dict) -> str:
        """Format flight search results for voice output"""
        if not search_results or not search_results.get("outbound"):
            return "I couldn't find any flights for that route."
        
        flights = search_results["outbound"][:3]  # Show max 3 options
        is_round_trip = search_results.get("return") is not None
        
        if len(flights) == 1:
            response = f"I found one great {'round trip' if is_round_trip else 'flight'} option for you:\n\n"
        else:
            response = f"I found {len(flights)} great {'round trip' if is_round_trip else 'flight'} options for you. Here are the best {len(flights)}:\n\n"
        
        for i, flight in enumerate(flights, 1):
            response += f"Option {i}: "
            response += f"A United flight departing at {flight['departure_time']}"
            
            # Add flight type description
            if flight["type"] == "nonstop":
                response += ", this is a direct flight"
            elif flight["type"] == "1 stop":
                response += ", with one stop"
            elif flight["type"] == "red-eye":
                response += ", this is a red-eye flight"
            else:
                response += f", with {flight['type']}"
            
            # Add duration in natural language
            response += f" taking {flight['duration']}"
            
            # Add price
            if is_round_trip:
                total = flight["price"] * 2  # Simplified
                response += f", priced at ${total} round trip"
            else:
                response += f", priced at ${flight['price']}"
            
            response += ".\n\n"  # Double newline for voice pauses
        
        response += "Would you like to book one of these flights, or would you like me to look for different options?"
        return response.strip()


# Test the flight database
if __name__ == "__main__":
    db = FlightDatabase()
    
    print("Testing Flight Database\n")
    
    # Test one-way search
    results = db.search_flights("San Francisco", "New York", "December 15")
    print("One-way search results:")
    print(db.format_flight_options(results))
    print()
    
    # Test round-trip search
    results = db.search_flights("Boston", "Miami", "January 10", "January 15")
    print("\nRound-trip search results:")
    print(db.format_flight_options(results))
    print()
    
    # Test invalid route
    results = db.search_flights("InvalidCity", "Unknown", "Tomorrow")
    print("\nInvalid route search:")
    print(db.format_flight_options(results))