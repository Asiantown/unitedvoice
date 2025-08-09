#!/usr/bin/env python3
"""
Speech Recognition Correction Utilities
Handles common speech-to-text mishearings and provides fuzzy matching for travel terms
"""

import difflib
import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TravelTermsCorrector:
    """Corrects common speech recognition errors for travel-related terms"""
    
    def __init__(self):
        # Common speech recognition mishearings for travel terms
        self.travel_mishearings = {
            # Trip type mishearings
            'phone trip': 'round trip',
            'found trip': 'round trip', 
            'run trip': 'round trip',
            'road trip': 'round trip',  
            'ground trip': 'round trip',
            'brown trip': 'round trip',
            'sound trip': 'round trip',
            'bound trip': 'round trip',
            'pound trip': 'round trip',
            'round chip': 'round trip',
            'round dip': 'round trip',
            'round grip': 'round trip',
            'around trip': 'round trip',
            'round strip': 'round trip',
            'one day': 'one way',
            'one we': 'one way', 
            'won way': 'one way',
            'when way': 'one way',
            'on way': 'one way',
            'own way': 'one way',
            'one weigh': 'one way',
            'one whey': 'one way',
            'juan way': 'one way',
            'one bay': 'one way',
            'one may': 'one way',
            
            # Time-related mishearings
            'morning': 'morning',  # Keep correct
            'mourning': 'morning',
            'warning': 'morning',  # Contextual
            'evening': 'evening',  # Keep correct
            'even in': 'evening',
            'have an ing': 'evening',
            'afternoon': 'afternoon',  # Keep correct
            'after noon': 'afternoon',
            'after new': 'afternoon',
            
            # Common city mishearings (examples)
            'san fran': 'san francisco',
            'sfo': 'san francisco',
            'nyc': 'new york',
            'ny': 'new york',
            'la': 'los angeles',
            'lax': 'los angeles',
            'vegas': 'las vegas',
            'philly': 'philadelphia',
            'chi town': 'chicago',
            'windy city': 'chicago',
        }
        
        # Phonetic patterns for regex-based corrections
        self.phonetic_patterns = [
            # Phone trip variations
            (r'\bfo?o?ne? trip\b', 'round trip'),
            (r'\bfound? trip\b', 'round trip'),
            (r'\brun trip\b', 'round trip'),
            
            # One day/way variations  
            (r'\bone da[wy]\b', 'one way'),
            (r'\bwon wa[wy]\b', 'one way'),
            (r'\bon wa[wy]\b', 'one way'),
        ]
    
    def correct_travel_terms(self, text: str, confidence_threshold: float = 0.6) -> Tuple[str, bool]:
        """
        Apply corrections to travel-related terms in text
        
        Args:
            text: Input text to correct
            confidence_threshold: Minimum similarity score for fuzzy matching
            
        Returns:
            Tuple of (corrected_text, was_corrected)
        """
        original_text = text
        text = text.lower().strip()
        corrected = False
        
        # First pass: exact phrase replacements (with word boundaries to avoid substring issues)
        for mishearing, correction in self.travel_mishearings.items():
            # Use word boundary regex to avoid partial matches like "round trip" in "ground trip"  
            pattern = r'\b' + re.escape(mishearing) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, correction, text, flags=re.IGNORECASE)
                corrected = True
                logger.info(f"Applied exact correction: '{mishearing}' -> '{correction}'")
        
        # Second pass: phonetic pattern replacements
        for pattern, replacement in self.phonetic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                corrected = True
                logger.info(f"Applied pattern correction: '{pattern}' -> '{replacement}'")
        
        # Third pass: fuzzy matching for individual words
        words = text.split()
        corrected_words = []
        
        for word in words:
            best_match = word
            best_score = 0.0
            
            # Check against all known corrections
            for mishearing in self.travel_mishearings.keys():
                mishearing_words = mishearing.split()
                
                # Single word fuzzy matching
                if len(mishearing_words) == 1:
                    similarity = difflib.SequenceMatcher(None, word, mishearing_words[0]).ratio()
                    if similarity > confidence_threshold and similarity > best_score:
                        correction = self.travel_mishearings[mishearing]
                        if ' ' not in correction:  # Single word correction
                            best_match = correction
                            best_score = similarity
                            corrected = True
                            logger.info(f"Applied fuzzy correction: '{word}' -> '{correction}' (score: {similarity:.2f})")
            
            corrected_words.append(best_match)
        
        # Fourth pass: multi-word phrase fuzzy matching
        corrected_text = ' '.join(corrected_words)
        for mishearing, correction in self.travel_mishearings.items():
            if len(mishearing.split()) > 1:  # Multi-word phrases only
                similarity = difflib.SequenceMatcher(None, corrected_text, mishearing).ratio()
                if similarity > confidence_threshold:
                    corrected_text = correction
                    corrected = True
                    logger.info(f"Applied phrase fuzzy correction: '{text}' -> '{correction}' (score: {similarity:.2f})")
                    break
        
        return corrected_text, corrected
    
    def correct_trip_type(self, text: str) -> Tuple[str, bool]:
        """
        Specialized correction for trip type terms
        
        Args:
            text: Input text containing potential trip type
            
        Returns:
            Tuple of (corrected_text, was_corrected)
        """
        # Focus only on trip type corrections
        trip_type_terms = {
            mishearing: correction 
            for mishearing, correction in self.travel_mishearings.items()
            if 'trip' in correction or 'way' in correction
        }
        
        original_text = text
        text = text.lower().strip()
        corrected = False
        
        # Exact replacements
        for mishearing, correction in trip_type_terms.items():
            if mishearing in text:
                text = text.replace(mishearing, correction)
                corrected = True
                logger.info(f"Applied trip type correction: '{mishearing}' -> '{correction}'")
        
        # Phonetic patterns for trip types
        trip_patterns = [
            (r'\b(?:phone|fo+ne?|found?|run|road|ground|brown|sound|bound|pound)\s+trip\b', 'round trip'),
            (r'\bround\s+(?:chip|dip|grip|strip)\b', 'round trip'),
            (r'\b(?:one|won|when|on|own)\s+(?:day|we|wa[wy]|weigh|whey|bay|may)\b', 'one way'),
        ]
        
        for pattern, replacement in trip_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                corrected = True
                logger.info(f"Applied trip type pattern correction: '{pattern}' -> '{replacement}'")
        
        return text, corrected
    
    def suggest_corrections(self, text: str, max_suggestions: int = 3) -> List[str]:
        """
        Generate correction suggestions for unclear input
        
        Args:
            text: Input text
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggested corrections
        """
        suggestions = []
        text_lower = text.lower().strip()
        
        # Get fuzzy matches
        travel_terms = list(self.travel_mishearings.values())
        matches = difflib.get_close_matches(
            text_lower, 
            travel_terms, 
            n=max_suggestions, 
            cutoff=0.4
        )
        
        return matches


# Singleton instance for easy access
travel_corrector = TravelTermsCorrector()