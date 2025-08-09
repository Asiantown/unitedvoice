#!/usr/bin/env python3
"""
Railway Startup Environment Check
=================================

Quick diagnostic script to run on Railway startup to verify environment
variables are properly loaded. This should be run as part of the deployment
process to catch environment variable issues early.
"""

import os
import sys
import json
from datetime import datetime


def quick_env_check():
    """Quick environment variable check for Railway deployment"""
    
    print("🚂 Railway Environment Variable Check")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Platform: {sys.platform}")
    
    # Check if we're on Railway
    is_railway = bool(os.getenv('RAILWAY_PROJECT_ID'))
    print(f"Railway Platform: {'✅ YES' if is_railway else '❌ NO'}")
    
    if is_railway:
        railway_vars = {
            'PROJECT_ID': os.getenv('RAILWAY_PROJECT_ID', 'NOT_SET')[:8] + '...',
            'SERVICE_ID': os.getenv('RAILWAY_SERVICE_ID', 'NOT_SET')[:8] + '...',
            'ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET'),
            'SERVICE_NAME': os.getenv('RAILWAY_SERVICE_NAME', 'NOT_SET'),
        }
        print("\nRailway Info:")
        for key, value in railway_vars.items():
            print(f"  {key}: {value}")
    
    print("\nEnvironment Variables Check:")
    
    # Check critical API keys
    critical_vars = {
        'GROQ_API_KEY': 'Groq API for LLM/STT',
        'ELEVENLABS_API_KEY': 'ElevenLabs for TTS', 
        'SERPAPI_API_KEY': 'SerpAPI for flight search'
    }
    
    all_good = True
    
    for var_name, description in critical_vars.items():
        # Try multiple methods
        methods = {
            'os.getenv()': os.getenv(var_name),
            'os.environ.get()': os.environ.get(var_name),
        }
        
        # Also try Railway prefixes
        railway_prefixed = f"RAILWAY_{var_name}"
        methods[f'RAILWAY_'] = os.getenv(railway_prefixed)
        
        # Check results
        found_value = None
        found_method = None
        
        for method, value in methods.items():
            if value and value.strip() and value not in ['YOUR_GROQ_API_KEY_HERE', 'your_groq_api_key_here']:
                found_value = value
                found_method = method
                break
        
        if found_value:
            # Mask the value for security
            masked = f"{found_value[:4]}...{found_value[-4:]}" if len(found_value) > 8 else "***"
            print(f"  ✅ {var_name}: FOUND via {found_method} ({masked})")
            
            # Validate format for GROQ key
            if var_name == 'GROQ_API_KEY' and not found_value.startswith('gsk_'):
                print(f"    ⚠️  WARNING: Should start with 'gsk_'")
                all_good = False
                
        else:
            print(f"  ❌ {var_name}: NOT FOUND ({description})")
            all_good = False
    
    print(f"\nOverall Status: {'✅ ALL GOOD' if all_good else '❌ ISSUES FOUND'}")
    
    # Quick test of robust loader if available
    try:
        sys.path.insert(0, '/app')  # Railway app path
        from src.utils.env_loader import load_groq_api_key, diagnose_env_vars
        
        print("\n🔧 Testing Robust Environment Loader:")
        groq_key_robust = load_groq_api_key()
        if groq_key_robust:
            print("  ✅ Robust loader found GROQ_API_KEY")
        else:
            print("  ❌ Robust loader could not find GROQ_API_KEY")
        
        # Get diagnostic info
        diagnosis = diagnose_env_vars()
        print(f"  Total env vars: {diagnosis['env_var_counts']['total_vars']}")
        print(f"  Railway vars: {diagnosis['env_var_counts']['railway_vars']}")
        print(f"  API key vars: {diagnosis['env_var_counts']['api_key_vars']}")
        
    except ImportError as e:
        print(f"\n⚠️  Could not import robust loader: {e}")
    except Exception as e:
        print(f"\n⚠️  Error testing robust loader: {e}")
    
    # Print helpful info for debugging
    print(f"\nDebugging Info:")
    print(f"  Working Directory: {os.getcwd()}")
    print(f"  Python Path: {':'.join(sys.path[:3])}...")
    print(f"  Total Environment Variables: {len(os.environ)}")
    
    # List all variables containing 'API' or 'KEY' (masked)
    api_vars = []
    for key, value in os.environ.items():
        if ('API' in key.upper() or 'KEY' in key.upper()) and value:
            masked = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
            api_vars.append(f"{key}: {masked}")
    
    if api_vars:
        print(f"\nFound API-related variables:")
        for var in api_vars[:10]:  # Show first 10
            print(f"  {var}")
        if len(api_vars) > 10:
            print(f"  ... and {len(api_vars) - 10} more")
    
    return all_good


def railway_deployment_instructions():
    """Print Railway deployment instructions"""
    print("\n" + "=" * 50)
    print("🚂 RAILWAY DEPLOYMENT INSTRUCTIONS")
    print("=" * 50)
    print()
    print("If environment variables are not found, follow these steps:")
    print()
    print("1. Go to Railway Dashboard: https://railway.app/dashboard")
    print("2. Select your project and service")
    print("3. Click on 'Variables' tab")
    print("4. Add these variables:")
    print()
    print("   Variable: GROQ_API_KEY")
    print("   Value: [your-groq-api-key-starting-with-gsk_]")
    print()
    print("   Variable: ELEVENLABS_API_KEY")
    print("   Value: [your-elevenlabs-api-key]")
    print()
    print("   Variable: SERPAPI_API_KEY") 
    print("   Value: [your-serpapi-key]")
    print()
    print("5. Click 'Deploy' to trigger a new deployment")
    print("6. Monitor logs during deployment")
    print()
    print("⚠️  IMPORTANT:")
    print("- Don't add quotes around the values")
    print("- Variable names are case-sensitive")
    print("- Groq keys should start with 'gsk_'")
    print("- Avoid placeholder values like 'YOUR_API_KEY_HERE'")
    print()


if __name__ == "__main__":
    success = quick_env_check()
    
    if not success:
        railway_deployment_instructions()
        sys.exit(1)  # Exit with error code
    else:
        print("\n🎉 Environment check passed! App should start successfully.")
        sys.exit(0)  # Exit with success code