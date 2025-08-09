#!/usr/bin/env python3
"""
Test ElevenLabs API configuration
"""

import os
import requests

def test_elevenlabs():
    """Test ElevenLabs API key and connection"""
    print("🎤 Testing ElevenLabs Text-to-Speech")
    print("=" * 50)
    
    # Check environment variable
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("   Add it to Railway Variables tab")
        return False
    
    print(f"📝 Found API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Check if it's actually a GROQ key
    if api_key.startswith('gsk_'):
        print("⚠️  WARNING: This looks like a GROQ API key, not ElevenLabs!")
        print("   ElevenLabs keys usually start with 'xi_' or 'sk_'")
        print()
        print("📝 To fix:")
        print("   1. Get your ElevenLabs API key from https://elevenlabs.io/api")
        print("   2. Update ELEVENLABS_API_KEY in Railway Variables")
        return False
    
    # Test the API
    print("\n🔗 Testing ElevenLabs API connection...")
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Test voices endpoint
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ ElevenLabs API key is VALID!")
            data = response.json()
            if 'voices' in data:
                print(f"   Available voices: {len(data['voices'])}")
                for voice in data['voices'][:3]:
                    print(f"     - {voice.get('name', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("   ❌ Invalid API key")
            print(f"   Error: {response.text}")
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
    
    return False

def check_quota():
    """Check ElevenLabs usage quota"""
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if not api_key or api_key.startswith('gsk_'):
        return
    
    print("\n📊 Checking ElevenLabs Quota...")
    
    headers = {"xi-api-key": api_key}
    
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            subscription = data.get('subscription', {})
            
            character_count = subscription.get('character_count', 0)
            character_limit = subscription.get('character_limit', 0)
            
            if character_limit > 0:
                usage_percent = (character_count / character_limit) * 100
                print(f"   Characters used: {character_count:,} / {character_limit:,} ({usage_percent:.1f}%)")
                
                if usage_percent > 90:
                    print("   ⚠️  WARNING: Quota almost exhausted!")
                elif usage_percent > 99:
                    print("   ❌ QUOTA EXHAUSTED - TTS will not work!")
            else:
                print(f"   Characters used: {character_count:,}")
                
    except Exception as e:
        print(f"   Error checking quota: {e}")

def main():
    """Run all tests"""
    print("=" * 50)
    print("🧪 ELEVENLABS CONFIGURATION TEST")
    print("=" * 50)
    print()
    
    valid = test_elevenlabs()
    
    if valid:
        check_quota()
    
    print("\n" + "=" * 50)
    print("📝 SUMMARY")
    print("=" * 50)
    
    if not valid:
        print("❌ ElevenLabs is NOT configured properly")
        print()
        print("To get ElevenLabs working:")
        print("1. Sign up at https://elevenlabs.io")
        print("2. Get your API key from https://elevenlabs.io/api")
        print("3. Add to Railway Variables:")
        print("   ELEVENLABS_API_KEY=xi_your_actual_key_here")
        print()
        print("Note: Free tier gives you 10,000 characters/month")
    else:
        print("✅ ElevenLabs is configured and working!")
    
    print("=" * 50)

if __name__ == "__main__":
    main()