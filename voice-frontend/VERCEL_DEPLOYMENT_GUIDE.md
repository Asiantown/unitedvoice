# Step-by-Step Vercel Deployment Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Prepare Your Backend URL
First, get your Railway backend URL. It should look like:
- `https://your-app-name.railway.app` (for HTTP/API)
- `wss://your-app-name.railway.app` (for WebSocket)

### Step 2: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 3: Login to Vercel
```bash
vercel login
```
Follow the prompts to authenticate with your Vercel account.

### Step 4: Run Pre-Deployment Check
```bash
./pre-deploy-check.sh
```
This will verify everything is ready for deployment.

### Step 5: Deploy
```bash
# For preview/testing
./deploy-vercel.sh --preview

# For production (after testing preview)
./deploy-vercel.sh --production
```

That's it! Your app should be deployed. ✅

---

## 📋 Detailed Step-by-Step Guide

### Step 1: Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with your GitHub, GitLab, or Bitbucket account
3. Verify your email address

### Step 2: Connect Your Repository

#### Option A: Import via Vercel Dashboard
1. In Vercel Dashboard, click "Add New..."
2. Select "Project"
3. Import your Git repository
4. Choose the `voice-frontend` directory if it's in a monorepo
5. Vercel will auto-detect it's a Next.js project

#### Option B: Deploy via CLI (Recommended)
1. Navigate to your project directory:
   ```bash
   cd /path/to/united-voice-agent/voice-frontend
   ```

2. Initialize Vercel project:
   ```bash
   vercel
   ```

3. Answer the setup questions:
   ```
   ? Set up and deploy "~/voice-frontend"? [Y/n] Y
   ? Which scope do you want to deploy to? [your-username]
   ? Link to existing project? [y/N] N
   ? What's your project's name? united-voice-agent-frontend
   ? In which directory is your code located? ./
   ```

### Step 3: Configure Environment Variables

#### 3.1: Get Your Environment Variables Ready
You'll need these values:
- **Backend URL**: Your Railway app URL (e.g., `https://myapp.railway.app`)
- **WebSocket URL**: Same as backend but with `wss://` protocol

#### 3.2: Set Variables in Vercel Dashboard
1. Go to your project in Vercel Dashboard
2. Click on "Settings" tab
3. Click on "Environment Variables" in the sidebar
4. Add each variable:

**Required Variables:**
```
NEXT_PUBLIC_WS_URL = wss://your-backend.railway.app
NEXT_PUBLIC_API_BASE_URL = https://your-backend.railway.app
NEXT_PUBLIC_ENVIRONMENT = production
```

**Recommended Variables:**
```
NEXT_PUBLIC_ENABLE_ANALYTICS = true
NEXT_PUBLIC_ENABLE_DEBUG = false
NEXT_PUBLIC_ENABLE_ADVANCED_FEATURES = true
NEXT_PUBLIC_ENABLE_VOICE_VISUALIZATION = true
NEXT_PUBLIC_ENABLE_CONVERSATION_HISTORY = true
NEXT_PUBLIC_ENABLE_SETTINGS = true
NEXT_PUBLIC_ENABLE_PREMIUM_FEATURES = true
NEXT_PUBLIC_AUDIO_QUALITY = high
NEXT_PUBLIC_MAX_RECONNECT_ATTEMPTS = 3
NEXT_PUBLIC_RECONNECT_DELAY = 2000
```

#### 3.3: Set Environment for Each Variable
For each variable, select the environment:
- ✅ **Production** (for production deployment)
- ✅ **Preview** (for preview deployments) 
- ❌ **Development** (leave unchecked unless needed)

### Step 4: Configure Build Settings (If Needed)

Most settings are automatically detected, but verify:

1. **Framework Preset**: Next.js (should be auto-detected)
2. **Build Command**: `npm run build` (default)
3. **Output Directory**: `.next` (default)
4. **Install Command**: `npm install` (default)

### Step 5: Deploy

#### 5.1: First Deployment (Preview)
```bash
vercel
```
This creates a preview deployment for testing.

#### 5.2: Test Your Preview
1. Click the preview URL provided
2. Test the voice interface:
   - Check if the page loads
   - Test microphone permissions
   - Verify WebSocket connection
   - Test voice recording and playback

#### 5.3: Deploy to Production
```bash
vercel --prod
```

### Step 6: Set Up Custom Domain (Optional)

#### 6.1: Add Domain in Vercel
1. Go to your project settings
2. Click "Domains" tab
3. Add your domain (e.g., `voice.yourdomain.com`)

#### 6.2: Configure DNS
Add these DNS records with your domain provider:

**For subdomain (recommended):**
```
Type: CNAME
Name: voice
Value: cname.vercel-dns.com
```

**For root domain:**
```
Type: A
Name: @
Value: 76.76.19.61
```

#### 6.3: Wait for Verification
- DNS propagation can take up to 24 hours
- Vercel will automatically issue SSL certificate

### Step 7: Verify Deployment

#### 7.1: Check Basic Functionality
- [ ] Homepage loads and redirects to `/voice`
- [ ] Voice interface appears correctly
- [ ] Three.js orb animates properly
- [ ] No console errors in browser dev tools

#### 7.2: Test Voice Features
- [ ] Microphone permission requested and granted
- [ ] Can record audio (hold to talk)
- [ ] WebSocket connects to backend
- [ ] Audio playback works for responses
- [ ] Visual feedback shows during recording/processing

#### 7.3: Test on Multiple Devices
- [ ] Desktop (Chrome, Firefox, Safari)
- [ ] Mobile (iOS Safari, Android Chrome)
- [ ] Tablet

### Step 8: Monitor and Maintain

#### 8.1: Set Up Monitoring
1. **Vercel Analytics**: Enable in project settings
2. **Performance Monitoring**: Check Core Web Vitals
3. **Error Tracking**: Monitor function logs

#### 8.2: Set Up Alerts (Optional)
1. Go to project Settings > Notifications
2. Configure alerts for:
   - Deployment failures
   - Performance issues
   - High error rates

---

## 🛠️ Troubleshooting Common Issues

### Issue 1: Build Fails
**Symptom**: Deployment fails during build step

**Solution**:
```bash
# Test build locally first
npm run build

# Check for specific errors:
npm run type-check  # TypeScript errors
npm run lint        # ESLint errors
```

**If build works locally but fails on Vercel**:
1. Check if all dependencies are in `package.json`
2. Ensure Node.js version compatibility
3. Check build logs in Vercel dashboard

### Issue 2: Environment Variables Not Working
**Symptom**: App loads but features don't work, WebSocket fails

**Solution**:
1. Verify all `NEXT_PUBLIC_` variables are set in Vercel
2. Check variable names (case-sensitive)
3. Ensure variables are enabled for "Production" environment
4. Redeploy after adding variables

**Debug commands**:
```bash
vercel env ls                    # List all variables
vercel env pull .env.vercel.local # Pull variables locally
```

### Issue 3: WebSocket Connection Fails
**Symptom**: Voice interface loads but can't connect to backend

**Common Causes & Solutions**:

1. **Wrong WebSocket URL**:
   - Check `NEXT_PUBLIC_WS_URL` matches your Railway app
   - Ensure it starts with `wss://` (not `ws://`)

2. **Backend Not Running**:
   - Verify your Railway backend is deployed and running
   - Test backend URL directly in browser

3. **CORS Issues**:
   - Ensure backend allows connections from your Vercel domain
   - Check backend CORS configuration

4. **Browser Security**:
   - HTTPS sites can only connect to WSS (secure WebSocket)
   - Mixed content (HTTPS → WS) is blocked by browsers

### Issue 4: Three.js/VoiceOrb Not Loading
**Symptom**: Voice interface loads but no animated orb appears

**Solution**:
1. **Browser Compatibility**:
   - Ensure WebGL is supported and enabled
   - Test in different browsers

2. **Clear Browser Cache**:
   - Hard refresh (Ctrl+F5 or Cmd+Shift+R)
   - Clear browser cache and cookies

3. **Check Console Errors**:
   - Open browser dev tools → Console tab
   - Look for WebGL or Three.js errors

### Issue 5: Mobile Issues
**Symptom**: Works on desktop but not mobile

**Common Solutions**:
1. **iOS Safari Restrictions**:
   - Microphone requires user gesture to activate
   - Ensure audio playback is triggered by user action

2. **Android Chrome**:
   - Check microphone permissions in browser settings
   - Verify HTTPS is used (required for microphone access)

3. **Performance Issues**:
   - Three.js can be heavy on mobile
   - Consider reducing visual quality for mobile

### Issue 6: Slow Loading
**Symptom**: App takes long time to load

**Solutions**:
1. **Check Bundle Size**:
   ```bash
   npm run analyze  # If available
   ```

2. **Optimize Images**:
   - Ensure images are properly optimized
   - Use Next.js Image component

3. **Reduce Three.js Bundle**:
   - Import only needed Three.js modules
   - Use dynamic imports for heavy components

---

## 📚 Additional Resources

### Vercel Documentation
- [Vercel Next.js Guide](https://vercel.com/docs/frameworks/nextjs)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/concepts/projects/custom-domains)

### Next.js Deployment
- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)
- [Production Checklist](https://nextjs.org/docs/going-to-production)

### Voice Features
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Three.js Documentation](https://threejs.org/docs/)

---

## 🎯 Success Checklist

After following this guide, you should have:

- [ ] ✅ Vercel account created and CLI installed
- [ ] ✅ Repository connected to Vercel
- [ ] ✅ Environment variables configured
- [ ] ✅ Successful build and deployment
- [ ] ✅ Custom domain configured (optional)
- [ ] ✅ Voice interface working
- [ ] ✅ WebSocket connection to backend
- [ ] ✅ Three.js animations working
- [ ] ✅ Mobile compatibility verified
- [ ] ✅ Production URL shared with stakeholders

**Your United Voice Agent frontend is now live! 🎉**

---

## 🚨 Emergency Procedures

### Quick Rollback
If something goes wrong after deployment:

```bash
# List recent deployments
vercel ls

# Promote a previous working deployment
vercel promote [previous-deployment-url]
```

### Disable Features Quickly
If a feature is causing issues, you can quickly disable it:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Set these to `false` to disable problematic features:
   - `NEXT_PUBLIC_ENABLE_PREMIUM_FEATURES`
   - `NEXT_PUBLIC_ENABLE_VOICE_VISUALIZATION`
   - `NEXT_PUBLIC_ENABLE_ADVANCED_FEATURES`
3. Redeploy: `vercel --prod`

### Contact Support
- **Vercel Support**: [vercel.com/support](https://vercel.com/support)
- **Include**: Deployment URL, error messages, browser console output