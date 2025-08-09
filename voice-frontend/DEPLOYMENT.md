# United Voice Agent Frontend - Deployment Guide

## Overview

This guide will walk you through deploying the United Voice Agent frontend to Vercel. The frontend is a Next.js 15.4.6 application with TypeScript, Three.js, and advanced voice features.

## Prerequisites

- Node.js 20.9.0 or higher
- npm or yarn package manager
- Vercel CLI installed globally: `npm install -g vercel`
- Git repository connected to your Vercel account
- Backend deployed to Railway (for WebSocket connections)

## Quick Deployment (Automated)

We've provided automated scripts to make deployment easy:

### 1. Pre-Deployment Check
```bash
./pre-deploy-check.sh
```

This script will verify:
- All required files are present
- Dependencies are installed correctly
- Build process works
- Environment variables are configured
- Vercel CLI is set up properly

### 2. Deploy to Vercel
```bash
# For preview deployment (staging)
./deploy-vercel.sh --preview

# For production deployment
./deploy-vercel.sh --production
```

## Manual Deployment Steps

### Step 1: Install Vercel CLI and Login

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to your Vercel account
vercel login
```

### Step 2: Configure Environment Variables

#### Option A: Using Vercel Dashboard
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings > Environment Variables
4. Add the following variables:

| Variable Name | Value | Environment |
|---------------|--------|-------------|
| `NEXT_PUBLIC_WS_URL` | `wss://your-backend.railway.app` | Production |
| `NEXT_PUBLIC_API_BASE_URL` | `https://your-backend.railway.app` | Production |
| `NEXT_PUBLIC_ENVIRONMENT` | `production` | Production |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | `true` | Production |
| `NEXT_PUBLIC_ENABLE_DEBUG` | `false` | Production |
| `NEXT_PUBLIC_ENABLE_ADVANCED_FEATURES` | `true` | Production |
| `NEXT_PUBLIC_ENABLE_VOICE_VISUALIZATION` | `true` | Production |
| `NEXT_PUBLIC_ENABLE_CONVERSATION_HISTORY` | `true` | Production |
| `NEXT_PUBLIC_ENABLE_SETTINGS` | `true` | Production |
| `NEXT_PUBLIC_ENABLE_PREMIUM_FEATURES` | `true` | Production |
| `NEXT_PUBLIC_AUDIO_QUALITY` | `high` | Production |
| `NEXT_PUBLIC_MAX_RECONNECT_ATTEMPTS` | `3` | Production |
| `NEXT_PUBLIC_RECONNECT_DELAY` | `2000` | Production |

#### Option B: Using Vercel CLI
```bash
# Set environment variables using CLI
vercel env add NEXT_PUBLIC_WS_URL
vercel env add NEXT_PUBLIC_API_BASE_URL
vercel env add NEXT_PUBLIC_ENVIRONMENT
# ... add all other variables
```

#### Option C: Import from .env file
```bash
# Use the provided .env.production file
# First, update the URLs in .env.production with your actual backend URLs
# Then import using Vercel CLI
vercel env pull .env.vercel.local
```

### Step 3: Update Backend URLs

Edit `.env.production` and replace placeholder URLs:

```bash
# Replace these with your actual Railway backend URLs
NEXT_PUBLIC_WS_URL=wss://your-actual-app-name.railway.app
NEXT_PUBLIC_API_BASE_URL=https://your-actual-app-name.railway.app
```

### Step 4: Test Build Locally

```bash
# Clean previous builds
npm run clean

# Install dependencies
npm install

# Test production build
npm run build

# Test production start (optional)
npm run start
```

### Step 5: Deploy

```bash
# For preview deployment
vercel

# For production deployment
vercel --prod
```

## Configuration Files

### vercel.json
The project includes a pre-configured `vercel.json` with:
- Optimized build settings
- Security headers (CSP, HSTS, etc.)
- Caching policies
- CORS configuration
- Function timeout and memory settings
- Automatic redirects (/ → /voice)

### next.config.ts
The Next.js configuration includes:
- Production optimizations
- Three.js compatibility fixes
- Security headers
- Image optimization
- TypeScript and ESLint settings (disabled for deployment)
- WebSocket connection support

## Environment-Specific Settings

### Development
- Debug mode enabled
- Relaxed security policies
- Hot reloading
- Source maps enabled

### Production
- Debug mode disabled
- Strict security policies
- Optimized builds
- Analytics enabled
- Error tracking (if configured)

## Domain Configuration

### Custom Domain (Optional)
1. In Vercel Dashboard, go to Settings > Domains
2. Add your custom domain
3. Configure DNS records as instructed by Vercel
4. Update CORS origins in environment variables if needed

### SSL/TLS
- Vercel automatically provides SSL certificates
- No additional configuration needed for HTTPS

## Performance Optimizations

The deployment includes several performance optimizations:

1. **Static Generation**: Most pages are statically generated
2. **Dynamic Imports**: Heavy components (Three.js) load only on client
3. **Image Optimization**: Automatic WebP/AVIF conversion
4. **Bundle Splitting**: Code splitting for optimal loading
5. **Caching**: Aggressive caching for static assets
6. **Compression**: Gzip/Brotli compression enabled

## Security Features

1. **Content Security Policy (CSP)**: Restricts resource loading
2. **HSTS**: Forces HTTPS connections
3. **X-Frame-Options**: Prevents clickjacking
4. **XSS Protection**: Built-in XSS filtering
5. **CORS Configuration**: Controlled cross-origin requests

## Monitoring and Analytics

### Built-in Monitoring
- Vercel provides built-in analytics
- Real-time performance monitoring
- Error tracking and logging

### Optional Integrations
- Google Analytics (configure NEXT_PUBLIC_GA_TRACKING_ID)
- Sentry error tracking (configure NEXT_PUBLIC_SENTRY_DSN)
- Custom analytics solutions

## Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check for TypeScript errors
npm run type-check

# Check for ESLint issues
npm run lint

# Clean and rebuild
npm run clean && npm run build
```

#### 2. Environment Variable Issues
- Ensure all NEXT_PUBLIC_ prefixed variables are set
- Check variable names match exactly (case-sensitive)
- Verify backend URLs are correct and accessible

#### 3. WebSocket Connection Issues
- Verify NEXT_PUBLIC_WS_URL is correct
- Ensure backend is deployed and running
- Check for firewall/proxy blocking WebSocket connections

#### 4. Three.js/VoiceOrb Issues
- Clear browser cache
- Check browser developer console for errors
- Ensure WebGL is supported and enabled

### Debug Commands

```bash
# Check environment variables
vercel env ls

# View deployment logs
vercel logs [deployment-url]

# Check project settings
vercel inspect

# Pull environment variables locally
vercel env pull .env.vercel.local
```

## Rollback Procedure

### Quick Rollback
```bash
# View recent deployments
vercel ls

# Promote a previous deployment to production
vercel promote [deployment-url]
```

### Emergency Rollback
1. Go to Vercel Dashboard
2. Select your project
3. Go to Deployments tab
4. Find a stable deployment
5. Click "Promote to Production"

## Maintenance

### Regular Tasks
1. **Update Dependencies**: Monthly security updates
2. **Monitor Performance**: Check Core Web Vitals
3. **Review Logs**: Check for errors or issues
4. **Update Environment Variables**: As backend changes
5. **Test Functionality**: Verify voice features work properly

### Scaling Considerations
- Vercel automatically scales based on traffic
- Function timeout can be increased if needed
- Consider CDN for static assets if global distribution needed

## Support

### Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Three.js Documentation](https://threejs.org/docs/)

### Getting Help
1. Check deployment logs first
2. Review environment variables
3. Test locally with production settings
4. Contact support with specific error messages and deployment URLs

## Checklist for First Deployment

- [ ] Backend deployed to Railway and accessible
- [ ] Vercel CLI installed and authenticated
- [ ] Environment variables configured in Vercel
- [ ] Backend URLs updated in production config
- [ ] Pre-deployment check script passes
- [ ] Build succeeds locally
- [ ] Domain configured (if using custom domain)
- [ ] SSL certificate provisioned
- [ ] Voice features tested in production
- [ ] WebSocket connections working
- [ ] Analytics configured (if desired)

## Post-Deployment Verification

After deployment, verify these features work:
1. **Basic Navigation**: All pages load correctly
2. **Voice Interface**: Microphone access and recording
3. **WebSocket Connection**: Real-time communication with backend
4. **Audio Playback**: TTS responses play correctly
5. **Visual Effects**: Three.js orb animations work
6. **Responsive Design**: Works on mobile and desktop
7. **Browser Compatibility**: Tested in major browsers