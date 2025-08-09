#!/usr/bin/env python3
"""
Test the new GROQ API key provided by the user
"""

import os
import json
import requests
from groq import Groq

# The new API key to test
NEW_GROQ_KEY = os.getenv('GROQ_API_KEY', 'YOUR_GROQ_API_KEY_HERE')

def test_groq_api_key():
    """Test if the new GROQ API key is valid"""
    print("🔑 Testing new GROQ API key...")
    print(f"   Key: {NEW_GROQ_KEY[:20]}...{NEW_GROQ_KEY[-4:]}")
    print()
    
    # Test 1: Direct API call
    print("📡 Test 1: Direct API Call")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {NEW_GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": "Say 'API key is valid'"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API Key is VALID!")
            data = response.json()
            if 'choices' in data and data['choices']:
                print(f"   Response: {data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"   ❌ API Key is INVALID")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    
    print()

def test_groq_client():
    """Test using the Groq Python client"""
    print("🐍 Test 2: Groq Python Client")
    print("-" * 40)
    
    try:
        client = Groq(api_key=NEW_GROQ_KEY)
        
        # Test transcription capability
        print("   Testing chat completion...")
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Reply with 'Success'"}],
            max_tokens=10
        )
        
        print(f"   ✅ Client works!")
        print(f"   Response: {completion.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"   ❌ Client Error: {e}")
        return False
    
    print()

def test_whisper_transcription():
    """Test if Whisper transcription works with this key"""
    print("🎤 Test 3: Whisper Transcription Support")
    print("-" * 40)
    
    try:
        from src.services.groq_whisper import GroqWhisperClient
        
        # Set the API key in environment
        os.environ['GROQ_API_KEY'] = NEW_GROQ_KEY
        
        # Initialize client
        client = GroqWhisperClient(api_key=NEW_GROQ_KEY)
        
        # Test connection
        success, message = client.test_connection()
        
        if success:
            print(f"   ✅ Whisper client ready!")
            print(f"   {message}")
        else:
            print(f"   ❌ Whisper client failed")
            print(f"   {message}")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Whisper Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("🧪 GROQ API KEY VALIDATION TEST")
    print("=" * 50)
    print()
    
    # Run tests
    api_valid = test_groq_api_key()
    print()
    
    client_valid = test_groq_client()
    print()
    
    whisper_valid = test_whisper_transcription()
    print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if api_valid and client_valid:
        print("✅ The new GROQ API key is VALID and WORKING!")
        print()
        print("📝 Next Steps:")
        print("1. Update this key in Railway environment variables:")
        print(f"   GROQ_API_KEY={NEW_GROQ_KEY}")
        print()
        print("2. Railway will automatically redeploy")
        print()
        print("3. Your voice transcription will work! 🎉")
    else:
        print("❌ The API key has issues")
        print("   Please check if the key is correct or if it has quota")
    
    print("=" * 50)

if __name__ == "__main__":
    main()