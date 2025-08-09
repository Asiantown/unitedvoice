#!/usr/bin/env python3
"""Direct test of pyttsx3 audio generation"""

import pyttsx3
import tempfile
import os
from pydub import AudioSegment
import base64

def test_pyttsx3():
    print("Testing pyttsx3 directly...")
    
    # Initialize engine
    engine = pyttsx3.init()
    
    # List available voices
    voices = engine.getProperty('voices')
    print(f"Available voices: {len(voices)}")
    for i, voice in enumerate(voices[:3]):  # Show first 3
        print(f"  {i}: {voice.name}")
    
    # Set properties
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    
    # Use first available voice
    if voices:
        engine.setProperty('voice', voices[0].id)
        print(f"Using voice: {voices[0].name}")
    
    text = "Hello! This is a test of the text to speech system. Can you hear me clearly?"
    
    # Save to file
    with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as f:
        temp_aiff = f.name
    
    print(f"Saving to: {temp_aiff}")
    engine.save_to_file(text, temp_aiff)
    engine.runAndWait()
    
    # Check file size
    if os.path.exists(temp_aiff):
        size = os.path.getsize(temp_aiff)
        print(f"AIFF file size: {size} bytes")
        
        if size > 1000:  # Should be larger than 1KB for real audio
            # Convert to MP3
            print("Converting to MP3...")
            audio = AudioSegment.from_file(temp_aiff, format="aiff")
            
            # Check audio properties
            print(f"  Duration: {len(audio)}ms")
            print(f"  Channels: {audio.channels}")
            print(f"  Frame rate: {audio.frame_rate}")
            print(f"  Sample width: {audio.sample_width}")
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_mp3 = f.name
            
            audio.export(temp_mp3, format="mp3", bitrate="128k")
            
            mp3_size = os.path.getsize(temp_mp3)
            print(f"MP3 file size: {mp3_size} bytes")
            
            # Read and encode
            with open(temp_mp3, 'rb') as f:
                mp3_bytes = f.read()
            
            # Check header
            print(f"MP3 header: {mp3_bytes[:4].hex()}")
            
            # Play it
            print(f"\nTo test the audio, run:")
            print(f"  afplay {temp_mp3}")
            
            return temp_mp3
        else:
            print("❌ File too small - likely empty/silent")
    else:
        print("❌ File not created")
    
    return None

if __name__ == "__main__":
    mp3_file = test_pyttsx3()
    if mp3_file:
        print(f"\n✅ Success! Audio file: {mp3_file}")
        # Try to play it
        os.system(f"afplay {mp3_file}")
    else:
        print("\n❌ Failed to generate audio")