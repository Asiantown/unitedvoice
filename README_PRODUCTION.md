# United Voice Agent - Production Deployment Guide

## Quick Production Deployment

This guide provides step-by-step instructions for deploying the United Voice Agent to production environments.

## Prerequisites

### Required Accounts & Services
- [GitHub](https://github.com) account with admin access to the repository
- [Vercel](https://vercel.com) account for frontend deployment
- [Railway](https://railway.app) or [Render](https://render.com) account for backend deployment
- [Groq](https://groq.com) API key for speech-to-text
- [ElevenLabs](https://elevenlabs.io) API key for text-to-speech
- (Optional) Google Flights API key and SerpAPI key for flight data

### Environment Variables

Create the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

#### Required for CI/CD Pipeline
```
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
VERCEL_TOKEN=your_vercel_deployment_token
VERCEL_ORG_ID=your_vercel_organization_id
VERCEL_PROJECT_ID=your_vercel_project_id
RAILWAY_TOKEN=your_railway_deployment_token
```

#### Optional for Enhanced Features
```
GOOGLE_FLIGHTS_API_KEY=your_google_flights_api_key
SERPAPI_KEY=your_serpapi_key
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=your_render_service_id
SLACK_WEBHOOK_URL=your_slack_webhook_for_notifications
```

#### Frontend Environment Variables
```
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-backend-domain.com
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

## Deployment Steps

### 1. Automated Deployment (Recommended)

The easiest way to deploy is using the automated CI/CD pipeline:

1. **Push to main branch** - The GitHub Actions workflow will automatically:
   - Run all tests (backend, frontend, security)
   - Build production assets
   - Deploy frontend to Vercel
   - Deploy backend to Railway/Render
   - Send notifications

2. **Monitor deployment** - Check the Actions tab in GitHub for deployment status

### 2. Manual Frontend Deployment (Vercel)

```bash
# In the voice-frontend directory
cd voice-frontend

# Install dependencies
npm ci

# Build for production
npm run build:prod

# Deploy to Vercel
npx vercel --prod
```

### 3. Manual Backend Deployment

#### Option A: Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy backend
railway up --service backend
```

#### Option B: Render
```bash
# Push to main branch - Render will auto-deploy from GitHub
git push origin main
```

#### Option C: Docker Deployment
```bash
# Build Docker image
docker build -t united-voice-agent .

# Run with environment variables
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e ELEVENLABS_API_KEY=your_key \
  united-voice-agent
```

### 4. Environment Configuration

#### Production Backend (.env)
```bash
# API Configuration
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GOOGLE_FLIGHTS_API_KEY=your_google_flights_api_key
SERPAPI_KEY=your_serpapi_key

# Server Configuration
PORT=8000
HOST=0.0.0.0
NODE_ENV=production

# CORS Settings
FRONTEND_URL=https://your-frontend-domain.vercel.app

# WebSocket Configuration
WEBSOCKET_ORIGINS=["https://your-frontend-domain.vercel.app"]

# Logging
LOG_LEVEL=info
```

#### Production Frontend (.env.local)
```bash
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-backend-domain.com
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_ENV=production
```

## Verification & Testing

### 1. Health Checks
- Frontend: `https://your-frontend-domain.vercel.app`
- Backend API: `https://your-backend-domain.com/health`
- WebSocket: Use browser dev tools to test WebSocket connection

### 2. End-to-End Testing
```bash
# Run comprehensive system test
python comprehensive_test.py

# Run final system verification
python final_system_test.py
```

### 3. Performance Monitoring
- Check Vercel Analytics for frontend performance
- Monitor Railway/Render logs for backend performance
- Set up alerts for critical errors

## Scaling & Optimization

### Frontend Optimization
- Enable Vercel Edge caching
- Optimize images and assets
- Use Next.js Image optimization
- Enable compression and minification

### Backend Optimization
- Configure horizontal scaling on Railway/Render
- Set up Redis for session management
- Enable request rate limiting
- Configure load balancing

## Security Checklist

- [ ] All API keys stored as secrets, not in code
- [ ] HTTPS enabled for all endpoints
- [ ] CORS configured for production domains only
- [ ] Input validation and sanitization implemented
- [ ] Rate limiting configured
- [ ] Security headers configured
- [ ] Regular dependency updates scheduled

## Troubleshooting

### Common Issues

#### Frontend Build Errors
```bash
# Clear Next.js cache
npm run clean
npm run build:prod
```

#### Backend Connection Issues
- Verify environment variables are set correctly
- Check CORS configuration matches frontend domain
- Ensure WebSocket URL uses 'wss://' for HTTPS sites

#### WebSocket Connection Failures
- Verify WebSocket server is running
- Check firewall/network configuration
- Test with WebSocket testing tools

### Logs & Monitoring
- **Vercel**: Check Function Logs in Vercel dashboard
- **Railway**: Use `railway logs` command
- **Render**: Check logs in Render dashboard

### Support Channels
- GitHub Issues: Report bugs and feature requests
- Documentation: Check inline code comments
- Monitoring: Set up alerts for production issues

## Rollback Procedures

### Quick Rollback
1. Revert to previous commit: `git revert HEAD`
2. Push to main: `git push origin main`
3. GitHub Actions will auto-deploy the previous version

### Manual Rollback
- **Vercel**: Use Vercel dashboard to promote previous deployment
- **Railway**: Use Railway dashboard to rollback to previous deployment
- **Render**: Redeploy from previous commit

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] DNS records pointed to production domains
- [ ] SSL certificates installed and valid
- [ ] Monitoring and alerts configured
- [ ] Backup procedures established
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team trained on rollback procedures

## Support & Maintenance

### Regular Maintenance
- Weekly dependency updates
- Monthly security audits
- Quarterly performance reviews
- Regular backup verification

### Emergency Contacts
- DevOps Team: [team@company.com]
- Infrastructure Provider: [Railway/Render support]
- Domain Provider: [DNS provider support]

---

## Quick Commands Reference

```bash
# Frontend Production Build
cd voice-frontend && npm run build:prod

# Backend Production Start
python start_websocket.py

# Health Check
curl https://your-backend-domain.com/health

# Deploy to Production
git push origin main  # Triggers automatic deployment

# View Production Logs
railway logs  # or check Render dashboard
vercel logs   # for frontend logs
```

This production setup ensures high availability, scalability, and maintainability for the United Voice Agent system.