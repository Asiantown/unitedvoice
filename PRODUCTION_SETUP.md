# United Voice Agent - Production Setup Quick Start

This guide provides step-by-step instructions to quickly deploy the United Voice Agent to production.

## 🚀 Quick Setup

### 1. Environment Setup

1. Copy the environment template:
```bash
cp .env.production.template .env
```

2. Fill in your API keys in `.env`:
```bash
GROQ_API_KEY=your_actual_groq_key_here
ELEVENLABS_API_KEY=your_actual_elevenlabs_key_here  
SERPAPI_API_KEY=your_actual_serpapi_key_here
CORS_ORIGINS=https://your-frontend.vercel.app
```

### 2. Using the Deployment Script

The easiest way to deploy is using the included deployment script:

```bash
# Setup development environment
./deploy.sh setup-dev

# Deploy backend to Heroku
./deploy.sh deploy heroku

# Deploy frontend to Vercel  
./deploy.sh deploy vercel

# Deploy both at once
./deploy.sh deploy all
```

### 3. Manual Platform Deployment

#### Backend (Choose One)

**Heroku:**
```bash
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key
heroku config:set ELEVENLABS_API_KEY=your_key
heroku config:set SERPAPI_API_KEY=your_key
heroku config:set CORS_ORIGINS=https://your-frontend.vercel.app
git push heroku main
```

**Railway:**
```bash
railway login
railway link
railway up
```

**Render:**
1. Connect GitHub repo in Render dashboard
2. Add environment variables
3. Deploy automatically on push

#### Frontend (Vercel)

```bash
cd voice-frontend
npm install
vercel --prod
```

## 📋 Environment Variables Reference

### Required for Backend:
- `GROQ_API_KEY` - Your Groq API key
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key  
- `SERPAPI_API_KEY` - Your SerpApi key
- `CORS_ORIGINS` - Frontend URLs (comma-separated)

### Required for Frontend:
- `NEXT_PUBLIC_WEBSOCKET_URL` - Backend WebSocket URL
- `NEXT_PUBLIC_API_URL` - Backend API URL

## 🔍 Verify Deployment

1. **Backend Health Check:**
```bash
curl https://your-backend.herokuapp.com/health/detailed
```

2. **Frontend Access:**
Open `https://your-frontend.vercel.app` in browser

3. **WebSocket Connection:**
Test voice functionality in the deployed frontend

## 🆘 Troubleshooting

### WebSocket Connection Issues
- Ensure CORS_ORIGINS includes your frontend URL
- Check if WSS is enabled (automatic on cloud platforms)
- Verify backend is accessible

### API Service Errors
- Check API keys are correct in environment variables
- Verify API quotas aren't exceeded
- Check health endpoint for service status

### Build/Deploy Failures
- Ensure all dependencies are in requirements.txt
- Check platform-specific logs
- Verify environment variables are set

## 📞 Support

For detailed troubleshooting, see `DEPLOYMENT.md` or check platform-specific documentation.

---

**Quick Commands Summary:**
```bash
# One-time setup
./deploy.sh setup-dev

# Deploy everything
./deploy.sh deploy all

# Check health
curl https://your-backend.herokuapp.com/health
```