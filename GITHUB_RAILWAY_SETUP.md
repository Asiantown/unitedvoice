# Connect GitHub to Railway - Step by Step

## 1. Create GitHub Repository

### Option A: Using GitHub CLI (if installed)
```bash
gh repo create united-voice-agent --public --source=. --remote=origin --push
```

### Option B: Manual GitHub Setup
1. Go to https://github.com/new
2. Repository name: `united-voice-agent`
3. Make it Public or Private (your choice)
4. DON'T initialize with README (we already have files)
5. Click "Create repository"

## 2. Push Your Code to GitHub

After creating the repo, run these commands:

```bash
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/united-voice-agent.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If you get an authentication error, you may need to:
- Use a Personal Access Token instead of password
- Or use GitHub CLI: `gh auth login`

## 3. Connect Railway to GitHub

1. **Go to Railway Dashboard**: https://railway.com/project/639756e6-f4cb-4f26-bfce-cd7ed231d4b0

2. **Create New Service from GitHub**:
   - Click "New" or "+" button
   - Select "GitHub Repo"
   - If not connected, click "Connect GitHub"
   - Authorize Railway to access your GitHub

3. **Select Your Repository**:
   - Search for "united-voice-agent"
   - Click on your repository
   - Railway will automatically detect it's a Python app

4. **Configure Deployment**:
   - Railway will use the `Procfile` automatically
   - Your environment variables are already set
   - Click "Deploy"

## 4. Set Up Auto-Deploy

Railway automatically deploys when you push to GitHub:
- Every push to `main` branch triggers a new deployment
- You can see deployment status in Railway dashboard

## 5. Verify Deployment

Once deployed, Railway will show:
- A green checkmark when successful
- Your app URL (like `https://united-voice-agent-production.up.railway.app`)
- Deployment logs

## Quick Commands Summary

```bash
# 1. Create GitHub repo (if using CLI)
gh repo create united-voice-agent --public --source=. --remote=origin

# 2. Or add remote manually
git remote add origin https://github.com/YOUR_USERNAME/united-voice-agent.git

# 3. Push to GitHub
git push -u origin main

# 4. Future updates (auto-deploys to Railway)
git add .
git commit -m "Your changes"
git push
```

## Troubleshooting

### Authentication Issues
If GitHub asks for password:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select "repo" scope
4. Use token as password

### Railway Not Detecting App
Make sure these files exist:
- `Procfile` (tells Railway how to start)
- `requirements.txt` or `pyproject.toml` (Python dependencies)

### Environment Variables
Remember to set in Railway dashboard:
- `GROQ_API_KEY`
- `ELEVENLABS_API_KEY`
- `CORS_ORIGINS=*`
- `PORT=8000`

Your app is ready to deploy via GitHub! 🚀