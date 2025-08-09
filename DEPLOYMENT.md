# United Voice Agent - Production Deployment Guide

This guide provides comprehensive instructions for deploying the United Voice Agent to production with frontend on Vercel and backend on various cloud platforms.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Backend Deployment Options](#backend-deployment-options)
   - [Heroku](#heroku-deployment)
   - [Railway](#railway-deployment)
   - [Render](#render-deployment)
5. [SSL/HTTPS Configuration](#sslhttps-configuration)
6. [WebSocket to WSS Migration](#websocket-to-wss-migration)
7. [Production Checklist](#production-checklist)
8. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.12+
- Git
- Domain name (optional but recommended)
- API keys for required services

### Required API Keys

- **Groq API Key**: For LLM and Whisper STT
- **ElevenLabs API Key**: For premium TTS
- **SerpApi API Key**: For Google Flights integration

## 🌍 Environment Variables

### Backend Environment Variables

Create a `.env` file in the project root:

```bash
# Core API Keys
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here

# Flight API Configuration
FLIGHT_API_USE_REAL=true
FLIGHT_API_FALLBACK_TO_MOCK=true

# WebSocket Configuration
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8000
WEBSOCKET_PATH=/socket.io/

# CORS Configuration (Production URLs)
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-custom-domain.com

# SSL Configuration (for WSS)
SSL_ENABLED=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Production Settings
ENVIRONMENT=production
DEBUG=false
```

### Frontend Environment Variables

Create a `.env.local` file in the `voice-frontend` directory:

```bash
# Backend WebSocket URL
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-backend-domain.herokuapp.com
NEXT_PUBLIC_API_URL=https://your-backend-domain.herokuapp.com

# Environment
NEXT_PUBLIC_ENVIRONMENT=production

# Analytics (optional)
NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

## 🚀 Frontend Deployment (Vercel)

### Step 1: Prepare Frontend for Production

1. Navigate to the frontend directory:
```bash
cd voice-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Build and test locally:
```bash
npm run build:prod
npm start
```

4. Create or update `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/"
    }
  ],
  "env": {
    "NEXT_PUBLIC_WEBSOCKET_URL": "@websocket-url",
    "NEXT_PUBLIC_API_URL": "@api-url",
    "NEXT_PUBLIC_ENVIRONMENT": "production"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ]
}
```

### Step 2: Deploy to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
vercel --prod
```

4. Set environment variables in Vercel dashboard:
   - Go to your project settings
   - Add environment variables from `.env.local`
   - Redeploy if needed

### Step 3: Custom Domain (Optional)

1. Add custom domain in Vercel dashboard
2. Configure DNS records as instructed
3. Update CORS origins in backend configuration

## 🔧 Backend Deployment Options

## Heroku Deployment

### Step 1: Prepare for Heroku

1. Ensure `Procfile` exists in root:
```
web: python -m uvicorn src.api.http_server:app --host 0.0.0.0 --port $PORT
websocket: python -m uvicorn src.services.websocket_server:app --host 0.0.0.0 --port $PORT
```

2. Create `runtime.txt`:
```
python-3.12
```

### Step 2: Deploy to Heroku

1. Install Heroku CLI
2. Login and create app:
```bash
heroku login
heroku create your-app-name
```

3. Set environment variables:
```bash
heroku config:set GROQ_API_KEY=your_key
heroku config:set ELEVENLABS_API_KEY=your_key
heroku config:set SERPAPI_API_KEY=your_key
heroku config:set CORS_ORIGINS=https://your-frontend.vercel.app
```

4. Deploy:
```bash
git push heroku main
```

5. Scale dynos:
```bash
heroku ps:scale web=1 websocket=1
```

## Railway Deployment

### Step 1: Configure Railway

1. Ensure `railway.json` exists in root
2. Connect Railway to your Git repository

### Step 2: Deploy

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and deploy:
```bash
railway login
railway link
railway up
```

3. Set environment variables in Railway dashboard

## Render Deployment

### Step 1: Configure Render

1. Ensure `render.yaml` exists in root
2. Connect Render to your Git repository

### Step 2: Deploy

1. Create account on Render.com
2. Connect GitHub repository
3. Configure environment variables in dashboard
4. Deploy automatically on git push

## 🔒 SSL/HTTPS Configuration

### For Custom Domains

1. **Certificate Generation** (Let's Encrypt):
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Certificates will be at:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

2. **Update Environment Variables**:
```bash
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### For Cloud Platforms

Most cloud platforms (Heroku, Railway, Render) provide SSL termination automatically. Enable HTTPS in your platform settings.

## 🔄 WebSocket to WSS Migration

### Backend Changes

1. **Update CORS Origins**:
```python
# In websocket_config.py
cors_allowed_origins = [
    "https://your-frontend.vercel.app",
    "https://your-custom-domain.com"
]
```

2. **Enable WSS Support**:
```python
# Production WebSocket configuration
if os.getenv('ENVIRONMENT') == 'production':
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins=cors_allowed_origins,
        logger=False,  # Disable debug logging in production
        engineio_logger=False
    )
```

### Frontend Changes

1. **Update WebSocket URL**:
```typescript
// In useWebSocket.ts
const WEBSOCKET_URL = process.env.NODE_ENV === 'production' 
  ? process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'wss://your-backend.herokuapp.com'
  : 'ws://localhost:8000';
```

2. **Connection Options**:
```typescript
const socket = io(WEBSOCKET_URL, {
  transports: ['websocket', 'polling'],
  upgrade: true,
  secure: true, // Enable for WSS
  rejectUnauthorized: true
});
```

## ✅ Production Checklist

### Pre-Deployment

- [ ] All API keys configured
- [ ] Environment variables set for both frontend and backend
- [ ] Build tests pass locally
- [ ] SSL certificates configured (if using custom domain)
- [ ] CORS origins updated for production URLs
- [ ] Database connections tested (if applicable)

### Post-Deployment

- [ ] Health check endpoints responding
- [ ] WebSocket connection working with WSS
- [ ] Audio streaming functioning correctly
- [ ] Voice agent responses working
- [ ] Flight search integration working
- [ ] Error tracking configured
- [ ] Monitoring dashboards set up
- [ ] Backup procedures in place

### Security Checklist

- [ ] HTTPS enabled on all endpoints
- [ ] WSS enabled for WebSocket connections
- [ ] API keys stored securely (not in code)
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Error messages don't expose sensitive data
- [ ] Security headers configured

### Performance Checklist

- [ ] Frontend build optimized
- [ ] Images and assets compressed
- [ ] CDN configured (if needed)
- [ ] Caching headers set
- [ ] Database queries optimized
- [ ] WebSocket connection pooling
- [ ] Memory usage monitored
- [ ] Response times acceptable

## 🔍 Troubleshooting

### Common Issues

#### WebSocket Connection Failed

**Symptoms**: Frontend can't connect to WebSocket server

**Solutions**:
1. Check if backend is running and accessible
2. Verify CORS origins include frontend domain
3. Ensure WSS is used in production (not WS)
4. Check firewall settings on server
5. Verify SSL certificates are valid

**Debug Commands**:
```bash
# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: your-backend.herokuapp.com" \
  -H "Origin: https://your-frontend.vercel.app" \
  https://your-backend.herokuapp.com/socket.io/
```

#### Audio Not Playing

**Symptoms**: Voice responses not audible

**Solutions**:
1. Check browser audio permissions
2. Verify HTTPS is enabled (required for audio)
3. Test with different browsers
4. Check audio format compatibility
5. Verify TTS service is responding

#### API Rate Limiting

**Symptoms**: 429 errors from external APIs

**Solutions**:
1. Implement exponential backoff
2. Add request queuing
3. Monitor API usage
4. Upgrade API plans if needed
5. Implement caching for repeated requests

#### High Memory Usage

**Symptoms**: Server running out of memory

**Solutions**:
1. Monitor memory usage patterns
2. Implement proper cleanup for WebSocket connections
3. Optimize audio buffer management
4. Consider upgrading server resources
5. Implement connection limits

### Log Analysis

#### Backend Logs
```bash
# Heroku logs
heroku logs --tail

# Railway logs
railway logs

# Render logs (check dashboard)
```

#### Frontend Logs
```bash
# Vercel logs
vercel logs

# Browser console
# Check Network tab for WebSocket connections
# Check Console tab for JavaScript errors
```

### Health Checks

#### Backend Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "groq": "healthy" if groq_client.test_connection() else "unhealthy",
            "elevenlabs": "healthy" if tts_service.test_connection() else "unhealthy",
            "serpapi": "healthy" if serpapi_client.test_connection() else "unhealthy"
        }
    }
```

#### Frontend Health Check
```bash
curl https://your-frontend.vercel.app/api/health
```

### Performance Monitoring

1. **Set up monitoring tools**:
   - Vercel Analytics for frontend
   - Heroku Metrics/Railway Metrics for backend
   - External monitoring (UptimeRobot, Pingdom)

2. **Key metrics to monitor**:
   - Response times
   - Error rates
   - Memory usage
   - CPU usage
   - WebSocket connection counts
   - API response times

### Emergency Procedures

#### Service Degradation
1. Check health endpoints
2. Review recent deployments
3. Check external API status
4. Scale resources if needed
5. Implement fallback modes

#### Complete Outage
1. Check cloud platform status
2. Verify DNS configuration
3. Check SSL certificate expiration
4. Review firewall rules
5. Implement emergency maintenance page

## 📞 Support

For deployment issues:

1. Check this troubleshooting guide first
2. Review platform-specific documentation
3. Check community forums
4. Contact platform support if needed

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Heroku Documentation](https://devcenter.heroku.com/)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)
- [Socket.IO Documentation](https://socket.io/docs/)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)

---

**Last Updated**: January 2024
**Version**: 1.0.0