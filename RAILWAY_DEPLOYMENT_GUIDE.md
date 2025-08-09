# Railway Deployment Guide - United Voice Agent Backend

This guide will help you deploy the United Voice Agent backend to Railway cloud platform and get the WebSocket URL for your Vercel frontend.

## Prerequisites

- Railway account (sign up at [railway.app](https://railway.app))
- GitHub repository with your backend code
- API keys: GROQ_API_KEY, ELEVENLABS_API_KEY, SERPAPI_API_KEY

## Step 1: Setup Railway Account

1. Go to [railway.app](https://railway.app) and sign up/log in
2. Connect your GitHub account
3. Install the Railway CLI (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

## Step 2: Create a New Railway Project

### Option A: Using Railway Dashboard
1. Click "New Project" in Railway dashboard
2. Select "Deploy from GitHub repo"
3. Choose your `united-voice-agent` repository
4. Railway will automatically detect it's a Python project

### Option B: Using Railway CLI
1. Navigate to your backend directory:
   ```bash
   cd /Users/ryanyin/united-voice-agent
   ```
2. Initialize Railway project:
   ```bash
   railway init
   railway link
   ```

## Step 3: Configure Environment Variables

In the Railway dashboard, go to your project → Variables tab and add these variables:

### Required API Keys
```
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
```

### Production Configuration
```
ENVIRONMENT=production
WEBSOCKET_HOST=0.0.0.0
SSL_ENABLED=false
LOG_LEVEL=INFO
MAX_CONNECTIONS=1000
PING_TIMEOUT=60
PING_INTERVAL=25
FLIGHT_API_USE_REAL=true
FLIGHT_API_FALLBACK_TO_MOCK=true
PYTHONPATH=/app/src
PYTHONUNBUFFERED=1
```

### CORS Configuration for Vercel
```
CORS_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app
```

**Note**: Replace `your-frontend.vercel.app` with your actual Vercel domain. You can add multiple domains separated by commas.

## Step 4: Deploy to Railway

### Automatic Deployment
1. Push your code to GitHub (if not already done)
2. Railway will automatically deploy when you push to your main branch
3. Monitor the build process in the Railway dashboard

### Manual Deployment (CLI)
```bash
railway up
```

## Step 5: Get Your Backend URLs

After successful deployment, Railway will provide you with:

1. **Public Domain**: `https://your-app-name.up.railway.app`
2. **WebSocket URL**: Same domain but with WebSocket protocol

### Your Frontend Environment Variable
Add this to your Vercel frontend environment variables:
```
NEXT_PUBLIC_WS_URL=https://your-app-name.up.railway.app
```

## Step 6: Verify Deployment

1. **Health Check**: Visit `https://your-app-name.up.railway.app/health`
2. **WebSocket Test**: Use the provided test files or browser dev tools
3. **Logs**: Check Railway dashboard → Deployments → Logs

## Step 7: Configure Custom Domain (Optional)

1. In Railway dashboard, go to Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed
4. Update CORS_ORIGINS environment variable with your custom domain

## Common Issues & Solutions

### Build Failures
- Check requirements.txt for correct dependencies
- Verify Python version in runtime.txt (3.12.8)
- Review build logs in Railway dashboard

### WebSocket Connection Issues
- Ensure CORS_ORIGINS includes your frontend domain
- Check that PORT environment variable is not overridden
- Verify WebSocket endpoint is `/socket.io/`

### API Key Issues
- Double-check all API keys are correctly set
- Ensure no extra spaces or quotes in environment variables
- Test API keys individually if needed

### Memory/Performance Issues
- Monitor resource usage in Railway dashboard
- Adjust MAX_CONNECTIONS if needed
- Consider upgrading Railway plan for more resources

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq API key for LLM and STT | - | Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for TTS | - | Yes |
| `SERPAPI_API_KEY` | SerpAPI key for flight search | - | Yes |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `*.vercel.app` | Yes |
| `ENVIRONMENT` | Environment mode | `production` | Yes |
| `WEBSOCKET_HOST` | WebSocket bind host | `0.0.0.0` | No |
| `SSL_ENABLED` | Enable SSL (Railway handles this) | `false` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `MAX_CONNECTIONS` | Maximum WebSocket connections | `1000` | No |
| `PING_TIMEOUT` | WebSocket ping timeout | `60` | No |
| `PING_INTERVAL` | WebSocket ping interval | `25` | No |
| `FLIGHT_API_USE_REAL` | Use real flight API | `true` | No |
| `FLIGHT_API_FALLBACK_TO_MOCK` | Fallback to mock data | `true` | No |

## Next Steps

1. **Deploy to Railway** using this guide
2. **Get your Railway URL** from the dashboard
3. **Update your Vercel frontend** with `NEXT_PUBLIC_WS_URL`
4. **Test the connection** between frontend and backend
5. **Configure custom domains** if needed

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [railway.app/discord](https://railway.app/discord)
- Check Railway dashboard logs for debugging

---

**Important**: After deployment, save your Railway URL as you'll need it for the frontend configuration!