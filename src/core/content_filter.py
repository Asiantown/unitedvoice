"""
Content Filter Module for United Voice Agent

This module provides comprehensive content filtering capabilities to ensure
safe and appropriate interactions in the voice agent system.
"""

import re
import logging
from typing import Tuple, Optional, Dict, List, Set
from enum import Enum
import unicodedata


class InappropriateType(Enum):
    """Enumeration of inappropriate content types."""
    PROFANITY = "profanity"
    PERSONAL_INFO = "personal_info"
    MALICIOUS_INPUT = "malicious_input"
    INAPPROPRIATE_NAME = "inappropriate_name"
    SPAM = "spam"
    HATE_SPEECH = "hate_speech"


class ContentFilter:
    """
    A comprehensive content filter for voice agent interactions.
    
    Provides methods to detect inappropriate content, sanitize input,
    and generate appropriate responses for filtered content.
    """
    
    def __init__(self):
        """Initialize the ContentFilter with predefined word lists and patterns."""
        self.logger = logging.getLogger(__name__)
        
        # Profanity word lists (expandable)
        self._profanity_words = {
            # Common profanity (using partial representations for code safety)
            'f***', 'f**k', 'sh**', 's***', 'd***', 'b****', 'a**', 'h***',
            'damn', 'crap', 'piss', 'bastard', 'bitch', 'hell',
            # Anatomical terms that are inappropriate for names
            'penis', 'dick', 'cock', 'pussy', 'vagina', 'tits', 'boobs',
            # Other inappropriate terms
            'motherfucker', 'asshole', 'whore', 'slut', 'faggot', 'retard',
            'nigger', 'chink', 'spic', 'kike'
        }
        
        # Variations and leetspeak patterns
        self._profanity_patterns = [
            r'\bf+u+c+k+\w*',
            r'\bs+h+i+t+\w*',
            r'\bd+a+m+n+\w*',
            r'\ba+s+s+\w*',
            r'\bb+i+t+c+h+\w*',
            r'\bf+\*+',
            r'\bs+\*+',
            r'f\W*u\W*c\W*k',
            r's\W*h\W*i\W*t',
        ]
        
        # Personal information patterns
        self._personal_info_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
            r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # Phone number with parentheses
        ]
        
        # Malicious input patterns
        self._malicious_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'javascript:',
            r'sql\s+injection',
            r'union\s+select',
            r'drop\s+table',
            r'insert\s+into',
            r'delete\s+from',
            r'exec\s*\(',
            r'eval\s*\(',
            r'system\s*\(',
        ]
        
        # Spam patterns
        self._spam_patterns = [
            r'(.)\1{8,}',  # Repeated characters (increased threshold)
            r'[A-Z]{16,}',  # All caps very long strings (increased threshold to avoid flagging place names)
            r'(\w+\s+){25,}',  # Excessive repetition (increased threshold)
            r'\b(\w+)\s+\1\s+\1\s+\1\b',  # Same word repeated 4+ times in a row
        ]
        
        # Hate speech keywords (basic list - should be expanded based on needs)
        self._hate_speech_words = {
            'nazi', 'terrorist', 'kill', 'murder', 'die', 'hate', 'stupid'
        }
        
        # Compile regex patterns for efficiency
        self._compiled_profanity = [re.compile(pattern, re.IGNORECASE) for pattern in self._profanity_patterns]
        self._compiled_personal_info = [re.compile(pattern) for pattern in self._personal_info_patterns]
        self._compiled_malicious = [re.compile(pattern, re.IGNORECASE) for pattern in self._malicious_patterns]
        self._compiled_spam = [re.compile(pattern, re.IGNORECASE) for pattern in self._spam_patterns]
    
    def filter_inappropriate_content(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Filter inappropriate content from text.
        
        Args:
            text (str): The input text to filter
            
        Returns:
            Tuple[bool, str, Optional[str]]: (is_appropriate, filtered_text, reason)
                - is_appropriate: True if content is appropriate
                - filtered_text: The text with inappropriate content filtered
                - reason: Reason for filtering (None if appropriate)
        """
        if not text or not isinstance(text, str):
            return True, text or "", None
        
        # Normalize the text
        normalized_text = self._normalize_text(text)
        filtered_text = text
        
        # Check for profanity
        is_profane, profane_reason = self._check_profanity(normalized_text)
        if is_profane:
            filtered_text = self._filter_profanity(filtered_text)
            self._log_filtered_content(text, InappropriateType.PROFANITY, profane_reason)
            return False, filtered_text, profane_reason
        
        # Check for personal information
        has_personal_info, personal_reason = self._check_personal_info(text)
        if has_personal_info:
            filtered_text = self._filter_personal_info(filtered_text)
            self._log_filtered_content(text, InappropriateType.PERSONAL_INFO, personal_reason)
            return False, filtered_text, personal_reason
        
        # Check for malicious input
        is_malicious, malicious_reason = self._check_malicious_input(normalized_text)
        if is_malicious:
            filtered_text = self._filter_malicious_input(filtered_text)
            self._log_filtered_content(text, InappropriateType.MALICIOUS_INPUT, malicious_reason)
            return False, filtered_text, malicious_reason
        
        # Check for spam
        is_spam, spam_reason = self._check_spam(text)
        if is_spam:
            filtered_text = self._filter_spam(filtered_text)
            self._log_filtered_content(text, InappropriateType.SPAM, spam_reason)
            return False, filtered_text, spam_reason
        
        # Check for hate speech
        has_hate_speech, hate_reason = self._check_hate_speech(normalized_text)
        if has_hate_speech:
            filtered_text = self._filter_hate_speech(filtered_text)
            self._log_filtered_content(text, InappropriateType.HATE_SPEECH, hate_reason)
            return False, filtered_text, hate_reason
        
        return True, filtered_text, None
    
    def sanitize_for_api(self, text: str) -> str:
        """
        Sanitize text for safe API consumption.
        
        Args:
            text (str): The input text to sanitize
            
        Returns:
            str: Sanitized text safe for API calls
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove control characters
        sanitized = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        # Limit length to prevent API overload
        max_length = 2000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        # Remove potentially harmful patterns
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def get_appropriate_response(self, inappropriate_type: InappropriateType) -> str:
        """
        Get an appropriate response for filtered content.
        
        Args:
            inappropriate_type (InappropriateType): The type of inappropriate content
            
        Returns:
            str: An appropriate response message
        """
        responses = {
            InappropriateType.PROFANITY: (
                "I get that travel planning can be frustrating sometimes! Let's keep things "
                "friendly though. How can I help make your trip planning easier?"
            ),
            InappropriateType.PERSONAL_INFO: (
                "Just a heads up - I noticed some personal info there. For your security, I won't "
                "use that. Let me help you book your trip safely though!"
            ),
            InappropriateType.MALICIOUS_INPUT: (
                "That's some unusual input that I can't work with. No worries though - "
                "just tell me how I can help you with your travel plans!"
            ),
            InappropriateType.INAPPROPRIATE_NAME: (
                "I'll need your actual name for the booking - the one that matches your ID. "
                "What name should I put on your ticket?"
            ),
            InappropriateType.SPAM: (
                "I'm seeing some repetitive stuff there. Could you rephrase that "
                "so I know how to help you?"
            ),
            InappropriateType.HATE_SPEECH: (
                "Let's keep things friendly and focus on getting you where you need to go. "
                "How can I help with your travel today?"
            )
        }
        
        return responses.get(inappropriate_type, 
                           "I'm here to make your travel planning easy! How can I help you?")
    
    def is_valid_name(self, name: str) -> bool:
        """
        Validate if a name is appropriate for booking purposes.
        
        Args:
            name (str): The name to validate
            
        Returns:
            bool: True if the name is valid and appropriate
        """
        if not name or not isinstance(name, str):
            return False
        
        # Basic length check
        if len(name.strip()) < 1 or len(name.strip()) > 100:
            return False
        
        # Check for inappropriate content
        is_appropriate, _, reason = self.filter_inappropriate_content(name)
        if not is_appropriate:
            return False
        
        # Check for valid name patterns
        # Names should contain only letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name.strip()):
            return False
        
        # Check for obviously fake names
        fake_names = ['test', 'testing', 'dummy', 'fake', 'xxx', 'na', 'none', 'null']
        normalized_name = name.lower().strip()
        
        # Check against fake name list
        if normalized_name in fake_names:
            return False
        
        # Check for repeated characters (like "aaaaaa")
        if re.match(r'^(.)\1{5,}$', normalized_name):
            return False
        
        # Check if it's just numbers
        if re.match(r'^\d+$', name.strip()):
            return False
        
        # Valid name
        return True
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent filtering."""
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove excessive punctuation and special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _check_profanity(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check for profanity in text."""
        # Check word list
        words = text.split()
        for word in words:
            if word in self._profanity_words:
                return True, f"Profanity detected: inappropriate language"
        
        # Check regex patterns
        for pattern in self._compiled_profanity:
            if pattern.search(text):
                return True, f"Profanity detected: pattern match"
        
        return False, None
    
    def _check_personal_info(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check for personal information in text."""
        for pattern in self._compiled_personal_info:
            if pattern.search(text):
                return True, "Personal information detected"
        return False, None
    
    def _check_malicious_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check for malicious input patterns."""
        for pattern in self._compiled_malicious:
            if pattern.search(text):
                return True, "Potentially malicious input detected"
        return False, None
    
    def _check_spam(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check for spam patterns."""
        for pattern in self._compiled_spam:
            if pattern.search(text):
                return True, "Spam-like content detected"
        return False, None
    
    def _check_hate_speech(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check for hate speech."""
        words = text.split()
        for word in words:
            if word in self._hate_speech_words:
                return True, "Potentially inappropriate language detected"
        return False, None
    
    def _filter_profanity(self, text: str) -> str:
        """Filter profanity from text."""
        filtered = text
        
        # Replace profane words
        for word in self._profanity_words:
            filtered = re.sub(re.escape(word), '[filtered]', filtered, flags=re.IGNORECASE)
        
        # Replace pattern matches
        for pattern in self._compiled_profanity:
            filtered = pattern.sub('[filtered]', filtered)
        
        return filtered
    
    def _filter_personal_info(self, text: str) -> str:
        """Filter personal information from text."""
        filtered = text
        for pattern in self._compiled_personal_info:
            filtered = pattern.sub('[REDACTED]', filtered)
        return filtered
    
    def _filter_malicious_input(self, text: str) -> str:
        """Filter malicious input from text."""
        filtered = text
        for pattern in self._compiled_malicious:
            filtered = pattern.sub('[BLOCKED]', filtered)
        return filtered
    
    def _filter_spam(self, text: str) -> str:
        """Filter spam content from text."""
        # Remove excessive repetition
        filtered = re.sub(r'(.)\1{3,}', r'\1\1\1', text)
        # Normalize excessive caps
        filtered = re.sub(r'[A-Z]{5,}', lambda m: m.group().capitalize(), filtered)
        return filtered
    
    def _filter_hate_speech(self, text: str) -> str:
        """Filter hate speech from text."""
        filtered = text
        for word in self._hate_speech_words:
            filtered = re.sub(r'\b' + re.escape(word) + r'\b', '[filtered]', filtered, flags=re.IGNORECASE)
        return filtered
    
    def _log_filtered_content(self, original_text: str, content_type: InappropriateType, reason: str):
        """Log filtered content for debugging and monitoring."""
        self.logger.warning(
            f"Content filtered - Type: {content_type.value}, "
            f"Reason: {reason}, "
            f"Original length: {len(original_text)}, "
            f"Preview: {original_text[:50]}..."
        )


# Convenience function for quick filtering
def quick_filter(text: str) -> Tuple[bool, str]:
    """
    Quick content filtering function.
    
    Args:
        text (str): Text to filter
        
    Returns:
        Tuple[bool, str]: (is_appropriate, filtered_text)
    """
    filter_instance = ContentFilter()
    is_appropriate, filtered_text, _ = filter_instance.filter_inappropriate_content(text)
    return is_appropriate, filtered_text


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create filter instance
    content_filter = ContentFilter()
    
    # Test cases
    test_cases = [
        "Hello, I'd like to book a flight to New York",
        "My name is F*** Q and I want a ticket",
        "Call me at 555-123-4567 for booking details",
        "This is a f***ing terrible service!",
        "My email is user@example.com",
        "AAAAAAAAAAAAAAAAAAAAAAAAA",
        "John Smith",
        "Test User",
        "a",
        "1234567890",
    ]
    
    print("Content Filter Test Results:")
    print("=" * 50)
    
    for test_text in test_cases:
        is_appropriate, filtered_text, reason = content_filter.filter_inappropriate_content(test_text)
        is_valid_name = content_filter.is_valid_name(test_text)
        
        print(f"\nInput: '{test_text}'")
        print(f"Appropriate: {is_appropriate}")
        print(f"Valid Name: {is_valid_name}")
        if not is_appropriate:
            print(f"Reason: {reason}")
            print(f"Filtered: '{filtered_text}'")
            print(f"Response: {content_filter.get_appropriate_response(InappropriateType.PROFANITY)}")