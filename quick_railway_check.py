#!/usr/bin/env python3
"""
Quick Railway environment check - Run this to verify your setup
"""

import os
import sys

print("🚂 RAILWAY QUICK CHECK")
print("=" * 50)

# Check critical environment variables
vars_to_check = {
    'GROQ_API_KEY': 'gsk_',
    'ELEVENLABS_API_KEY': None,
    'CORS_ORIGINS': None,
    'ENVIRONMENT': None,
    'PORT': None
}

found = []
missing = []

for var, prefix in vars_to_check.items():
    value = os.getenv(var)
    if value:
        masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else value
        if prefix and not value.startswith(prefix):
            print(f"⚠️  {var}: Found but invalid format (should start with {prefix})")
            print(f"    Current: {masked}")
        else:
            print(f"✅ {var}: {masked}")
            found.append(var)
    else:
        print(f"❌ {var}: NOT FOUND")
        missing.append(var)

print("\n" + "=" * 50)
print("📊 SUMMARY")
print("=" * 50)

if missing:
    print(f"⚠️  Missing {len(missing)} critical variables:")
    for var in missing:
        print(f"   - {var}")
    print("\n📝 Add these in Railway Variables tab!")
else:
    print("✅ All environment variables configured!")

print("\n🔍 Quick Fixes:")
if 'GROQ_API_KEY' in missing:
    print("1. Add GROQ_API_KEY = (your valid Groq API key starting with gsk_)")
if 'CORS_ORIGINS' in missing:
    print("2. Add CORS_ORIGINS = *")
if 'ENVIRONMENT' in missing:
    print("3. Add ENVIRONMENT = production")

print("\n" + "=" * 50)