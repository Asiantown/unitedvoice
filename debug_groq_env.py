#!/usr/bin/env python3
"""
Debug script for GROQ_API_KEY environment variable and connection issues
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

# Import our services
try:
    from services.groq_client import GroqClient
    from services.groq_whisper import GroqWhisperClient
    from config.settings import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_environment_variables():
    """Log all environment variables and their availability"""
    print("\n" + "="*60)
    print("ENVIRONMENT VARIABLES DEBUG")
    print("="*60)
    
    # Critical API keys
    critical_keys = [
        'GROQ_API_KEY',
        'ELEVENLABS_API_KEY', 
        'SERPAPI_API_KEY'
    ]
    
    # All relevant environment variables
    all_env_vars = dict(os.environ)
    
    # Log critical keys first
    print("\n🔑 CRITICAL API KEYS:")
    for key in critical_keys:
        value = os.getenv(key)
        if value:
            # Show first/last few chars for security
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***MASKED***"
            print(f"  ✅ {key}: {masked_value} (length: {len(value)})")
        else:
            print(f"  ❌ {key}: NOT SET")
    
    # Test different methods of getting GROQ_API_KEY
    print(f"\n🔍 GROQ_API_KEY ACCESS METHODS:")
    groq_key_os = os.getenv('GROQ_API_KEY')
    groq_key_environ = os.environ.get('GROQ_API_KEY')
    groq_key_settings = settings.groq.api_key
    
    print(f"  os.getenv('GROQ_API_KEY'): {'SET' if groq_key_os else 'NOT SET'}")
    print(f"  os.environ.get('GROQ_API_KEY'): {'SET' if groq_key_environ else 'NOT SET'}")
    print(f"  settings.groq.api_key: {'SET' if groq_key_settings else 'NOT SET'}")
    
    if groq_key_os and groq_key_environ:
        print(f"  Keys match: {groq_key_os == groq_key_environ}")
    
    # Log all environment variables (filtered for privacy)
    print(f"\n📋 ALL ENVIRONMENT VARIABLES ({len(all_env_vars)} total):")
    for key, value in sorted(all_env_vars.items()):
        if any(sensitive in key.upper() for sensitive in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD']):
            if value:
                masked = f"{value[:4]}...{value[-2:]}" if len(value) > 6 else "***"
                print(f"  🔐 {key}: {masked}")
            else:
                print(f"  🔐 {key}: (empty)")
        else:
            print(f"  📝 {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
    
    # Check for .env files
    print(f"\n📁 .ENV FILES:")
    env_files = ['.env', '.env.local', '.env.production', '.env.development']
    for env_file in env_files:
        path = Path(env_file)
        if path.exists():
            print(f"  ✅ {env_file}: EXISTS")
            try:
                content = path.read_text()
                if 'GROQ_API_KEY' in content:
                    print(f"    🔍 Contains GROQ_API_KEY")
                else:
                    print(f"    ❌ No GROQ_API_KEY found")
            except Exception as e:
                print(f"    ⚠️  Error reading: {e}")
        else:
            print(f"  ❌ {env_file}: NOT FOUND")

def test_groq_api_connection():
    """Test Groq API connection with detailed error reporting"""
    print("\n" + "="*60)
    print("GROQ API CONNECTION TEST")
    print("="*60)
    
    # Get API key
    api_key = os.getenv('GROQ_API_KEY') or settings.groq.api_key
    
    if not api_key:
        print("❌ No GROQ_API_KEY found - cannot test connection")
        return False
    
    print(f"🔑 Using API key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test LLM client
    print("\n🤖 Testing Groq LLM Client...")
    try:
        llm_client = GroqClient(api_key=api_key)
        success, message = llm_client.test_connection()
        
        if success:
            print(f"✅ LLM Connection: SUCCESS")
            print(f"   Response: {message}")
        else:
            print(f"❌ LLM Connection: FAILED")
            print(f"   Error: {message}")
            return False
    except Exception as e:
        print(f"❌ LLM Client Error: {e}")
        return False
    
    # Test Whisper client
    print("\n🎤 Testing Groq Whisper Client...")
    try:
        whisper_client = GroqWhisperClient(api_key=api_key)
        success = whisper_client.test_connection()
        
        if success:
            print(f"✅ Whisper Connection: SUCCESS")
        else:
            print(f"❌ Whisper Connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Whisper Client Error: {e}")
        return False
    
    return True

def test_groq_quota():
    """Test if Groq API key has remaining quota"""
    print("\n" + "="*60)
    print("GROQ API QUOTA TEST")
    print("="*60)
    
    api_key = os.getenv('GROQ_API_KEY') or settings.groq.api_key
    
    if not api_key:
        print("❌ No GROQ_API_KEY found - cannot test quota")
        return False
    
    try:
        import requests
        
        # Make a simple API call to check quota
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test with multiple small requests to check rate limiting
        for i in range(3):
            print(f"\n📞 API Call #{i+1}...")
            
            payload = {
                "model": "gemma2-9b-it",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS")
                if 'usage' in result:
                    usage = result['usage']
                    print(f"   📊 Usage: {usage}")
                
                # Check response headers for rate limit info
                rate_headers = {k: v for k, v in response.headers.items() 
                               if 'rate' in k.lower() or 'limit' in k.lower() or 'remaining' in k.lower()}
                if rate_headers:
                    print(f"   📈 Rate Limit Headers: {rate_headers}")
                    
            elif response.status_code == 429:
                print(f"   ❌ RATE LIMITED")
                print(f"   Response: {response.text}")
                return False
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED - Invalid API key")
                print(f"   Response: {response.text}")
                return False
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN - Quota exhausted or access denied")
                print(f"   Response: {response.text}")
                return False
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")
        
        print(f"\n✅ Quota test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Quota test error: {e}")
        return False

def generate_debug_report():
    """Generate a comprehensive debug report"""
    print("\n" + "="*60)
    print("GENERATING DEBUG REPORT")
    print("="*60)
    
    timestamp = datetime.now().isoformat()
    
    report = {
        "timestamp": timestamp,
        "environment": {},
        "groq_tests": {},
        "recommendations": []
    }
    
    # Environment info
    critical_keys = ['GROQ_API_KEY', 'ELEVENLABS_API_KEY', 'SERPAPI_API_KEY']
    for key in critical_keys:
        value = os.getenv(key)
        report["environment"][key] = {
            "present": bool(value),
            "length": len(value) if value else 0
        }
    
    # Test results
    api_key = os.getenv('GROQ_API_KEY') or settings.groq.api_key
    
    if api_key:
        report["groq_tests"]["api_key_found"] = True
        report["groq_tests"]["connection_test"] = test_groq_api_connection()
        report["groq_tests"]["quota_test"] = test_groq_quota()
    else:
        report["groq_tests"]["api_key_found"] = False
        report["recommendations"].append("Set GROQ_API_KEY in environment variables")
    
    # Generate recommendations
    if not report["groq_tests"].get("connection_test"):
        report["recommendations"].append("Check network connectivity to api.groq.com")
        report["recommendations"].append("Verify API key is correct and not expired")
    
    if not report["groq_tests"].get("quota_test"):
        report["recommendations"].append("Check Groq account quota and billing")
        report["recommendations"].append("Implement fallback mechanisms for quota exhaustion")
    
    # Save report
    report_file = f"groq_debug_report_{timestamp.replace(':', '_')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Debug report saved to: {report_file}")
    return report

def main():
    """Main debug function"""
    print("🔍 GROQ API DEBUG TOOL")
    print("=" * 60)
    print("This tool will help diagnose GROQ_API_KEY issues in production")
    print("=" * 60)
    
    # Log environment
    log_environment_variables()
    
    # Test connections
    connection_success = test_groq_api_connection()
    
    # Test quota
    quota_success = test_groq_quota()
    
    # Generate report
    report = generate_debug_report()
    
    # Summary
    print("\n" + "="*60)
    print("DEBUG SUMMARY")
    print("="*60)
    
    api_key_present = bool(os.getenv('GROQ_API_KEY') or settings.groq.api_key)
    
    print(f"🔑 API Key Present: {'✅' if api_key_present else '❌'}")
    print(f"🔗 Connection Test: {'✅' if connection_success else '❌'}")  
    print(f"📊 Quota Test: {'✅' if quota_success else '❌'}")
    
    if not api_key_present:
        print("\n🚨 CRITICAL: GROQ_API_KEY not found!")
        print("   In Railway, make sure you have set the environment variable:")
        print("   GROQ_API_KEY = YOUR_GROQ_API_KEY_HERE")
        
    elif not connection_success:
        print("\n⚠️  WARNING: Connection failed!")
        print("   This could be due to network issues or invalid API key")
        
    elif not quota_success:
        print("\n⚠️  WARNING: Quota issues detected!")
        print("   Your Groq API key may have exceeded its quota")
        print("   Check your Groq account at https://console.groq.com/")
    
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("   GROQ_API_KEY is working correctly")

if __name__ == "__main__":
    main()