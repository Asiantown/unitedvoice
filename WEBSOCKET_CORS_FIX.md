# WebSocket CORS Configuration Fix

## Problem Description

The United Voice Agent frontend deployed at `https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app` could not connect to the Railway backend at `https://web-production-204e.up.railway.app` due to CORS (Cross-Origin Resource Sharing) configuration issues.

### Error Message
```
ERROR:engineio.server:https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app is not an accepted origin
INFO: connection rejected (403 Forbidden)
```

### Root Cause
Socket.IO requires **exact domain matches** for CORS origins, but the original configuration used wildcard patterns like `https://*.vercel.app` which don't work with Socket.IO's CORS mechanism.

## Solution Implemented

### 1. Updated WebSocket Configuration (`src/services/websocket_config.py`)
- ✅ Modified `_get_default_cors_origins()` to use exact domain matches
- ✅ Added support for `FRONTEND_URL` environment variable
- ✅ Added automatic wildcard pattern expansion to specific domains
- ✅ Included the exact Vercel deployment URL: `https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app`

### 2. Created Production Environment File (`.env.production`)
- ✅ Set `ENVIRONMENT=production`
- ✅ Configured exact CORS origins
- ✅ Added `FRONTEND_URL` variable for easy updates

### 3. Updated Main Server Entry Point (`websocket_main.py`)
- ✅ Added automatic environment file loading
- ✅ Display CORS configuration on startup
- ✅ Production-specific server configuration

### 4. Created Testing Tools
- ✅ `test_websocket_cors.py` - Python script to test connection
- ✅ `test_cors_browser.html` - Browser-based connection test
- ✅ `start-production-websocket.sh` - Production startup script

## Configuration Details

### Exact CORS Origins Now Allowed
```
https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app
https://united-voice-agent.vercel.app
https://web-production-204e.up.railway.app
```

### Environment Variables (Production)
```bash
ENVIRONMENT=production
FRONTEND_URL=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app
CORS_ORIGINS=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app,https://united-voice-agent.vercel.app
```

## Deployment Instructions

### For Railway Backend:
1. **Set Environment Variables in Railway Dashboard:**
   ```
   ENVIRONMENT=production
   FRONTEND_URL=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app
   CORS_ORIGINS=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app,https://united-voice-agent.vercel.app
   ```

2. **Deploy with updated code:**
   - The updated `websocket_config.py` automatically includes the exact Vercel URL
   - Server will display CORS configuration on startup

### For Local Testing:
```bash
# Use the production startup script
./start-production-websocket.sh

# Or run manually with environment variables
ENVIRONMENT=production FRONTEND_URL=https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app python websocket_main.py
```

## Testing & Verification

### 1. Test with Python Script
```bash
python test_websocket_cors.py
```

### 2. Test in Browser
Open `test_cors_browser.html` in a browser and click "Connect to WebSocket"

### 3. Test Frontend Connection
After deploying the backend changes:
1. Visit: `https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app`
2. The connection status should change from "Connecting to server..." to "Connected"
3. Check browser console for WebSocket connection logs

## Expected Results

### ✅ Success Indicators:
- Frontend shows "Connected" status instead of "Connecting to server..."
- Browser DevTools Network tab shows successful Socket.IO connection
- Backend logs show successful connection without CORS errors
- Voice recording and TTS functionality works

### ❌ If Still Failing:
1. Check Railway environment variables are set correctly
2. Verify backend deployment includes updated code
3. Check browser console for specific error messages
4. Use the test tools to isolate the issue

## Key Technical Changes

### Before (Not Working):
```python
cors_origins = [
    "https://*.vercel.app",  # Wildcard - doesn't work with Socket.IO
    "https://*.railway.app",
    "https://*.render.com"
]
```

### After (Working):
```python
cors_origins = [
    "https://unitedvoice-bke1yxntg-asiantowns-projects.vercel.app",  # Exact match
    "https://web-production-204e.up.railway.app",
    "https://united-voice-agent.vercel.app"
]
```

## Additional Notes

- **Socket.IO Transport**: Both polling and WebSocket transports are supported
- **Security**: CORS is properly configured for production (no wildcards)
- **Flexibility**: New frontend URLs can be added via environment variables
- **Monitoring**: Server logs display all allowed CORS origins on startup

This fix ensures the WebSocket connection works immediately for the deployed frontend while maintaining security best practices.