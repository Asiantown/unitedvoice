# Railway Environment Variables Troubleshooting Guide

This guide helps resolve the common issue where Railway environment variables are set but not detected by the application.

## 🚨 Problem
You've set `GROQ_API_KEY` in Railway dashboard, but the app logs show:
```
GROQ_API_KEY not found - transcription will not work
```

## ✅ Solution
We've implemented a robust environment variable loading system that handles Railway's specific deployment environment.

### New Features Added:

1. **Robust Environment Loader** (`src/utils/env_loader.py`)
   - Tests multiple prefixes (`RAILWAY_`, `APP_`, `PRODUCTION_`, etc.)
   - Handles case sensitivity issues
   - Provides fuzzy matching for partial key names
   - Validates API key formats

2. **Updated Settings System** (`src/config/settings.py`)
   - Uses robust loader for all API keys
   - Provides better logging and validation
   - Handles fallback scenarios gracefully

3. **Debug Scripts**
   - `railway_env_debug.py` - Comprehensive environment variable analysis
   - `railway_startup_check.py` - Quick deployment verification
   - `test_robust_env_loading.py` - Local testing before deployment

## 🔧 Usage

### Local Testing
```bash
# Test the new environment loading system locally
python test_robust_env_loading.py
```

### Railway Deployment
```bash
# Deploy with environment variable checking
./railway_deploy_with_env_check.sh
```

### Debug on Railway
```bash
# Run comprehensive debug on Railway
railway run python railway_env_debug.py

# Quick environment check
railway run python railway_startup_check.py
```

## 📋 Troubleshooting Steps

### 1. Verify Variables in Railway Dashboard
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your project and service
3. Click "Variables" tab
4. Verify these variables exist:
   - `GROQ_API_KEY` (should start with `gsk_`)
   - `ELEVENLABS_API_KEY` 
   - `SERPAPI_API_KEY`

### 2. Check Variable Format
- **GROQ_API_KEY**: Must start with `gsk_`
- **No quotes**: Don't wrap values in quotes
- **No spaces**: Trim whitespace from values
- **Case sensitive**: Use UPPERCASE variable names

### 3. Common Railway Issues

#### Issue: Variable shows as set but app can't find it
**Solution**: Railway sometimes uses different loading mechanisms. Our robust loader handles this by checking:
- Standard environment variables
- Railway-prefixed variables (`RAILWAY_*`)
- App-prefixed variables (`APP_*`, `BACKEND_*`)
- Production-prefixed variables (`PRODUCTION_*`, `PROD_*`)

#### Issue: Placeholder values still in use
**Solution**: Make sure you replaced placeholder values like:
- ❌ `YOUR_GROQ_API_KEY_HERE`
- ✅ `gsk_actual_groq_api_key_here`

#### Issue: Variables work locally but not on Railway
**Solution**: Railway deployment environment can be different. Use our debug scripts:
```bash
railway run python railway_startup_check.py
```

### 4. Environment Variable Prefixes Tested

The robust loader automatically tests these prefixes:
- `` (no prefix - standard)
- `RAILWAY_`
- `APP_`
- `SERVICE_`
- `BACKEND_`
- `PRODUCTION_`
- `PROD_`
- `API_`
- `ENV_`

### 5. Validation Checks

The system now validates:
- GROQ keys start with `gsk_`
- Keys are not placeholder values
- Keys meet minimum length requirements
- Keys contain actual values, not empty strings

## 🔍 Debug Information

### Check Environment Variables
```python
from src.utils.env_loader import diagnose_env_vars

diagnosis = diagnose_env_vars()
print(diagnosis)
```

### Manual Key Loading
```python
from src.utils.env_loader import load_groq_api_key

groq_key = load_groq_api_key()
if groq_key:
    print("✅ GROQ key found")
else:
    print("❌ GROQ key not found")
```

## 🚀 Deployment Best Practices

1. **Always test locally first**:
   ```bash
   python test_robust_env_loading.py
   ```

2. **Use the deployment script**:
   ```bash
   ./railway_deploy_with_env_check.sh
   ```

3. **Monitor deployment logs**:
   ```bash
   railway logs -f
   ```

4. **Verify after deployment**:
   ```bash
   railway run python railway_startup_check.py
   ```

## 📞 Still Having Issues?

If you're still experiencing problems:

1. **Run the comprehensive debug**:
   ```bash
   railway run python railway_env_debug.py
   ```

2. **Check the generated debug report** (JSON file with detailed analysis)

3. **Verify Railway platform detection**:
   - Look for `RAILWAY_PROJECT_ID` in environment
   - Check if `is_railway: true` in debug output

4. **Test API key manually** at:
   - Groq: [https://console.groq.com/](https://console.groq.com/)
   - ElevenLabs: [https://elevenlabs.io/](https://elevenlabs.io/)
   - SerpAPI: [https://serpapi.com/](https://serpapi.com/)

## 🎯 Key Files Modified

- `src/utils/env_loader.py` - New robust environment loader
- `src/config/settings.py` - Updated to use robust loader
- `src/api/http_server.py` - Updated fallback loading
- `src/services/websocket_server.py` - Updated fallback loading
- `src/core/voice_agent.py` - Updated fallback loading
- `src/api/health.py` - Updated health checks

The system now provides multiple fallback mechanisms and comprehensive logging to ensure environment variables are properly detected in Railway's deployment environment.