# 🚀 United Voice Agent - Production Deployment Checklist

## Current Status ✅
- **Frontend**: Ready for Vercel deployment
- **Backend**: Ready for Railway deployment
- **UI**: Working perfectly (no changes made)
- **Build**: All errors fixed, builds successfully

## Step 1: Deploy Backend to Railway (5 minutes)

```bash
# From project root directory
cd /Users/ryanyin/united-voice-agent

# Install Railway CLI if not installed
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy backend
./deploy-to-railway.sh
```

After deployment, Railway will give you a URL like:
`https://united-voice-backend-production.up.railway.app`

## Step 2: Configure Vercel Environment (2 minutes)

Update `/Users/ryanyin/united-voice-agent/voice-frontend/.env.production`:

```bash
# Replace with your Railway backend URL
NEXT_PUBLIC_WS_URL=https://united-voice-backend-production.up.railway.app
```

## Step 3: Deploy Frontend to Vercel (5 minutes)

```bash
# From frontend directory
cd /Users/ryanyin/united-voice-agent/voice-frontend

# Pre-deployment check
./pre-deploy-check.sh

# Deploy to Vercel
./deploy-vercel.sh --production
```

Vercel will give you a URL like:
`https://united-voice-agent.vercel.app`

## Step 4: Update Backend CORS (2 minutes)

In Railway dashboard, add environment variable:
```
CORS_ORIGINS=https://united-voice-agent.vercel.app
```

## Step 5: Verify Deployment ✅

1. **Test Frontend**: Visit your Vercel URL
2. **Test WebSocket**: Click "Start Call" button
3. **Test Voice**: Speak and verify transcription
4. **Test AI Response**: Verify AI responds with audio

## Environment Variables Checklist

### Backend (Railway) ✅
- [ ] `GROQ_API_KEY` - Your Groq API key
- [ ] `ELEVENLABS_API_KEY` - Your ElevenLabs API key  
- [ ] `SERPAPI_API_KEY` - Your SerpAPI key (optional)
- [ ] `GOOGLE_FLIGHTS_API_KEY` - Google Flights key (optional)
- [ ] `CORS_ORIGINS` - Your Vercel frontend URL

### Frontend (Vercel) ✅
- [ ] `NEXT_PUBLIC_WS_URL` - Your Railway backend URL

## Quick Troubleshooting

### If WebSocket won't connect:
1. Check NEXT_PUBLIC_WS_URL is set correctly in Vercel
2. Verify CORS_ORIGINS includes your Vercel URL in Railway
3. Check Railway logs for connection errors

### If audio doesn't play:
1. Verify ELEVENLABS_API_KEY is set in Railway
2. Check browser console for audio errors
3. Ensure microphone permissions are granted

### If transcription fails:
1. Verify GROQ_API_KEY is set in Railway
2. Check browser console for API errors
3. Ensure microphone is working

## Production URLs

After deployment, you'll have:
- **Frontend**: `https://[your-app].vercel.app`
- **Backend**: `https://[your-app].railway.app`
- **WebSocket**: `wss://[your-app].railway.app`

## Total Deployment Time: ~15 minutes

Your app is production-ready! 🎉

---

## Need Help?

- Railway issues: Check `/Users/ryanyin/united-voice-agent/RAILWAY_DEPLOYMENT_GUIDE.md`
- Vercel issues: Check `/Users/ryanyin/united-voice-agent/voice-frontend/VERCEL_DEPLOYMENT_GUIDE.md`
- General issues: Check `/Users/ryanyin/united-voice-agent/voice-frontend/DEPLOYMENT.md`