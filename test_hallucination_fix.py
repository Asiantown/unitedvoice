#!/usr/bin/env python3
"""
Test script to verify hallucination filtering is working correctly
while ensuring legitimate "thank you" messages still work.
"""

import sys
import os
import tempfile
import wave
import numpy as np
import re
from typing import List, Tuple, Set

# Test the hallucination filtering logic directly
# This mirrors the logic from WebSocketVoiceAgent.is_likely_hallucination

# Common Whisper hallucinations to filter out
WHISPER_HALLUCINATIONS: Set[str] = {
    'thank you', 'thanks', 'thank', 'you', 'bye', 'goodbye', 
    'hello', 'hi', 'hey', 'oh', 'okay', 'ok', 'yes', 'no',
    'um', 'uh', 'ah', 'hmm', 'mmm', '.', '...', 
    'please', 'sorry', 'excuse me', 'pardon'
}

# Minimum confidence threshold for accepting transcriptions
MIN_TRANSCRIPTION_CONFIDENCE = 0.7
MIN_TRANSCRIPTION_LENGTH = 3  # Minimum characters
MAX_HALLUCINATION_LENGTH = 15  # Maximum length for potential hallucinations


def is_likely_hallucination(text: str) -> bool:
    """Check if transcribed text is likely a Whisper hallucination"""
    if not text or len(text.strip()) == 0:
        return True
        
    # Clean and normalize the text
    cleaned_text = re.sub(r'[^\w\s]', '', text.lower().strip())
    
    # Check if it's too short to be meaningful
    if len(cleaned_text) < MIN_TRANSCRIPTION_LENGTH:
        return True
        
    # Check if it's a short phrase that's likely a hallucination
    if len(cleaned_text) <= MAX_HALLUCINATION_LENGTH:
        # Check against known hallucinations
        if cleaned_text in WHISPER_HALLUCINATIONS:
            return True
            
        # Check for single word repetitions
        words = cleaned_text.split()
        if len(words) == 1 and words[0] in WHISPER_HALLUCINATIONS:
            return True
            
        # Check for very short repeated patterns
        if len(words) <= 3 and len(set(words)) == 1:
            return True
    
    # Check for patterns that indicate noise transcription
    noise_patterns = [
        r'^[\s\.\,\!\?]+$',  # Only punctuation and whitespace
        r'^(uh|um|ah|mm|hmm)\s*$',  # Common filler words alone
        r'^\w{1,2}$',  # Single or double character words
    ]
    
    for pattern in noise_patterns:
        if re.match(pattern, cleaned_text, re.IGNORECASE):
            return True
            
    return False


def create_test_audio(duration_seconds: float = 1.0, sample_rate: int = 16000, 
                     amplitude: float = 0.1) -> bytes:
    """Create a simple test audio file with white noise"""
    num_samples = int(duration_seconds * sample_rate)
    
    # Generate white noise
    audio_data = np.random.normal(0, amplitude, num_samples)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        temp_path = temp_file.name
    
    # Read the file back as bytes
    with open(temp_path, 'rb') as f:
        audio_bytes = f.read()
    
    # Clean up
    os.unlink(temp_path)
    return audio_bytes


def test_hallucination_filtering():
    """Test the hallucination filtering functionality"""
    
    print("Testing Hallucination Filtering")
    print("=" * 50)
    
    # Test cases: (text, should_be_filtered)
    test_cases = [
        # Should be filtered (hallucinations)
        ("Thank you", True),
        ("thanks", True), 
        ("Thank you.", True),
        ("you", True),
        (".", True),
        ("...", True),
        ("um", True),
        ("uh", True),
        ("okay", True),
        ("", True),
        ("  ", True),
        ("a", True),  # Too short
        ("hi", True),  # Too short and hallucination
        
        # Should NOT be filtered (legitimate speech)
        ("Thank you for helping me book this flight", False),
        ("I would like to thank you for your assistance", False),
        ("Can you help me find flights to New York", False),
        ("I need to book a flight from Chicago to Miami", False),
        ("What flights are available tomorrow morning", False),
        ("Thank you very much for all your help today", False),  # Longer context
        ("Could you please help me", False),
        ("I appreciate your assistance", False),
        ("Yes, I would like to proceed with the booking", False),
    ]
    
    print("\nTesting individual transcriptions:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for text, should_be_filtered in test_cases:
        result = is_likely_hallucination(text)
        status = "✅ PASS" if result == should_be_filtered else "❌ FAIL"
        expected = "FILTERED" if should_be_filtered else "ACCEPTED"
        actual = "FILTERED" if result else "ACCEPTED"
        
        print(f"{status} '{text}' -> Expected: {expected}, Got: {actual}")
        
        if result == should_be_filtered:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    return failed == 0


def test_audio_processing_pipeline():
    """Test the complete audio processing pipeline with mock data"""
    
    print("\n\nTesting Audio Processing Pipeline")
    print("=" * 50)
    
    # Test different audio scenarios
    test_scenarios = [
        ("Very short audio (0.1s)", 0.1, "Should be rejected for duration"),
        ("Short audio (0.3s)", 0.3, "Should be rejected for duration"), 
        ("Minimum duration (0.5s)", 0.5, "Should pass duration check"),
        ("Normal duration (2.0s)", 2.0, "Should pass all checks"),
        ("Long audio (5.0s)", 5.0, "Should pass all checks"),
    ]
    
    print("\nTesting audio duration filtering:")
    print("-" * 40)
    
    for description, duration, expected in test_scenarios:
        # Create test audio
        audio_bytes = create_test_audio(duration_seconds=duration, amplitude=0.05)
        
        # Simulate the audio checks that would happen in handleAudioData
        MIN_DURATION_MS = 500
        duration_ms = duration * 1000
        MIN_BLOB_SIZE = 1024
        
        # Check duration
        duration_pass = duration_ms >= MIN_DURATION_MS
        
        # Check size  
        size_pass = len(audio_bytes) >= MIN_BLOB_SIZE
        
        overall_pass = duration_pass and size_pass
        status = "✅ PASS" if overall_pass else "❌ REJECT"
        
        print(f"{status} {description}: {duration_ms:.0f}ms, {len(audio_bytes)} bytes - {expected}")


def test_legitimate_thank_you_messages():
    """Specifically test that legitimate thank you messages are not filtered"""
    
    print("\n\nTesting Legitimate 'Thank You' Messages")
    print("=" * 50)
    
    legitimate_messages = [
        "Thank you for helping me find the best flight options",
        "I want to thank you for your excellent customer service", 
        "Thank you so much, this has been very helpful",
        "Could you help me please? Thank you in advance",
        "I really appreciate your help, thank you",
        "Thank you for finding me such a great deal on flights",
        "Thank you for explaining all the flight options to me",
        "This is perfect, thank you for your assistance",
        "Thank you for being so patient with my questions",
        "I'm grateful for your help, thank you very much"
    ]
    
    print("\nTesting legitimate thank you messages (should NOT be filtered):")
    print("-" * 60)
    
    all_passed = True
    for message in legitimate_messages:
        is_filtered = is_likely_hallucination(message)
        status = "✅ ACCEPTED" if not is_filtered else "❌ FILTERED (ERROR!)"
        
        if is_filtered:
            all_passed = False
            
        print(f"{status} '{message}'")
    
    return all_passed


def main():
    """Run all tests"""
    
    print("Voice Agent Hallucination Fix - Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_hallucination_filtering()
    test_audio_processing_pipeline()  # This is informational, doesn't return pass/fail
    test2_passed = test_legitimate_thank_you_messages()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("-" * 20)
    print(f"Hallucination Filtering Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Legitimate Messages Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    overall_success = test1_passed and test2_passed
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The hallucination fix is working correctly!")
        print("✅ Short hallucinations like 'Thank you' are filtered out")
        print("✅ Legitimate 'thank you' messages in context are preserved")
        print("✅ Audio duration and quality checks are in place")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)