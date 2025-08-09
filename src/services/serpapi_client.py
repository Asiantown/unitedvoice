#!/usr/bin/env python3
"""
SerpApi Client for Google Flights API
Handles communication with SerpApi service
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class GoogleFlightsParams:
    """Parameters for Google Flights search"""
    departure_id: str  # Airport code (e.g., "LAX") or multiple ("LAX,BUR")
    arrival_id: str    # Airport code (e.g., "JFK") 
    outbound_date: str # Format: YYYY-MM-DD
    return_date: Optional[str] = None  # For round trips
    currency: str = "USD"
    hl: str = "en"  # Language
    gl: str = "us"  # Country
    type: int = 2   # 1=Round trip, 2=One way, 3=Multi-city
    travel_class: int = 1  # 1=Economy, 2=Premium economy, 3=Business, 4=First
    adults: int = 1
    children: int = 0
    stops: int = 0  # 0=Any, 1=Nonstop only, 2=1 stop or fewer
    max_price: Optional[int] = None
    include_airlines: Optional[List[str]] = None
    exclude_airlines: Optional[List[str]] = None
    bags: int = 0  # Number of carry-on bags


class SerpApiError(Exception):
    """Base exception for SerpApi errors"""
    pass


class RateLimitError(SerpApiError):
    """Raised when API rate limit is exceeded"""
    pass


class InvalidQueryError(SerpApiError):
    """Raised when query parameters are invalid"""
    pass


class NetworkError(SerpApiError):
    """Raised when network request fails"""
    pass


class SerpApiClient:
    """Client for SerpApi Google Flights API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
        self.base_url = "https://serpapi.com/search"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0
        
    async def search_flights(self, params: GoogleFlightsParams) -> Dict[str, Any]:
        """
        Search for flights using Google Flights API
        
        Args:
            params: Flight search parameters
            
        Returns:
            Dict containing flight search results
            
        Raises:
            RateLimitError: API rate limit exceeded
            InvalidQueryError: Invalid search parameters
            NetworkError: Network request failed
        """
        # Build query parameters
        query_params = self._build_query_params(params)
        
        # Perform search with retry logic
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.base_url,
                        params=query_params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        # Check response status
                        if response.status == 429:
                            raise RateLimitError("API rate limit exceeded")
                        elif response.status == 400:
                            error_data = await response.json()
                            raise InvalidQueryError(f"Invalid query: {error_data.get('error', 'Unknown error')}")
                        elif response.status != 200:
                            raise NetworkError(f"API request failed with status {response.status}")
                        
                        # Parse response
                        data = await response.json()
                        
                        # Check for API errors in response
                        if "error" in data:
                            raise SerpApiError(f"API error: {data['error']}")
                        
                        return data
                        
            except aiohttp.ClientTimeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    raise NetworkError("Request timed out after retries")
                    
            except aiohttp.ClientError as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise NetworkError(f"Network error: {str(e)}")
            
            # Exponential backoff
            await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        raise NetworkError("Failed after maximum retries")
    
    def _build_query_params(self, params: GoogleFlightsParams) -> Dict[str, str]:
        """Build query parameters for API request"""
        query = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "departure_id": params.departure_id,
            "arrival_id": params.arrival_id,
            "outbound_date": params.outbound_date,
            "currency": params.currency,
            "hl": params.hl,
            "gl": params.gl,
            "type": str(params.type),
            "travel_class": str(params.travel_class),
            "adults": str(params.adults),
            "children": str(params.children),
            "stops": str(params.stops),
            "bags": str(params.bags)
        }
        
        # Add optional parameters
        if params.return_date and params.type == 1:  # Round trip
            query["return_date"] = params.return_date
            
        if params.max_price:
            query["max_price"] = str(params.max_price)
            
        if params.include_airlines:
            query["include_airlines"] = ",".join(params.include_airlines)
            
        if params.exclude_airlines:
            query["exclude_airlines"] = ",".join(params.exclude_airlines)
            
        return query
    
    def parse_flight_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw API response into structured format
        
        Args:
            data: Raw API response
            
        Returns:
            Structured flight data
        """
        results = {
            "flights": [],
            "best_flights": [],
            "price_insights": {},
            "airports": {},
            "search_metadata": {}
        }
        
        # Extract search metadata
        if "search_metadata" in data:
            results["search_metadata"] = data["search_metadata"]
        
        # Extract price insights
        if "price_insights" in data:
            results["price_insights"] = data["price_insights"]
        
        # Extract airport information
        if "airports" in data:
            results["airports"] = data["airports"]
        
        # Parse best flights
        if "best_flights" in data:
            results["best_flights"] = self._parse_flight_list(data["best_flights"])
        
        # Parse other flights
        if "other_flights" in data:
            results["flights"] = self._parse_flight_list(data["other_flights"])
        
        return results
    
    def _parse_flight_list(self, flights: List[Dict]) -> List[Dict]:
        """Parse list of flights into normalized format"""
        parsed_flights = []
        
        for flight_group in flights:
            parsed_flight = {
                "price": flight_group.get("price", 0),
                "type": flight_group.get("type", "One way"),
                "total_duration": flight_group.get("total_duration", 0),
                "carbon_emissions": flight_group.get("carbon_emissions", {}),
                "booking_token": flight_group.get("booking_token", ""),
                "segments": []
            }
            
            # Parse individual flight segments
            if "flights" in flight_group:
                for segment in flight_group["flights"]:
                    parsed_segment = {
                        "departure_airport": segment.get("departure_airport", {}),
                        "arrival_airport": segment.get("arrival_airport", {}),
                        "duration": segment.get("duration", 0),
                        "airplane": segment.get("airplane", ""),
                        "airline": segment.get("airline", ""),
                        "airline_logo": segment.get("airline_logo", ""),
                        "flight_number": segment.get("flight_number", ""),
                        "travel_class": segment.get("travel_class", "Economy"),
                        "extensions": segment.get("extensions", []),
                        "overnight": segment.get("overnight", False)
                    }
                    parsed_flight["segments"].append(parsed_segment)
            
            # Parse layovers
            if "layovers" in flight_group:
                parsed_flight["layovers"] = flight_group["layovers"]
            
            parsed_flights.append(parsed_flight)
        
        return parsed_flights


# Async wrapper for synchronous code
def search_flights_sync(params: GoogleFlightsParams) -> Dict[str, Any]:
    """Synchronous wrapper for flight search"""
    client = SerpApiClient()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(client.search_flights(params))
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the client
    print("Testing SerpApi Client")
    print("=" * 50)
    
    # Example search
    test_params = GoogleFlightsParams(
        departure_id="LAX",
        arrival_id="JFK", 
        outbound_date="2024-12-20",
        type=2  # One way
    )
    
    try:
        client = SerpApiClient()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print(f"\nSearching flights from {test_params.departure_id} to {test_params.arrival_id}")
        print(f"Date: {test_params.outbound_date}")
        
        results = loop.run_until_complete(client.search_flights(test_params))
        parsed = client.parse_flight_results(results)
        
        print(f"\nFound {len(parsed['flights']) + len(parsed['best_flights'])} flights")
        
        if parsed['price_insights']:
            print(f"Lowest price: ${parsed['price_insights'].get('lowest_price', 'N/A')}")
        
        loop.close()
        
    except Exception as e:
        print(f"Error: {e}")