#!/usr/bin/env python3
"""
Airport Mapper Utility
Maps city names to IATA airport codes for flight searches
"""

import json
import os
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)


class AirportMapper:
    """Maps city names to airport codes"""
    
    def __init__(self):
        # Comprehensive airport database
        self.airports = {
            # Major US Cities with multiple airports
            "new york": ["JFK", "LGA", "EWR"],
            "nyc": ["JFK", "LGA", "EWR"],
            "manhattan": ["JFK", "LGA", "EWR"],
            "los angeles": ["LAX", "BUR", "LGB", "SNA"],
            "la": ["LAX", "BUR", "LGB"],
            "chicago": ["ORD", "MDW"],
            "washington": ["DCA", "IAD", "BWI"],
            "dc": ["DCA", "IAD", "BWI"],
            "washington dc": ["DCA", "IAD", "BWI"],
            "san francisco": ["SFO", "OAK", "SJC"],
            "sf": ["SFO", "OAK"],
            "bay area": ["SFO", "OAK", "SJC"],
            "miami": ["MIA", "FLL"],
            "south florida": ["MIA", "FLL", "PBI"],
            "dallas": ["DFW", "DAL"],
            "houston": ["IAH", "HOU"],
            "london": ["LHR", "LGW", "STN", "LCY", "LTN"],
            "paris": ["CDG", "ORY"],
            "tokyo": ["NRT", "HND"],
            
            # Single Airport Cities
            "boston": ["BOS"],
            "seattle": ["SEA"],
            "denver": ["DEN"],
            "atlanta": ["ATL"],
            "phoenix": ["PHX"],
            "philadelphia": ["PHL"],
            "detroit": ["DTW"],
            "minneapolis": ["MSP"],
            "orlando": ["MCO"],
            "las vegas": ["LAS"],
            "vegas": ["LAS"],
            "nashville": ["BNA"],
            "portland": ["PDX"],
            "salt lake city": ["SLC"],
            "charlotte": ["CLT"],
            "pittsburgh": ["PIT"],
            "cincinnati": ["CVG"],
            "cleveland": ["CLE"],
            "baltimore": ["BWI"],
            "kansas city": ["MCI"],
            "san diego": ["SAN"],
            "san antonio": ["SAT"],
            "austin": ["AUS"],
            "raleigh": ["RDU"],
            "tampa": ["TPA"],
            "jacksonville": ["JAX"],
            "memphis": ["MEM"],
            "milwaukee": ["MKE"],
            "indianapolis": ["IND"],
            "columbus": ["CMH"],
            "sacramento": ["SMF"],
            "san jose": ["SJC"],
            "oakland": ["OAK"],
            "new orleans": ["MSY"],
            "st louis": ["STL"],
            "saint louis": ["STL"],
            "honolulu": ["HNL"],
            "anchorage": ["ANC"],
            "albuquerque": ["ABQ"],
            "albany": ["ALB"],
            "buffalo": ["BUF"],
            "burbank": ["BUR"],
            "charleston": ["CHS"],
            "des moines": ["DSM"],
            "el paso": ["ELP"],
            "fort lauderdale": ["FLL"],
            "fort myers": ["RSW"],
            "fresno": ["FAT"],
            "grand rapids": ["GRR"],
            "hartford": ["BDL"],
            "long beach": ["LGB"],
            "louisville": ["SDF"],
            "madison": ["MSN"],
            "manchester": ["MHT"],
            "norfolk": ["ORF"],
            "oklahoma city": ["OKC"],
            "omaha": ["OMA"],
            "ontario": ["ONT"],
            "palm beach": ["PBI"],
            "west palm beach": ["PBI"],
            "providence": ["PVD"],
            "richmond": ["RIC"],
            "rochester": ["ROC"],
            "santa ana": ["SNA"],
            "orange county": ["SNA"],
            "spokane": ["GEG"],
            "syracuse": ["SYR"],
            "tucson": ["TUS"],
            "tulsa": ["TUL"],
            "wichita": ["ICT"],
            
            # International Cities
            "toronto": ["YYZ", "YTZ"],
            "vancouver": ["YVR"],
            "montreal": ["YUL"],
            "calgary": ["YYC"],
            "mexico city": ["MEX"],
            "cancun": ["CUN"],
            "guadalajara": ["GDL"],
            "amsterdam": ["AMS"],
            "frankfurt": ["FRA"],
            "munich": ["MUC"],
            "berlin": ["BER"],
            "rome": ["FCO", "CIA"],
            "milan": ["MXP", "LIN"],
            "madrid": ["MAD"],
            "barcelona": ["BCN"],
            "lisbon": ["LIS"],
            "dublin": ["DUB"],
            "brussels": ["BRU"],
            "vienna": ["VIE"],
            "zurich": ["ZRH"],
            "geneva": ["GVA"],
            "copenhagen": ["CPH"],
            "stockholm": ["ARN"],
            "oslo": ["OSL"],
            "helsinki": ["HEL"],
            "athens": ["ATH"],
            "istanbul": ["IST"],
            "dubai": ["DXB"],
            "abu dhabi": ["AUH"],
            "doha": ["DOH"],
            "singapore": ["SIN"],
            "hong kong": ["HKG"],
            "shanghai": ["PVG", "SHA"],
            "beijing": ["PEK", "PKX"],
            "seoul": ["ICN", "GMP"],
            "bangkok": ["BKK", "DMK"],
            "kuala lumpur": ["KUL"],
            "jakarta": ["CGK"],
            "sydney": ["SYD"],
            "melbourne": ["MEL"],
            "brisbane": ["BNE"],
            "auckland": ["AKL"],
            "mumbai": ["BOM"],
            "delhi": ["DEL"],
            "bangalore": ["BLR"],
            "chennai": ["MAA"],
            "hyderabad": ["HYD"],
            "kolkata": ["CCU"],
            "cairo": ["CAI"],
            "johannesburg": ["JNB"],
            "cape town": ["CPT"],
            "lagos": ["LOS"],
            "nairobi": ["NBO"],
            "casablanca": ["CMN"],
            "buenos aires": ["EZE", "AEP"],
            "sao paulo": ["GRU", "CGH"],
            "rio de janeiro": ["GIG", "SDU"],
            "lima": ["LIM"],
            "santiago": ["SCL"],
            "bogota": ["BOG"],
            "quito": ["UIO"],
            "panama city": ["PTY"],
            "san jose costa rica": ["SJO"],
            "havana": ["HAV"],
            "santo domingo": ["SDQ"],
            "san juan": ["SJU"],
            
            # US State names to major airports
            "california": ["LAX", "SFO", "SAN", "SJC"],
            "texas": ["DFW", "IAH", "AUS", "SAT"],
            "florida": ["MIA", "MCO", "TPA", "FLL"],
            "new york state": ["JFK", "LGA", "BUF", "ALB"],
            "illinois": ["ORD", "MDW"],
            "georgia": ["ATL"],
            "arizona": ["PHX", "TUS"],
            "nevada": ["LAS", "RNO"],
            "colorado": ["DEN"],
            "massachusetts": ["BOS"],
            "michigan": ["DTW", "GRR"],
            "pennsylvania": ["PHL", "PIT"],
            "ohio": ["CLE", "CMH", "CVG"],
            "north carolina": ["CLT", "RDU"],
            "tennessee": ["BNA", "MEM"],
            "missouri": ["STL", "MCI"],
            "louisiana": ["MSY"],
            "oregon": ["PDX"],
            "washington state": ["SEA", "GEG"],
            "utah": ["SLC"],
            "minnesota": ["MSP"],
            "wisconsin": ["MKE", "MSN"],
            "indiana": ["IND"],
            "maryland": ["BWI"],
            "connecticut": ["BDL"],
            "virginia": ["DCA", "IAD", "ORF", "RIC"],
            "hawaii": ["HNL", "OGG", "KOA", "LIH"],
            "alaska": ["ANC", "FAI", "JNU"]
        }
        
        # Airport code to city name mapping (for validation)
        self.airport_to_city = {
            "JFK": "New York",
            "LGA": "New York",
            "EWR": "Newark/New York",
            "LAX": "Los Angeles",
            "ORD": "Chicago",
            "DFW": "Dallas",
            "ATL": "Atlanta",
            "DEN": "Denver",
            "SFO": "San Francisco",
            "SEA": "Seattle",
            "LAS": "Las Vegas",
            "MCO": "Orlando",
            "MIA": "Miami",
            "PHX": "Phoenix",
            "IAH": "Houston",
            "BOS": "Boston",
            "MSP": "Minneapolis",
            "DTW": "Detroit",
            "PHL": "Philadelphia",
            "LGA": "New York",
            "DCA": "Washington DC",
            "IAD": "Washington DC",
            "BWI": "Baltimore/Washington",
            "CLT": "Charlotte",
            "SLC": "Salt Lake City",
            "DEN": "Denver",
            "SAN": "San Diego",
            "TPA": "Tampa",
            "PDX": "Portland",
            "AUS": "Austin",
            "BNA": "Nashville",
            "RDU": "Raleigh",
            "MSY": "New Orleans",
            "MCI": "Kansas City",
            "SMF": "Sacramento",
            "SJC": "San Jose",
            "OAK": "Oakland",
            "IND": "Indianapolis",
            "CMH": "Columbus",
            "CLE": "Cleveland",
            "PIT": "Pittsburgh",
            "CVG": "Cincinnati",
            "STL": "St. Louis",
            "MKE": "Milwaukee",
            "BDL": "Hartford",
            "JAX": "Jacksonville",
            "MEM": "Memphis",
            "BUF": "Buffalo",
            "ALB": "Albany",
            "OMA": "Omaha",
            "TUL": "Tulsa",
            "OKC": "Oklahoma City",
            "ABQ": "Albuquerque",
            "SAT": "San Antonio",
            "ELP": "El Paso",
            "TUS": "Tucson",
            "RNO": "Reno",
            "SNA": "Orange County",
            "ONT": "Ontario",
            "BUR": "Burbank",
            "LGB": "Long Beach",
            "FAT": "Fresno",
            "ANC": "Anchorage",
            "HNL": "Honolulu",
            # Add more as needed
        }
        
        # Common variations and nicknames
        self.city_variations = {
            "nyc": "new york",
            "ny": "new york",
            "la": "los angeles", 
            "sf": "san francisco",
            "dc": "washington",
            "vegas": "las vegas",
            "nola": "new orleans",
            "philly": "philadelphia",
            "kc": "kansas city",
            "okc": "oklahoma city",
            "the bay": "san francisco",
            "bay area": "san francisco",
            "twin cities": "minneapolis",
            "windy city": "chicago",
            "big apple": "new york",
            "atl": "atlanta",
            "dtw": "detroit",
            "dfw": "dallas",
            "iah": "houston",
            "mia": "miami",
            "big d": "dallas",
            "h-town": "houston",
            "chi-town": "chicago",
            "beantown": "boston",
            "music city": "nashville",
            "motor city": "detroit",
            "mile high": "denver",
            "emerald city": "seattle",
            "alamo city": "san antonio"
        }
    
    def get_airport_codes(self, city_name: str) -> List[str]:
        """
        Get airport codes for a given city name
        
        Args:
            city_name: Name of the city
            
        Returns:
            List of IATA airport codes
        """
        if not city_name:
            return []
        
        city_lower = city_name.lower().strip()
        
        # Check if it's already an airport code
        if len(city_lower) == 3 and city_lower.upper() in self.airport_to_city:
            return [city_lower.upper()]
        
        # Check variations first
        if city_lower in self.city_variations:
            city_lower = self.city_variations[city_lower]
        
        # Direct lookup
        if city_lower in self.airports:
            return self.airports[city_lower]
        
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for city in self.airports:
            score = fuzz.ratio(city_lower, city)
            if score > best_score and score > 80:  # 80% similarity threshold
                best_score = score
                best_match = city
        
        if best_match:
            logger.info(f"Fuzzy matched '{city_name}' to '{best_match}' (score: {best_score})")
            return self.airports[best_match]
        
        # Check if it contains a known city name
        for city, codes in self.airports.items():
            if city in city_lower or city_lower in city:
                return codes
        
        logger.warning(f"No airport codes found for city: {city_name}")
        return []
    
    def get_city_name(self, airport_code: str) -> Optional[str]:
        """
        Get city name for a given airport code
        
        Args:
            airport_code: IATA airport code
            
        Returns:
            City name or None if not found
        """
        code_upper = airport_code.upper()
        return self.airport_to_city.get(code_upper)
    
    def validate_airport_code(self, code: str) -> bool:
        """
        Validate if a string is a valid airport code
        
        Args:
            code: String to validate
            
        Returns:
            True if valid airport code
        """
        return len(code) == 3 and code.upper() in self.airport_to_city
    
    def get_all_airports(self) -> Dict[str, List[str]]:
        """Get all airports in the database"""
        return self.airports.copy()
    
    def search_airports(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Search for airports by partial city or airport name
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching airports with city names
        """
        query_lower = query.lower()
        results = []
        
        # Search by city name
        for city, codes in self.airports.items():
            if query_lower in city:
                for code in codes:
                    results.append({
                        "code": code,
                        "city": city.title(),
                        "name": self.airport_to_city.get(code, city.title())
                    })
        
        # Search by airport code
        for code, city in self.airport_to_city.items():
            if query_lower in code.lower():
                results.append({
                    "code": code,
                    "city": city,
                    "name": city
                })
        
        # Remove duplicates and limit results
        seen = set()
        unique_results = []
        for result in results:
            if result["code"] not in seen:
                seen.add(result["code"])
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results


if __name__ == "__main__":
    # Test the airport mapper
    mapper = AirportMapper()
    
    print("Testing Airport Mapper")
    print("=" * 50)
    
    test_cities = [
        "New York",
        "San Francisco", 
        "houston",
        "NYC",
        "LA",
        "The Bay Area",
        "Connecticut",  # Should not match
        "JFK",  # Airport code
        "atlanta"
    ]
    
    for city in test_cities:
        codes = mapper.get_airport_codes(city)
        print(f"{city} -> {codes}")
    
    print("\nSearching for 'san':")
    results = mapper.search_airports("san")
    for result in results:
        print(f"  {result['code']} - {result['city']}")