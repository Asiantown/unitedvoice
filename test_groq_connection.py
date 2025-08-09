#!/usr/bin/env python3
"""
Test script to verify Groq API connection and quota with the provided API key
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

# The API key from Railway
RAILWAY_GROQ_KEY = "YOUR_GROQ_API_KEY_HERE"  # Replace with actual key

def test_direct_api_call():
    """Test direct API call to Groq"""
    print("🔗 TESTING DIRECT GROQ API CONNECTION")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {RAILWAY_GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test LLM endpoint
    print("\n🤖 Testing LLM endpoint...")
    payload = {
        "model": "gemma2-9b-it",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ LLM API SUCCESS")
            print(f"Response: {result['choices'][0]['message']['content']}")
            if 'usage' in result:
                print(f"Usage: {result['usage']}")
        else:
            print("❌ LLM API FAILED")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ LLM API Exception: {e}")
        return False
    
    # Test Whisper endpoint
    print("\n🎤 Testing Whisper endpoint...")
    
    # Create a small test audio file
    import wave
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        with wave.open(tmp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # Write 0.5 seconds of silence
            wav_file.writeframes(b'\x00\x00' * 8000)
        
        tmp_path = tmp_file.name
    
    try:
        with open(tmp_path, 'rb') as audio_file:
            files = {
                'file': ('test.wav', audio_file, 'audio/wav'),
                'model': (None, 'whisper-large-v3-turbo'),
                'language': (None, 'en')
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {RAILWAY_GROQ_KEY}"},
                files=files,
                timeout=30
            )
            
            print(f"Whisper Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Whisper API SUCCESS")
                print(f"Transcription: '{response.text.strip()}'")
            else:
                print("❌ Whisper API FAILED")
                print(f"Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Whisper API Exception: {e}")
        return False
    finally:
        os.unlink(tmp_path)
    
    return True

def test_quota_limits():
    """Test quota and rate limits"""
    print("\n📊 TESTING QUOTA AND RATE LIMITS")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {RAILWAY_GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    # Make multiple requests to test rate limiting
    for i in range(5):
        print(f"\nRequest {i+1}/5...")
        
        payload = {
            "model": "gemma2-9b-it",
            "messages": [{"role": "user", "content": f"Count to {i+1}"}],
            "max_tokens": 20
        }
        
        start_time = time.time()
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        end_time = time.time()
        
        print(f"Status: {response.status_code} | Time: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result['choices'][0]['message']['content'].strip()}")
            
            # Look for usage info
            if 'usage' in result:
                usage = result['usage']
                print(f"   Tokens used: {usage.get('total_tokens', 'unknown')}")
                
        elif response.status_code == 429:
            print("❌ RATE LIMITED")
            print(f"   Response: {response.text}")
            
            # Check retry headers
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                print(f"   Retry after: {retry_after} seconds")
            break
            
        elif response.status_code == 403:
            print("❌ QUOTA EXCEEDED OR ACCESS DENIED")
            print(f"   Response: {response.text}")
            break
            
        else:
            print(f"❌ UNEXPECTED ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
        
        time.sleep(0.5)  # Small delay between requests
    
    return True

def test_with_environment():
    """Test with environment variable set"""
    print("\n🌍 TESTING WITH ENVIRONMENT VARIABLE")
    print("=" * 50)
    
    # Set the environment variable
    os.environ['GROQ_API_KEY'] = RAILWAY_GROQ_KEY
    
    print(f"Set GROQ_API_KEY in environment")
    print(f"os.getenv('GROQ_API_KEY'): {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    
    # Test our clients
    sys.path.append(str(Path(__file__).parent / 'src'))
    
    try:
        from services.groq_client import GroqClient
        from services.groq_whisper import GroqWhisperClient
        
        print("\n🤖 Testing GroqClient...")
        client = GroqClient()
        success, message = client.test_connection()
        print(f"GroqClient: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Message: {message}")
        
        print("\n🎤 Testing GroqWhisperClient...")
        whisper = GroqWhisperClient()
        success = whisper.test_connection()
        print(f"GroqWhisperClient: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Client test error: {e}")
        return False

def test_key_validity():
    """Test if the API key format is valid"""
    print("\n🔑 TESTING API KEY VALIDITY")
    print("=" * 50)
    
    key = RAILWAY_GROQ_KEY
    
    print(f"API Key: {key[:8]}...{key[-8:]}")
    print(f"Length: {len(key)} characters")
    print(f"Starts with 'gsk_': {'✅' if key.startswith('gsk_') else '❌'}")
    
    # Check if it contains only valid characters
    import re
    valid_pattern = re.match(r'^gsk_[A-Za-z0-9]+$', key)
    print(f"Valid format: {'✅' if valid_pattern else '❌'}")
    
    if len(key) < 20:
        print("⚠️  WARNING: API key seems too short")
    elif len(key) > 100:
        print("⚠️  WARNING: API key seems too long")
    
    return bool(valid_pattern)

def create_fallback_config():
    """Create configuration for fallback mechanisms"""
    print("\n🛡️ CREATING FALLBACK CONFIGURATION")
    print("=" * 50)
    
    fallback_config = {
        "groq_available": False,
        "fallback_modes": {
            "stt": "mock",  # Use mock transcription
            "llm": "simple_responses",  # Use predefined responses
            "error_handling": "graceful"
        },
        "mock_responses": {
            "transcription_unavailable": "Sorry, I'm having trouble hearing you right now. Could you type your request instead?",
            "llm_unavailable": "I'm experiencing some technical difficulties. Let me help you with basic flight information.",
            "quota_exceeded": "Our voice system is temporarily at capacity. You can still book flights through our website at united.com"
        },
        "recovery_strategies": [
            "Retry API calls with exponential backoff",
            "Switch to mock data for demonstrations", 
            "Provide clear error messages to users",
            "Maintain core booking functionality without AI"
        ]
    }
    
    config_file = "groq_fallback_config.json"
    with open(config_file, 'w') as f:
        json.dump(fallback_config, f, indent=2)
    
    print(f"📁 Fallback config saved to: {config_file}")
    return fallback_config

def main():
    """Main test function"""
    print("🧪 GROQ API COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"Testing with Railway API key: {RAILWAY_GROQ_KEY[:8]}...{RAILWAY_GROQ_KEY[-4:]}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Key validity
    results['key_valid'] = test_key_validity()
    
    # Test 2: Direct API calls
    results['api_direct'] = test_direct_api_call()
    
    # Test 3: Quota limits
    if results['api_direct']:
        results['quota_ok'] = test_quota_limits()
    else:
        results['quota_ok'] = False
    
    # Test 4: Environment variable usage
    results['env_test'] = test_with_environment()
    
    # Test 5: Create fallback config
    fallback_config = create_fallback_config()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    print(f"🔑 API Key Valid: {'✅' if results['key_valid'] else '❌'}")
    print(f"🔗 Direct API Test: {'✅' if results['api_direct'] else '❌'}")
    print(f"📊 Quota Test: {'✅' if results['quota_ok'] else '❌'}")
    print(f"🌍 Environment Test: {'✅' if results['env_test'] else '❌'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Groq API key is working correctly.")
        
    else:
        print("\n⚠️  SOME TESTS FAILED")
        
        if not results['key_valid']:
            print("   - API key format is invalid")
            
        if not results['api_direct']:
            print("   - Cannot connect to Groq API")
            print("   - This could be due to:")
            print("     * Network connectivity issues")
            print("     * Invalid API key")
            print("     * Groq service downtime")
            
        if not results['quota_ok']:
            print("   - Quota or rate limit issues detected")
            print("   - Check your Groq account at https://console.groq.com/")
            
        if not results['env_test']:
            print("   - Environment variable integration issues")
    
    print("\n💡 RECOMMENDATIONS:")
    if not all_passed:
        print("   - Implement fallback mechanisms for production")
        print("   - Add comprehensive error logging")
        print("   - Use mock data when API is unavailable")
        print("   - Monitor API usage and quotas")
    
    print("   - Set GROQ_API_KEY in Railway environment variables")
    print("   - Test the debug script in production: python debug_groq_env.py")
    print("   - Monitor logs for environment variable availability")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)