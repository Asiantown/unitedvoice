#!/usr/bin/env python3
"""
Test Robust Environment Variable Loading
========================================

This script tests the new robust environment variable loading system
locally before deployment to Railway.
"""

import os
import sys
import tempfile
from unittest.mock import patch
import importlib.util

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_env_loader_basic():
    """Test basic functionality of the robust environment loader"""
    print("🧪 Testing Basic Environment Loader Functionality")
    print("-" * 50)
    
    try:
        from utils.env_loader import load_env_var_robust, load_groq_api_key
        
        # Test 1: Standard environment variable
        test_key = "TEST_API_KEY_STANDARD"
        test_value = "test_standard_value_123"
        os.environ[test_key] = test_value
        
        result = load_env_var_robust(test_key)
        assert result == test_value, f"Expected {test_value}, got {result}"
        print("✅ Standard environment variable loading works")
        
        # Test 2: Prefixed environment variable
        prefixed_key = "APP_TEST_API_KEY_PREFIXED"
        prefixed_value = "test_prefixed_value_456"
        os.environ[prefixed_key] = prefixed_value
        
        result = load_env_var_robust("TEST_API_KEY_PREFIXED", prefixes=["", "APP_"])
        assert result == prefixed_value, f"Expected {prefixed_value}, got {result}"
        print("✅ Prefixed environment variable loading works")
        
        # Test 3: Case insensitive loading
        case_key = "test_api_key_case"
        case_value = "test_case_value_789"
        os.environ[case_key] = case_value
        
        result = load_env_var_robust("TEST_API_KEY_CASE", case_sensitive=False)
        assert result == case_value, f"Expected {case_value}, got {result}"
        print("✅ Case insensitive environment variable loading works")
        
        # Test 4: GROQ API key loading
        groq_key = "gsk_test_groq_key_12345678901234567890"
        os.environ["GROQ_API_KEY"] = groq_key
        
        result = load_groq_api_key()
        assert result == groq_key, f"Expected {groq_key}, got {result}"
        print("✅ GROQ API key loading works")
        
        # Clean up
        for key in [test_key, prefixed_key, case_key, "GROQ_API_KEY"]:
            os.environ.pop(key, None)
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_railway_scenarios():
    """Test Railway-specific scenarios"""
    print("\n🚂 Testing Railway-Specific Scenarios")
    print("-" * 50)
    
    try:
        from utils.env_loader import load_groq_api_key, diagnose_env_vars
        
        # Simulate Railway environment
        railway_env = {
            "RAILWAY_PROJECT_ID": "test-project-123",
            "RAILWAY_SERVICE_ID": "test-service-456", 
            "RAILWAY_ENVIRONMENT": "production",
            "RAILWAY_GROQ_API_KEY": "gsk_railway_test_key_123456789",
        }
        
        # Set Railway environment
        for key, value in railway_env.items():
            os.environ[key] = value
        
        # Test Railway-prefixed GROQ key detection
        result = load_groq_api_key()
        assert result == "gsk_railway_test_key_123456789", f"Railway GROQ key not found: {result}"
        print("✅ Railway-prefixed GROQ API key detection works")
        
        # Test diagnostic function
        diagnosis = diagnose_env_vars()
        assert diagnosis['platform_info']['is_railway'] == True, "Railway detection failed"
        print("✅ Railway platform detection works")
        
        # Clean up
        for key in railway_env.keys():
            os.environ.pop(key, None)
        
        print("\n✅ All Railway scenario tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Railway scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings_integration():
    """Test integration with settings system"""
    print("\n⚙️  Testing Settings Integration")
    print("-" * 50)
    
    try:
        # Set up test environment
        test_env = {
            "GROQ_API_KEY": "gsk_test_groq_key_settings_123",
            "ELEVENLABS_API_KEY": "test_elevenlabs_key_456",
            "SERPAPI_API_KEY": "test_serpapi_key_789",
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Import and test settings
        from config.settings import Settings
        
        settings = Settings.from_env()
        
        # Test that settings loaded the keys correctly
        assert settings.groq.api_key == "gsk_test_groq_key_settings_123", "GROQ key not loaded in settings"
        assert settings.elevenlabs.api_key == "test_elevenlabs_key_456", "ElevenLabs key not loaded in settings"
        assert settings.serpapi.api_key == "test_serpapi_key_789", "SerpAPI key not loaded in settings"
        
        print("✅ Settings integration works correctly")
        
        # Clean up
        for key in test_env.keys():
            os.environ.pop(key, None)
        
        print("\n✅ Settings integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Settings integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """Test API key validation"""
    print("\n🔍 Testing API Key Validation")
    print("-" * 50)
    
    try:
        from utils.env_loader import validate_api_keys
        
        # Test with valid GROQ key
        os.environ["GROQ_API_KEY"] = "gsk_valid_groq_key_1234567890123456789"
        
        issues = validate_api_keys()
        groq_issues = [issue for issue in issues if "GROQ_API_KEY" in issue and "placeholder" not in issue]
        assert len(groq_issues) == 0, f"Valid GROQ key failed validation: {groq_issues}"
        print("✅ Valid GROQ key passes validation")
        
        # Test with invalid GROQ key (placeholder)
        os.environ["GROQ_API_KEY"] = "YOUR_GROQ_API_KEY_HERE"
        
        issues = validate_api_keys()
        placeholder_issues = [issue for issue in issues if "placeholder" in issue]
        assert len(placeholder_issues) > 0, "Placeholder GROQ key should fail validation"
        print("✅ Placeholder GROQ key properly detected")
        
        # Test with invalid format
        os.environ["GROQ_API_KEY"] = "invalid_format_key"
        
        issues = validate_api_keys()
        format_issues = [issue for issue in issues if "should start with" in issue]
        assert len(format_issues) > 0, "Invalid format should be detected"
        print("✅ Invalid GROQ key format properly detected")
        
        # Clean up
        os.environ.pop("GROQ_API_KEY", None)
        
        print("\n✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def simulate_railway_deployment():
    """Simulate how the app would behave in Railway deployment"""
    print("\n🚀 Simulating Railway Deployment")
    print("-" * 50)
    
    try:
        # Clear any existing keys
        for key in os.environ.copy():
            if "API_KEY" in key:
                del os.environ[key]
        
        # Simulate Railway environment with proper API key
        railway_env = {
            "RAILWAY_PROJECT_ID": "sim-project-123",
            "RAILWAY_SERVICE_ID": "sim-service-456",
            "RAILWAY_ENVIRONMENT": "production",
            "GROQ_API_KEY": "gsk_simulated_railway_key_123456789012345",
            "ELEVENLABS_API_KEY": "sim_elevenlabs_key_456789012345",
        }
        
        for key, value in railway_env.items():
            os.environ[key] = value
        
        print("🔧 Simulated Railway environment set up")
        
        # Test settings loading
        from config.settings import Settings
        importlib.reload(sys.modules['config.settings'])  # Reload to pick up new env
        
        settings = Settings.from_env()
        
        # Verify keys were loaded
        assert settings.groq.api_key is not None, "GROQ key not loaded in simulated Railway"
        assert settings.elevenlabs.api_key is not None, "ElevenLabs key not loaded in simulated Railway"
        
        print("✅ Settings loaded successfully in simulated Railway environment")
        
        # Test that the app components would work
        groq_available = bool(settings.groq.api_key)
        elevenlabs_available = bool(settings.elevenlabs.api_key)
        
        print(f"  GROQ API: {'✅ Available' if groq_available else '❌ Not available'}")
        print(f"  ElevenLabs API: {'✅ Available' if elevenlabs_available else '❌ Not available'}")
        
        # Clean up
        for key in railway_env.keys():
            os.environ.pop(key, None)
        
        print("\n✅ Railway deployment simulation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Railway deployment simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🧪 Robust Environment Variable Loading Test Suite")
    print("=" * 60)
    print("Testing the improved environment variable loading system")
    print("before deployment to Railway.")
    print()
    
    tests = [
        ("Basic Functionality", test_env_loader_basic),
        ("Railway Scenarios", test_railway_scenarios),
        ("Settings Integration", test_settings_integration),
        ("API Key Validation", test_validation),
        ("Railway Deployment Simulation", simulate_railway_deployment),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print('=' * 60)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            failed += 1
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'=' * 60}")
    print("TEST RESULTS SUMMARY")
    print('=' * 60)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The robust environment loading system is ready for Railway deployment.")
        print("\n📋 Next steps:")
        print("1. Deploy to Railway using: ./railway_deploy_with_env_check.sh")
        print("2. Run railway_startup_check.py on Railway to verify")
        print("3. Monitor deployment logs for environment variable detection")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix the issues before deploying.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)