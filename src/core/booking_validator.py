"""
Validation logic for booking information with confidence scoring.
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    confidence: float = 0.0
    normalized_value: Any = None
    error_message: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class BookingValidator:
    """Validates and normalizes booking information."""
    
    # Common airport codes and cities
    AIRPORT_CODES = {
        # Major US cities
        "LAX": "Los Angeles", "JFK": "New York", "LGA": "New York", "EWR": "New York",
        "ORD": "Chicago", "MDW": "Chicago", "DFW": "Dallas", "DAL": "Dallas",
        "ATL": "Atlanta", "DEN": "Denver", "PHX": "Phoenix", "LAS": "Las Vegas",
        "SEA": "Seattle", "SFO": "San Francisco", "SJC": "San Jose", "OAK": "Oakland",
        "MIA": "Miami", "FLL": "Fort Lauderdale", "MCO": "Orlando", "TPA": "Tampa",
        "BOS": "Boston", "BWI": "Baltimore", "DCA": "Washington", "IAD": "Washington",
        "PHL": "Philadelphia", "CLT": "Charlotte", "MSP": "Minneapolis", "DTW": "Detroit",
        "STL": "St. Louis", "CLE": "Cleveland", "PIT": "Pittsburgh", "CVG": "Cincinnati",
        "MEM": "Memphis", "BNA": "Nashville", "RDU": "Raleigh", "GSO": "Greensboro",
        "SAT": "San Antonio", "AUS": "Austin", "HOU": "Houston", "IAH": "Houston",
        "MSY": "New Orleans", "JAX": "Jacksonville", "RSW": "Fort Myers",
        "SLC": "Salt Lake City", "PDX": "Portland", "SMF": "Sacramento",
        "SAN": "San Diego", "ABQ": "Albuquerque", "TUS": "Tucson", "ELP": "El Paso",
        
        # International
        "LHR": "London", "CDG": "Paris", "FRA": "Frankfurt", "AMS": "Amsterdam",
        "NRT": "Tokyo", "ICN": "Seoul", "PEK": "Beijing", "PVG": "Shanghai",
        "SYD": "Sydney", "MEL": "Melbourne", "YYZ": "Toronto", "YVR": "Vancouver"
    }
    
    CITY_TO_AIRPORTS = {v: k for k, v in AIRPORT_CODES.items()}
    
    # Add city variations
    CITY_VARIATIONS = {
        "new york": ["JFK", "LGA", "EWR"],
        "nyc": ["JFK", "LGA", "EWR"],
        "ny": ["JFK", "LGA", "EWR"],
        "chicago": ["ORD", "MDW"],
        "dallas": ["DFW", "DAL"],
        "washington": ["DCA", "IAD"],
        "dc": ["DCA", "IAD"],
        "houston": ["IAH", "HOU"],
        "los angeles": ["LAX"],
        "la": ["LAX"],
        "san francisco": ["SFO"],
        "sf": ["SFO"],
        "san jose": ["SJC"],
        "oakland": ["OAK"],
        "fort lauderdale": ["FLL"],
        "miami": ["MIA"],
        "orlando": ["MCO"],
        "tampa": ["TPA"],
        "baltimore": ["BWI"],
        "fort myers": ["RSW"],
        "salt lake city": ["SLC"],
        "portland": ["PDX"],
        "sacramento": ["SMF"],
        "san diego": ["SAN"],
        "albuquerque": ["ABQ"],
        "tucson": ["TUS"],
        "el paso": ["ELP"],
        "london": ["LHR"],
        "paris": ["CDG"],
        "frankfurt": ["FRA"],
        "amsterdam": ["AMS"],
        "tokyo": ["NRT"],
        "seoul": ["ICN"],
        "beijing": ["PEK"],
        "shanghai": ["PVG"],
        "sydney": ["SYD"],
        "melbourne": ["MEL"],
        "toronto": ["YYZ"],
        "vancouver": ["YVR"]
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.date_formats = [
            "%Y-%m-%d",      # 2024-03-15
            "%m/%d/%Y",      # 03/15/2024
            "%m-%d-%Y",      # 03-15-2024
            "%B %d, %Y",     # March 15, 2024
            "%b %d, %Y",     # Mar 15, 2024
            "%d %B %Y",      # 15 March 2024
            "%d %b %Y",      # 15 Mar 2024
            "%m/%d",         # 03/15 (current year assumed)
            "%B %d",         # March 15 (current year assumed)
            "%b %d",         # Mar 15 (current year assumed)
        ]
    
    def validate_city_pair(self, departure: str, arrival: str) -> ValidationResult:
        """
        Validate and normalize city pair.
        
        Args:
            departure: Departure city or airport code
            arrival: Arrival city or airport code
            
        Returns:
            ValidationResult with normalized airport codes
        """
        if not departure or not arrival:
            return ValidationResult(
                is_valid=False,
                error_message="Both departure and arrival cities are required"
            )
        
        # Normalize departure
        dep_result = self._normalize_city(departure)
        arr_result = self._normalize_city(arrival)
        
        if not dep_result.is_valid or not arr_result.is_valid:
            suggestions = []
            if not dep_result.is_valid:
                suggestions.extend([f"Departure: {s}" for s in dep_result.suggestions])
            if not arr_result.is_valid:
                suggestions.extend([f"Arrival: {s}" for s in arr_result.suggestions])
            
            return ValidationResult(
                is_valid=False,
                error_message="Could not identify one or both cities",
                suggestions=suggestions
            )
        
        # Check if same city
        if dep_result.normalized_value == arr_result.normalized_value:
            return ValidationResult(
                is_valid=False,
                error_message="Departure and arrival cities cannot be the same",
                suggestions=["Please specify different departure and arrival cities"]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=min(dep_result.confidence, arr_result.confidence),
            normalized_value={
                "departure": dep_result.normalized_value,
                "arrival": arr_result.normalized_value
            }
        )
    
    def _normalize_city(self, city: str) -> ValidationResult:
        """Normalize a single city name to airport code."""
        if not city:
            return ValidationResult(is_valid=False, error_message="City name is required")
        
        city_clean = city.strip().upper()
        city_lower = city.strip().lower()
        
        # Direct airport code match
        if city_clean in self.AIRPORT_CODES:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                normalized_value=city_clean
            )
        
        # City name match
        if city_lower in self.CITY_VARIATIONS:
            # For cities with multiple airports, return the primary one
            primary_airport = self.CITY_VARIATIONS[city_lower][0]
            return ValidationResult(
                is_valid=True,
                confidence=0.9,
                normalized_value=primary_airport
            )
        
        # Fuzzy matching for common misspellings
        suggestions = self._get_city_suggestions(city_lower)
        if suggestions:
            return ValidationResult(
                is_valid=False,
                confidence=0.5,
                error_message=f"Could not find exact match for '{city}'",
                suggestions=suggestions[:5]  # Top 5 suggestions
            )
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Unknown city or airport: '{city}'",
            suggestions=["Please use a 3-letter airport code or major city name"]
        )
    
    def _get_city_suggestions(self, city: str) -> List[str]:
        """Get suggestions for misspelled city names."""
        suggestions = []
        
        # Check for partial matches in city names
        for known_city in self.CITY_VARIATIONS.keys():
            if city in known_city or known_city in city:
                suggestions.append(known_city.title())
        
        # Check for partial matches in airport codes
        for code, city_name in self.AIRPORT_CODES.items():
            if city in city_name.lower() or city_name.lower() in city:
                suggestions.append(f"{city_name} ({code})")
        
        return suggestions
    
    def validate_date(self, date_str: str, field_name: str = "date") -> ValidationResult:
        """
        Validate and normalize a date string.
        
        Args:
            date_str: Date string to validate
            field_name: Name of the field for error messages
            
        Returns:
            ValidationResult with normalized date
        """
        if not date_str:
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name.title()} is required"
            )
        
        date_str = date_str.strip()
        
        # Try to parse with different formats
        for fmt in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                
                # For formats without year, assume current year or next year if date has passed
                if "%Y" not in fmt:
                    current_year = datetime.now().year
                    parsed_date = parsed_date.replace(year=current_year)
                    
                    # If date is in the past, assume next year
                    if parsed_date < date.today():
                        parsed_date = parsed_date.replace(year=current_year + 1)
                
                # Validate date is not too far in the past or future
                today = date.today()
                max_future_date = today + timedelta(days=365)  # 1 year from now
                min_past_date = today - timedelta(days=1)      # Yesterday (for flexibility)
                
                if parsed_date < min_past_date:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"{field_name.title()} cannot be in the past",
                        suggestions=[f"Please use a date on or after {today.strftime('%B %d, %Y')}"]
                    )
                
                if parsed_date > max_future_date:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"{field_name.title()} is too far in the future",
                        suggestions=[f"Please use a date before {max_future_date.strftime('%B %d, %Y')}"]
                    )
                
                # Calculate confidence based on format specificity
                confidence = 1.0 if "%Y" in fmt else 0.8
                
                return ValidationResult(
                    is_valid=True,
                    confidence=confidence,
                    normalized_value=parsed_date
                )
                
            except ValueError:
                continue
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Could not parse {field_name}: '{date_str}'",
            suggestions=[
                "Try formats like: March 15, 2024 or 03/15/2024 or 2024-03-15",
                "For dates this year, you can use: March 15 or 03/15"
            ]
        )
    
    def validate_date_order(self, departure_date_str: str, return_date_str: str) -> ValidationResult:
        """
        Validate that return date is after departure date for round trips.
        
        Args:
            departure_date_str: Departure date string
            return_date_str: Return date string
            
        Returns:
            ValidationResult indicating if date order is valid
        """
        # First validate individual dates
        dep_result = self.validate_date(departure_date_str, "departure date")
        if not dep_result.is_valid:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid departure date: {dep_result.error_message}"
            )
        
        ret_result = self.validate_date(return_date_str, "return date")
        if not ret_result.is_valid:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid return date: {ret_result.error_message}"
            )
        
        departure_date = dep_result.normalized_value
        return_date = ret_result.normalized_value
        
        # Check if return date is after departure date
        if return_date <= departure_date:
            # Calculate suggested return date (at least 1 day after departure)
            suggested_date = departure_date + timedelta(days=1)
            
            return ValidationResult(
                is_valid=False,
                error_message="Return date must be after departure date",
                suggestions=[
                    f"Your departure is {departure_date.strftime('%B %d, %Y')}",
                    f"Return date should be {suggested_date.strftime('%B %d, %Y')} or later"
                ]
            )
        
        # Calculate trip duration
        trip_days = (return_date - departure_date).days
        
        # Warn if trip is very long (more than 30 days)
        confidence = 1.0
        if trip_days > 30:
            confidence = 0.7
            
        return ValidationResult(
            is_valid=True,
            confidence=confidence,
            normalized_value={
                "departure_date": departure_date,
                "return_date": return_date,
                "trip_duration_days": trip_days
            }
        )
    
    def validate_name(self, name: str, field_name: str = "name") -> ValidationResult:
        """
        Validate a person's name.
        
        Args:
            name: Name to validate
            field_name: Field name for error messages
            
        Returns:
            ValidationResult with normalized name
        """
        if not name:
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name.title()} is required"
            )
        
        name = name.strip()
        
        # Basic validation
        if len(name) < 1:
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name.title()} cannot be empty"
            )
        
        if len(name) > 50:
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name.title()} is too long (max 50 characters)"
            )
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name.title()} contains invalid characters",
                suggestions=["Names can only contain letters, spaces, hyphens, and apostrophes"]
            )
        
        # Normalize: title case
        normalized_name = name.title()
        
        # Handle special cases like "McDonald", "O'Connor"
        normalized_name = re.sub(r"\bMc([a-z])", r"Mc\1".title(), normalized_name)
        normalized_name = re.sub(r"\bO'([a-z])", r"O'\1".title(), normalized_name)
        
        return ValidationResult(
            is_valid=True,
            confidence=1.0,
            normalized_value=normalized_name
        )
    
    def validate_email(self, email: str) -> ValidationResult:
        """Validate email address."""
        if not email:
            return ValidationResult(
                is_valid=False,
                error_message="Email is required"
            )
        
        email = email.strip().lower()
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid email format",
                suggestions=["Please use format: example@domain.com"]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=1.0,
            normalized_value=email
        )
    
    def validate_phone(self, phone: str) -> ValidationResult:
        """Validate phone number."""
        if not phone:
            return ValidationResult(
                is_valid=False,
                error_message="Phone number is required"
            )
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # US phone number validation
        if len(digits_only) == 10:
            formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only[0] == '1':
            formatted = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid phone number format",
                suggestions=["Please use US format: (555) 123-4567 or +1 (555) 123-4567"]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=1.0,
            normalized_value=formatted
        )
    
    def validate_passenger_count(self, count: Any) -> ValidationResult:
        """Validate passenger count."""
        try:
            count_int = int(count)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="Passenger count must be a number"
            )
        
        if count_int < 1:
            return ValidationResult(
                is_valid=False,
                error_message="Must have at least 1 passenger"
            )
        
        if count_int > 9:
            return ValidationResult(
                is_valid=False,
                error_message="Maximum 9 passengers per booking",
                suggestions=["For groups larger than 9, please make separate bookings"]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=1.0,
            normalized_value=count_int
        )
    
    def validate_cabin_class(self, cabin_class: str) -> ValidationResult:
        """Validate cabin class."""
        if not cabin_class:
            return ValidationResult(
                is_valid=False,
                error_message="Cabin class is required"
            )
        
        cabin_class = cabin_class.strip().lower()
        
        valid_classes = {
            'economy': 'Economy',
            'premium economy': 'Premium Economy',
            'business': 'Business',
            'first': 'First',
            'coach': 'Economy',  # Alias
            'first class': 'First',  # Alias
            'business class': 'Business'  # Alias
        }
        
        if cabin_class in valid_classes:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                normalized_value=valid_classes[cabin_class]
            )
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Unknown cabin class: '{cabin_class}'",
            suggestions=list(set(valid_classes.values()))
        )