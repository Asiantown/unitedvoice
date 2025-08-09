#!/usr/bin/env python3
"""
Enhanced Date Parser for Natural Language
Handles various date formats and expressions
"""

from datetime import datetime, timedelta
import re
from typing import Optional, Tuple
import calendar


class DateParser:
    """Parse natural language dates into standardized format"""
    
    def __init__(self):
        self.today = datetime.now()
        
        # Month names
        self.months = {
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
        
        # Day names
        self.weekdays = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        # Relative time expressions
        self.relative_days = {
            'today': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'yesterday': -1  # For validation
        }
        
        # Holiday periods
        self.holidays = {
            'christmas': (12, 25),
            'new year': (1, 1),
            'new years': (1, 1),
            'thanksgiving': (11, 24),  # Approximate
            'july 4th': (7, 4),
            'fourth of july': (7, 4)
        }
    
    def parse(self, text: str) -> Optional[Tuple[datetime, str]]:
        """
        Parse natural language date
        Returns: (datetime object, formatted string) or None
        """
        if not text:
            return None
            
        text = text.lower().strip()
        
        # Try different parsing strategies
        result = (
            self._parse_relative_days(text) or
            self._parse_in_x_days(text) or
            self._parse_weekday(text) or
            self._parse_month_day(text) or
            self._parse_date_formats(text) or
            self._parse_holidays(text) or
            self._parse_special_expressions(text)
        )
        
        if result:
            # Validate date is in the future
            if result[0].date() < self.today.date():
                # If date is in past, assume next year
                if result[0].month < self.today.month or \
                   (result[0].month == self.today.month and result[0].day < self.today.day):
                    next_year = result[0].replace(year=result[0].year + 1)
                    return (next_year, next_year.strftime("%B %d, %Y"))
            
            return result
        
        return None
    
    def _parse_relative_days(self, text: str) -> Optional[Tuple[datetime, str]]:
        """Parse relative day expressions (today, tomorrow, etc.)"""
        for phrase, days_offset in self.relative_days.items():
            if phrase in text and days_offset >= 0:  # Exclude yesterday
                target_date = self.today + timedelta(days=days_offset)
                return (target_date, target_date.strftime("%B %d"))
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
    
    def format_date(self, date: datetime) -> str:
        """Format date for display"""
        # Add day of week for dates within next 2 weeks
        days_until = (date.date() - self.today.date()).days
        
        if days_until == 0:
            return "Today " + date.strftime("(%B %d)")
        elif days_until == 1:
            return "Tomorrow " + date.strftime("(%B %d)")
        elif days_until <= 14:
            return date.strftime("%A, %B %d")
        else:
            return date.strftime("%B %d")


# Test the date parser
if __name__ == "__main__":
    parser = DateParser()
    
    # Test cases
    test_inputs = [
        # Relative days
        "today",
        "tomorrow",
        "day after tomorrow",
        
        # In X days/weeks
        "in 3 days",
        "in a week",
        "in 2 weeks",
        "in 1 month",
        
        # Weekdays
        "this Friday",
        "next Monday",
        "Thursday",
        "next Thursday",
        
        # Month + day
        "March 15",
        "March 15th",
        "15th of March",
        "December 25",
        "Dec 25",
        
        # Numeric formats
        "3/15",
        "12-25",
        
        # Holidays
        "Christmas",
        "New Years",
        "Thanksgiving",
        
        # Special expressions
        "this weekend",
        "end of month",
        "beginning of month",
        
        # Complex expressions
        "I want to fly next Friday",
        "sometime in March",
        "leaving December 15th",
    ]
    
    print("Date Parser Test Results")
    print("="*60)
    
    for test_input in test_inputs:
        result = parser.parse(test_input)
        if result:
            date_obj, formatted = result
            display = parser.format_date(date_obj)
            print(f"✅ '{test_input}' → {display}")
        else:
            print(f"❌ '{test_input}' → Could not parse")
    
    print("\n" + "="*60)
    print(f"Today's date: {datetime.now().strftime('%A, %B %d, %Y')}")