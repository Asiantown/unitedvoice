#!/usr/bin/env python3
"""
Railway Environment Variables Debug Script
==========================================

This script helps debug Railway environment variable issues, specifically 
focusing on GROQ_API_KEY detection problems.

Railway sometimes uses different prefixes, case sensitivity, or variable 
loading mechanisms that can cause environment variables to not be detected 
by standard Python methods.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """Mask sensitive values showing only first/last few characters"""
    if not value or len(value) <= show_chars * 2:
        return "*" * len(value) if value else "EMPTY"
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def get_all_env_vars() -> Dict[str, str]:
    """Get all environment variables"""
    return dict(os.environ)


def find_groq_related_vars(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Find all environment variables that might be related to GROQ"""
    groq_vars = {}
    
    # Look for various patterns
    patterns = [
        'GROQ',
        'groq',
        'Groq',
        'WHISPER',
        'whisper',
        'API_KEY',
        'api_key'
    ]
    
    for key, value in env_vars.items():
        for pattern in patterns:
            if pattern in key:
                groq_vars[key] = value
                break
    
    return groq_vars


def test_environment_access_methods() -> Dict[str, Any]:
    """Test different methods of accessing environment variables"""
    results = {
        'methods': {},
        'railway_specific': {},
        'case_variations': {},
        'prefixed_variations': {}
    }
    
    # Standard methods
    key = 'GROQ_API_KEY'
    results['methods'] = {
        'os.getenv()': os.getenv(key),
        'os.environ.get()': os.environ.get(key),
        'direct_access': os.environ.get(key, 'NOT_FOUND'),
        'subprocess_env': subprocess.run(['printenv', key], 
                                       capture_output=True, 
                                       text=True).stdout.strip() or None
    }
    
    # Railway-specific checks
    railway_prefixes = ['RAILWAY_', 'RLW_', 'APP_', 'SERVICE_']
    for prefix in railway_prefixes:
        prefixed_key = f"{prefix}GROQ_API_KEY"
        results['railway_specific'][prefixed_key] = os.getenv(prefixed_key)
    
    # Case variations
    case_variations = ['groq_api_key', 'Groq_Api_Key', 'GROQ_api_key', 'groq_API_KEY']
    for variation in case_variations:
        results['case_variations'][variation] = os.getenv(variation)
    
    # Other prefixed variations
    other_prefixes = ['PRODUCTION_', 'PROD_', 'APP_', 'SERVICE_', 'BACKEND_']
    for prefix in other_prefixes:
        prefixed_key = f"{prefix}GROQ_API_KEY"
        results['prefixed_variations'][prefixed_key] = os.getenv(prefixed_key)
    
    return results


def check_railway_runtime_info() -> Dict[str, Any]:
    """Check Railway-specific runtime information"""
    railway_info = {
        'is_railway': False,
        'railway_vars': {},
        'runtime_info': {}
    }
    
    # Check for Railway-specific environment variables
    railway_indicators = [
        'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT',
        'RAILWAY_SERVICE_NAME', 'RAILWAY_DEPLOYMENT_ID', 'NIXPACKS_METADATA'
    ]
    
    for indicator in railway_indicators:
        value = os.getenv(indicator)
        if value:
            railway_info['is_railway'] = True
            railway_info['railway_vars'][indicator] = mask_sensitive_value(value, 6)
    
    # Runtime environment info
    railway_info['runtime_info'] = {
        'platform': sys.platform,
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'user': os.getenv('USER', 'unknown'),
        'home': os.getenv('HOME', 'unknown'),
        'path_count': len(os.getenv('PATH', '').split(':')),
    }
    
    return railway_info


def test_groq_connection(api_key: Optional[str]) -> Dict[str, Any]:
    """Test Groq API connection if key is available"""
    if not api_key:
        return {'status': 'no_key', 'message': 'No API key available for testing'}
    
    try:
        # Try to import groq client
        from groq import Groq
        
        # Initialize client
        client = Groq(api_key=api_key)
        
        # Test with a simple request
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )
        
        return {
            'status': 'success',
            'message': 'API key is valid and working',
            'model_used': 'llama-3.1-8b-instant',
            'response_received': True
        }
        
    except ImportError:
        return {
            'status': 'import_error',
            'message': 'Groq library not installed - cannot test connection'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'API test failed: {str(e)}',
            'error_type': type(e).__name__
        }


def check_config_files() -> Dict[str, Any]:
    """Check various config files that might contain environment variables"""
    config_files = [
        '.env',
        '.env.local',
        '.env.production',
        '.env.railway',
        'railway.json',
        'nixpacks.toml',
        'Dockerfile',
        'docker-compose.yml'
    ]
    
    config_info = {}
    
    for config_file in config_files:
        file_path = os.path.join(os.getcwd(), config_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    config_info[config_file] = {
                        'exists': True,
                        'size': len(content),
                        'has_groq_key': 'GROQ_API_KEY' in content,
                        'lines': len(content.splitlines())
                    }
            except Exception as e:
                config_info[config_file] = {
                    'exists': True,
                    'error': str(e)
                }
        else:
            config_info[config_file] = {'exists': False}
    
    return config_info


def generate_railway_setup_instructions() -> List[str]:
    """Generate specific instructions for Railway setup"""
    return [
        "🚂 Railway Environment Variable Setup Instructions:",
        "",
        "1. Log into your Railway dashboard: https://railway.app/dashboard",
        "2. Select your project and service",
        "3. Go to 'Variables' tab",
        "4. Add these variables (click 'New Variable'):",
        "",
        "   Variable Name: GROQ_API_KEY",
        "   Value: [your-actual-groq-api-key]",
        "",
        "   Variable Name: ELEVENLABS_API_KEY", 
        "   Value: [your-actual-elevenlabs-api-key]",
        "",
        "   Variable Name: SERPAPI_API_KEY",
        "   Value: [your-actual-serpapi-api-key]",
        "",
        "5. Click 'Deploy' to redeploy with new variables",
        "6. Wait for deployment to complete",
        "",
        "⚠️  IMPORTANT NOTES:",
        "- Do NOT include quotes around the values",
        "- Make sure there are no spaces before/after the key",
        "- Variable names are case-sensitive (use UPPERCASE)",
        "- Keys should start with 'gsk_' for Groq",
        "",
        "🔍 To verify deployment:",
        "- Check deployment logs for 'GROQ_API_KEY not found' messages",
        "- Use Railway CLI: railway logs",
        "- Run this debug script on Railway to verify"
    ]


def create_robust_env_loader() -> str:
    """Generate code for a more robust environment variable loader"""
    return '''
def load_env_var_robust(var_name: str, prefixes: List[str] = None, 
                       case_sensitive: bool = True) -> Optional[str]:
    """
    Robust environment variable loader for Railway and other platforms
    
    Args:
        var_name: Base variable name (e.g., 'GROQ_API_KEY')
        prefixes: List of prefixes to try (e.g., ['RAILWAY_', 'APP_'])
        case_sensitive: Whether to try case variations
    
    Returns:
        The environment variable value if found, None otherwise
    """
    import os
    
    # Default prefixes for Railway
    if prefixes is None:
        prefixes = ['', 'RAILWAY_', 'APP_', 'SERVICE_', 'PRODUCTION_', 'PROD_']
    
    # Case variations to try
    case_variations = [var_name]
    if not case_sensitive:
        case_variations.extend([
            var_name.lower(),
            var_name.upper(), 
            var_name.title(),
            var_name.swapcase()
        ])
    
    # Try all combinations
    for prefix in prefixes:
        for case_var in case_variations:
            full_key = f"{prefix}{case_var}"
            
            # Try multiple access methods
            for method in [os.getenv, os.environ.get]:
                value = method(full_key)
                if value:
                    return value
    
    # Last resort: check all environment variables for partial matches
    for env_key, env_value in os.environ.items():
        if var_name.lower() in env_key.lower() and env_value:
            return env_value
    
    return None

# Usage example:
groq_key = load_env_var_robust('GROQ_API_KEY')
if groq_key:
    print(f"Found GROQ_API_KEY: {groq_key[:8]}...")
else:
    print("GROQ_API_KEY not found with any method")
'''


def main():
    """Main debug function"""
    print("🔍 Railway Environment Variables Debug Script")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python: {sys.version}")
    print("")
    
    # 1. Check Railway runtime info
    print("🚂 Railway Runtime Information:")
    railway_info = check_railway_runtime_info()
    if railway_info['is_railway']:
        print("✅ Running on Railway platform")
        for key, value in railway_info['railway_vars'].items():
            print(f"   {key}: {value}")
    else:
        print("❌ Not detected as Railway platform (or Railway vars not set)")
    print("")
    
    # 2. Get all environment variables (masked)
    print("🌍 Environment Variables Summary:")
    all_env = get_all_env_vars()
    print(f"Total environment variables: {len(all_env)}")
    
    # Find GROQ-related variables
    groq_vars = find_groq_related_vars(all_env)
    print(f"GROQ-related variables found: {len(groq_vars)}")
    for key, value in groq_vars.items():
        masked_value = mask_sensitive_value(value, 4) if value else "NOT SET"
        print(f"   {key}: {masked_value}")
    print("")
    
    # 3. Test different access methods
    print("🔧 Environment Variable Access Methods:")
    access_results = test_environment_access_methods()
    
    print("Standard methods:")
    for method, value in access_results['methods'].items():
        status = "✅ SET" if value else "❌ NOT SET" 
        masked = mask_sensitive_value(value, 4) if value else "NONE"
        print(f"   {method}: {status} ({masked})")
    
    print("\nRailway-specific prefixes:")
    found_railway = False
    for key, value in access_results['railway_specific'].items():
        if value:
            found_railway = True
            masked = mask_sensitive_value(value, 4)
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: NOT SET")
    
    if not found_railway:
        print("   ⚠️  No Railway-prefixed variables found")
    
    print("\nCase variations:")
    found_case = False
    for key, value in access_results['case_variations'].items():
        if value:
            found_case = True
            masked = mask_sensitive_value(value, 4)
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: NOT SET")
    
    if not found_case:
        print("   ⚠️  No case variations found")
    
    print("")
    
    # 4. Check config files
    print("📁 Configuration Files:")
    config_info = check_config_files()
    for file_name, info in config_info.items():
        if info['exists']:
            groq_status = "✅ Contains GROQ_API_KEY" if info.get('has_groq_key') else "❌ No GROQ_API_KEY"
            print(f"   ✅ {file_name}: {groq_status} ({info.get('lines', 0)} lines)")
        else:
            print(f"   ❌ {file_name}: Not found")
    print("")
    
    # 5. Test API connection
    print("🧪 API Connection Test:")
    # Try to find any GROQ key from all methods
    test_key = None
    for method_results in access_results.values():
        for key, value in method_results.items():
            if value and 'gsk_' in value:  # Groq keys start with gsk_
                test_key = value
                break
        if test_key:
            break
    
    connection_result = test_groq_connection(test_key)
    print(f"   Status: {connection_result['status']}")
    print(f"   Message: {connection_result['message']}")
    if 'error_type' in connection_result:
        print(f"   Error Type: {connection_result['error_type']}")
    print("")
    
    # 6. Generate recommendations
    print("💡 Recommendations:")
    
    # Check if we found a valid GROQ key
    has_groq_key = any(
        value for method_results in access_results.values() 
        for value in method_results.values() 
        if value
    )
    
    if not has_groq_key:
        print("🚨 CRITICAL: No GROQ_API_KEY found!")
        print("")
        for instruction in generate_railway_setup_instructions():
            print(instruction)
        print("")
    else:
        print("✅ GROQ_API_KEY found, but may have connection issues")
        print("   - Verify the key is valid at https://console.groq.com/")
        print("   - Check if you have quota remaining")
        print("   - Test the key manually with Groq's API")
    
    # 7. Generate improved code
    print("🛠️  Robust Environment Loader Code:")
    print("Save this code to improve environment variable detection:")
    print("")
    print(create_robust_env_loader())
    
    # 8. Generate debug report
    debug_report = {
        'timestamp': datetime.now().isoformat(),
        'platform': sys.platform,
        'is_railway': railway_info['is_railway'],
        'railway_vars': railway_info['railway_vars'],
        'groq_vars_found': groq_vars,
        'access_methods_results': access_results,
        'config_files': config_info,
        'api_test': connection_result,
        'total_env_vars': len(all_env),
        'recommendations': [
            "Update code to use robust environment variable loader",
            "Verify GROQ_API_KEY is set correctly in Railway",
            "Check API key validity and quota",
            "Use Railway CLI to verify deployment environment"
        ]
    }
    
    # Save debug report
    report_filename = f"railway_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(debug_report, f, indent=2, default=str)
    
    print(f"📋 Debug report saved to: {report_filename}")
    print("")
    print("🎯 Next Steps:")
    print("1. Run this script on Railway to compare results")
    print("2. Update your code with the robust environment loader")
    print("3. Verify Railway environment variables are set correctly")
    print("4. Test API connectivity from Railway environment")


if __name__ == "__main__":
    main()