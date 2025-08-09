#!/usr/bin/env python3
"""
Enhanced Date Parser for Natural Language Processing

A comprehensive date parsing system that converts natural language date expressions
into standardized datetime objects. Supports various formats including relative dates,
weekdays, holidays, and numeric formats.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

import calendar
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union

# Configure module logger
logger = logging.getLogger(__name__)


class DateParser:
    """
    Enhanced natural language date parser.
    
    Converts human-readable date expressions into datetime objects with
    comprehensive support for various date formats, relative expressions,
    and special date references.
    
    Features:
    - Relative dates (today, tomorrow, next Friday)
    - Numeric formats (3/15, 12-25)
    - Holiday recognition (Christmas, Thanksgiving)
    - Flexible expressions (end of month, this weekend)
    - Automatic future date inference
    
    Attributes:
        today: Reference datetime for relative calculations
        months: Dictionary mapping month names to numbers
        weekdays: Dictionary mapping weekday names to numbers
        relative_days: Dictionary mapping relative expressions
        holidays: Dictionary mapping holiday names to dates
    """
    
    def __init__(self, reference_date: Optional[datetime] = None) -> None:
        """
        Initialize the date parser.
        
        Args:
            reference_date: Reference date for relative calculations.
                           Defaults to current datetime if not provided.
        """
        self.today = reference_date or datetime.now()
        logger.debug(f"DateParser initialized with reference date: {self.today.strftime('%Y-%m-%d')}")
        
        # Month name mappings with comprehensive variations
        self.months: Dict[str, int] = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        # Weekday name mappings with variations
        self.weekdays: Dict[str, int] = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        # Relative time expressions mapping
        self.relative_days: Dict[str, int] = {
            'today': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'yesterday': -1  # Included for validation but filtered out
        }
        
        # Holiday date mappings (month, day)
        self.holidays: Dict[str, Tuple[int, int]] = {
            'christmas': (12, 25),
            'new year': (1, 1),
            'new years': (1, 1),
            'thanksgiving': (11, 24),  # Approximate - 4th Thursday varies
            'july 4th': (7, 4),
            'fourth of july': (7, 4),
            'independence day': (7, 4),
            'memorial day': (5, 30),  # Approximate
            'labor day': (9, 7),  # Approximate
        }
    
    def parse(self, text: str) -> Optional[Tuple[datetime, str]]:
        """
        Parse natural language date expressions into datetime objects.
        
        Args:
            text: Natural language date expression
            
        Returns:
            Tuple of (datetime object, formatted string) if parsing succeeds,
            None otherwise
            
        Raises:
            ValueError: If text is not a string
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
            
        if not text.strip():
            logger.debug("Empty input text provided")
            return None
            
        text = text.lower().strip()
        logger.debug(f"Parsing date expression: '{text}'")
        
        # Try parsing strategies in order of specificity
        parsing_strategies = [
            self._parse_relative_days,
            self._parse_in_x_days,
            self._parse_weekday,
            self._parse_month_day,
            self._parse_date_formats,
            self._parse_holidays,
            self._parse_special_expressions
        ]
        
        for strategy in parsing_strategies:
            try:
                result = strategy(text)
                if result:
                    logger.debug(f"Successfully parsed with {strategy.__name__}: {result[1]}")
                    break
            except Exception as e:
                logger.warning(f"Error in {strategy.__name__}: {e}")
                continue
        else:
            logger.debug(f"Failed to parse date expression: '{text}'")
            return None
        
        # Apply future date validation and adjustment
        return self._validate_and_adjust_date(result)
    
    def _validate_and_adjust_date(self, result: Optional[Tuple[datetime, str]]) -> Optional[Tuple[datetime, str]]:
        """
        Validate and adjust parsed date to ensure it's in the future.
        
        Args:
            result: Parsing result tuple or None
            
        Returns:
            Adjusted result tuple or None
        """
        if not result:
            return None
            
        date_obj, _ = result
        
        # If date is in the past, adjust to next occurrence
        if date_obj.date() < self.today.date():
            logger.debug(f"Date {date_obj.date()} is in past, adjusting to future")
            
            # For dates in current year that have passed, try next year
            if (date_obj.month < self.today.month or 
                (date_obj.month == self.today.month and date_obj.day < self.today.day)):
                
                next_year_date = date_obj.replace(year=date_obj.year + 1)
                formatted = next_year_date.strftime("%B %d, %Y")
                logger.debug(f"Adjusted to next year: {formatted}")
                return (next_year_date, formatted)
        
        return result
    
    def _parse_relative_days(self, text: str) -> Optional[Tuple[datetime, str]]:
        """
        Parse relative day expressions (today, tomorrow, etc.).
        
        Args:
            text: Input text to parse
            
        Returns:
            Parsed date tuple or None
        """
        for phrase, days_offset in self.relative_days.items():
            if phrase in text and days_offset >= 0:  # Exclude yesterday
                target_date = self.today + timedelta(days=days_offset)
                formatted = target_date.strftime("%B %d")
                return (target_date, formatted)
        return None
    
    def _parse_in_x_days(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse 'in X days/weeks/months' expressions"""
        # In X days
        match = re.search(r'in (\d+) days?', text)
        if match:
            days = int(match.group(1))
            target_date = self.today + timedelta(days=days)
            return (target_date, target_date.strftime("%B %d"))
        
        # In X weeks
        match = re.search(r'in (\d+) weeks?', text)
        if match:
            weeks = int(match.group(1))
            target_date = self.today + timedelta(weeks=weeks)
            return (target_date, target_date.strftime("%B %d"))
        
        # In a week
        if 'in a week' in text or 'next week' in text:
            target_date = self.today + timedelta(weeks=1)
            return (target_date, target_date.strftime("%B %d"))
        
        # In X months (approximate)
        match = re.search(r'in (\d+) months?', text)
        if match:
            months = int(match.group(1))
            target_date = self.today + timedelta(days=months * 30)
            return (target_date, target_date.strftime("%B %d"))
        
        return None
    
    def _parse_weekday(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse weekday references (this Friday, next Monday, etc.)"""
        for day_name, day_num in self.weekdays.items():
            if day_name in text:
                current_weekday = self.today.weekday()
                days_until = (day_num - current_weekday) % 7
                
                # Handle this/next modifiers
                if 'next' in text:
                    days_until += 7
                elif 'this' in text and days_until == 0:
                    days_until = 7  # If today is the day, assume next week
                elif days_until == 0:
                    days_until = 7  # Default to next week if today
                
                target_date = self.today + timedelta(days=days_until)
                return (target_date, target_date.strftime("%B %d"))
        
        return None
    
    def _parse_month_day(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse month and day combinations"""
        # Try month name + day
        for month_name, month_num in self.months.items():
            if month_name in text:
                # Look for day number after month
                pattern = rf'{month_name}\s*(\d{{1,2}})'
                match = re.search(pattern, text)
                if match:
                    day = int(match.group(1))
                    if 1 <= day <= 31:
                        try:
                            # Use current year initially
                            year = self.today.year
                            target_date = datetime(year, month_num, day)
                            
                            # If date is in past, use next year
                            if target_date.date() < self.today.date():
                                target_date = datetime(year + 1, month_num, day)
                            
                            return (target_date, target_date.strftime("%B %d"))
                        except ValueError:
                            pass  # Invalid day for month
                
                # Look for day number before month (e.g., "15th of March")
                pattern = rf'(\d{{1,2}})\w*\s*(?:of\s*)?{month_name}'
                match = re.search(pattern, text)
                if match:
                    day = int(match.group(1))
                    if 1 <= day <= 31:
                        try:
                            year = self.today.year
                            target_date = datetime(year, month_num, day)
                            
                            if target_date.date() < self.today.date():
                                target_date = datetime(year + 1, month_num, day)
                            
                            return (target_date, target_date.strftime("%B %d"))
                        except ValueError:
                            pass
        
        return None
    
    def _parse_date_formats(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse numeric date formats"""
        # MM/DD or MM-DD
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})', text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    year = self.today.year
                    target_date = datetime(year, month, day)
                    
                    if target_date.date() < self.today.date():
                        target_date = datetime(year + 1, month, day)
                    
                    return (target_date, target_date.strftime("%B %d"))
                except ValueError:
                    pass
        
        return None
    
    def _parse_holidays(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse holiday references"""
        for holiday, (month, day) in self.holidays.items():
            if holiday in text:
                year = self.today.year
                target_date = datetime(year, month, day)
                
                # If holiday passed this year, use next year
                if target_date.date() < self.today.date():
                    target_date = datetime(year + 1, month, day)
                
                holiday_name = holiday.title()
                return (target_date, f"{holiday_name} ({target_date.strftime('%B %d')})")
        
        return None
    
    def _parse_special_expressions(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse special expressions like 'end of month', 'weekend', etc."""
        # This weekend
        if 'this weekend' in text or 'the weekend' in text:
            days_until_saturday = (5 - self.today.weekday()) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            target_date = self.today + timedelta(days=days_until_saturday)
            return (target_date, target_date.strftime("%B %d") + " (Saturday)")
        
        # End of month
        if 'end of month' in text or 'end of the month' in text:
            # Get last day of current month
            last_day = calendar.monthrange(self.today.year, self.today.month)[1]
            target_date = datetime(self.today.year, self.today.month, last_day)
            
            # If we're already past the 25th, assume next month
            if self.today.day > 25:
                if self.today.month == 12:
                    target_date = datetime(self.today.year + 1, 1, 31)
                else:
                    next_month = self.today.month + 1
                    last_day = calendar.monthrange(self.today.year, next_month)[1]
                    target_date = datetime(self.today.year, next_month, last_day)
            
            return (target_date, target_date.strftime("%B %d"))
        
        # Beginning of month
        if 'beginning of month' in text or 'start of month' in text:
            if self.today.day > 15:  # If past mid-month, assume next month
                if self.today.month == 12:
                    target_date = datetime(self.today.year + 1, 1, 1)
                else:
                    target_date = datetime(self.today.year, self.today.month + 1, 1)
            else:
                target_date = datetime(self.today.year, self.today.month, 1)
            
            return (target_date, target_date.strftime("%B %d"))
        
        return None
    
    def format_date(self, date: datetime, include_year: bool = False) -> str:
        """
        Format datetime object for user-friendly display.
        
        Args:
            date: Datetime object to format
            include_year: Whether to include year in formatting
            
        Returns:
            Formatted date string
            
        Raises:
            ValueError: If date is not a datetime object
        """
        if not isinstance(date, datetime):
            raise ValueError("Input must be a datetime object")
            
        try:
            days_until = (date.date() - self.today.date()).days
            
            # Format based on relative distance
            if days_until == 0:
                return "Today " + date.strftime("(%B %d)")
            elif days_until == 1:
                return "Tomorrow " + date.strftime("(%B %d)")
            elif 2 <= days_until <= 14:
                base_format = date.strftime("%A, %B %d")
                return base_format + (f", %Y" if include_year or date.year != self.today.year else "")
            else:
                year_suffix = f", %Y" if include_year or date.year != self.today.year else ""
                return date.strftime(f"%B %d{year_suffix}")
                
        except Exception as e:
            logger.error(f"Error formatting date {date}: {e}")
            # Fallback to simple format
            return date.strftime("%B %d, %Y")


def main() -> None:
    """
    Test the date parser functionality.
    
    Demonstrates various date parsing capabilities with test cases.
    """
    parser = DateParser()
    
    print(f"DateParser Test Suite (Reference: {parser.today.strftime('%Y-%m-%d')})")
    print("=" * 70)
    
    # Comprehensive test cases organized by category
    test_categories = {
        "Relative Days": [
            "today", "tomorrow", "day after tomorrow"
        ],
        "Time Offsets": [
            "in 3 days", "in a week", "in 2 weeks", "in 1 month"
        ],
        "Weekdays": [
            "this Friday", "next Monday", "Thursday", "next Thursday"
        ],
        "Month + Day": [
            "March 15", "March 15th", "15th of March", "December 25", "Dec 25"
        ],
        "Numeric Formats": [
            "3/15", "12-25"
        ],
        "Holidays": [
            "Christmas", "New Years", "Thanksgiving", "Independence Day"
        ],
        "Special Expressions": [
            "this weekend", "end of month", "beginning of month"
        ],
        "Complex Expressions": [
            "I want to fly next Friday", "sometime in March", "leaving December 15th"
        ]
    }
    
    success_count = 0
    total_count = 0
    
    for category, test_inputs in test_categories.items():
        print(f"\n📅 {category}:")
        print("-" * (len(category) + 3))
        
        for test_input in test_inputs:
            total_count += 1
            try:
                result = parser.parse(test_input)
                if result:
                    date_obj, formatted = result
                    display = parser.format_date(date_obj, include_year=True)
                    print(f"  ✅ '{test_input}' → {display}")
                    success_count += 1
                else:
                    print(f"  ❌ '{test_input}' → Could not parse")
            except Exception as e:
                print(f"  🐛 '{test_input}' → Error: {e}")
    
    # Summary statistics
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"\n{'='*70}")
    print(f"📊 Test Results: {success_count}/{total_count} ({success_rate:.1f}%) successful")
    print(f"🗓️  Reference Date: {parser.today.strftime('%A, %B %d, %Y')}")


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    main()