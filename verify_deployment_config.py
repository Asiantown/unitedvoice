#!/usr/bin/env python3
"""
Deployment Configuration Verification Script
Run this on Railway to verify the CORS configuration is correct
"""

import os
import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    print("🔍 United Voice Agent - Deployment Configuration Verification")
    print("=" * 70)
    
    # Check environment
    environment = os.getenv('ENVIRONMENT', 'development')
    print(f"Environment: {environment}")
    
    # Check key environment variables
    env_vars = [
        'ENVIRONMENT',
        'PORT',
        'FRONTEND_URL',
        'CORS_ORIGINS',
        'GROQ_API_KEY',
        'ELEVENLABS_API_KEY',
        'SERPAPI_API_KEY'
    ]
    
    print("\n📋 Environment Variables:")
    missing_vars = []
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var:
                # Mask API keys for security
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"  ✅ {var}: {masked_value}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)
    
    # Load WebSocket configuration
    try:
        from src.services.websocket_config import get_websocket_config
        config = get_websocket_config()
        
        print(f"\n🌐 WebSocket Configuration:")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Environment: {config.environment}")
        print(f"  SSL Enabled: {config.ssl_enabled}")
        
        print(f"\n🔒 CORS Origins ({len(config.cors_allowed_origins)} configured):")
        for i, origin in enumerate(config.cors_allowed_origins, 1):
            print(f"  {i}. {origin}")
            
        # Check for the specific frontend URL
        frontend_url = "https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app"
        if frontend_url in config.cors_allowed_origins:
            print(f"  ✅ Frontend URL is properly configured!")
        else:
            print(f"  ⚠️  Frontend URL ({frontend_url}) not found in CORS origins")
            
    except Exception as e:
        print(f"\n❌ Error loading WebSocket configuration: {e}")
        return False
    
    # Check file system
    print(f"\n📁 File System Check:")
    important_files = [
        '.env.production',
        'src/services/websocket_config.py',
        'src/services/websocket_server.py',
        'websocket_main.py'
    ]
    
    for file_path in important_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}: Not found")
    
    # Final assessment
    print(f"\n🎯 Configuration Assessment:")
    
    critical_issues = []
    warnings = []
    
    if environment != 'production':
        critical_issues.append("ENVIRONMENT should be set to 'production'")
        
    if not os.getenv('FRONTEND_URL'):
        warnings.append("FRONTEND_URL not explicitly set (using defaults)")
        
    if missing_vars:
        if any('API_KEY' in var for var in missing_vars):
            critical_issues.append("Required API keys are missing")
        else:
            warnings.append(f"Some environment variables are missing: {', '.join(missing_vars)}")
    
    if frontend_url not in config.cors_allowed_origins:
        critical_issues.append("Frontend URL not in CORS origins - connection will fail")
    
    if critical_issues:
        print(f"  ❌ Critical Issues Found ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"    • {issue}")
        print(f"\n  🔧 Fix these issues before deploying!")
        return False
    else:
        print(f"  ✅ Configuration looks good!")
        
    if warnings:
        print(f"  ⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"    • {warning}")
    
    print(f"\n🚀 Ready for deployment!")
    print(f"   Frontend should be able to connect to WebSocket server.")
    print(f"   Expected connection: {frontend_url} -> Railway backend")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)