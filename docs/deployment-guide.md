# Deployment Guide

## Prerequisites

### Required Services
- **Groq API Key**: For Whisper STT and LLaMA LLM
- **ElevenLabs API Key**: For high-quality TTS
- **SerpAPI Key** (Optional): For Google Flights integration

### System Requirements
- Python 3.8+ (Backend)
- Node.js 18+ (Frontend)
- 2GB RAM minimum
- 10GB storage

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/united-voice-agent.git
cd united-voice-agent
```

### 2. Backend Setup

#### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys
GROQ_API_KEY=gsk_your_actual_key_here
ELEVENLABS_API_KEY=sk_your_actual_key_here
SERPAPI_API_KEY=your_optional_key_here
ENVIRONMENT=development
```

#### Run Backend
```bash
# Start WebSocket server
python -m src.main

# Or with hot reload
python -m src.services.websocket_server
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd voice-frontend
npm install
```

#### Configure Environment
```bash
# Create .env.local
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local
```

#### Run Frontend
```bash
npm run dev
# Access at http://localhost:3000
```

## Production Deployment

### Railway (Backend)

#### 1. Setup Railway Project
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init
```

#### 2. Configure Environment Variables
```bash
# Set production variables
railway variables set GROQ_API_KEY=gsk_your_key
railway variables set ELEVENLABS_API_KEY=sk_your_key
railway variables set SERPAPI_API_KEY=your_key
railway variables set ENVIRONMENT=production
railway variables set PORT=8000
```

#### 3. Deploy
```bash
# Deploy to Railway
railway up

# Get deployment URL
railway domain
```

#### 4. Railway Configuration Files

##### `railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -m src.main"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

##### `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "gcc"]

[phases.install]
cmds = ["pip install --no-cache-dir -r requirements.txt"]

[start]
cmd = "python -m src.main"
```

### Vercel (Frontend)

#### 1. Setup Vercel Project
```bash
cd voice-frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Initialize project
vercel
```

#### 2. Configure Environment
```bash
# Set environment variables in Vercel dashboard
NEXT_PUBLIC_BACKEND_URL=https://your-app.up.railway.app
```

#### 3. Deploy
```bash
# Production deployment
vercel --prod

# Preview deployment
vercel
```

#### 4. Vercel Configuration

##### `vercel.json`
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_BACKEND_URL": "@backend_url"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        }
      ]
    }
  ]
}
```

## Docker Deployment

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "src.main"]
```

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

# Install production dependencies
RUN npm ci --only=production

# Environment
ENV NODE_ENV=production
ENV PORT=3000

# Run
CMD ["npm", "start"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - ENVIRONMENT=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./voice-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

## Environment Variables Reference

### Backend Variables
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | Yes | Groq API key for STT/LLM | `gsk_...` |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key for TTS | `sk_...` |
| `SERPAPI_API_KEY` | No | SerpAPI key for flights | `...` |
| `ENVIRONMENT` | Yes | Deployment environment | `production` |
| `PORT` | No | Server port (default: 8000) | `8000` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `https://app.com` |

### Frontend Variables
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | Backend WebSocket URL | `wss://api.example.com` |
| `NEXT_PUBLIC_APP_NAME` | No | Application name | `United Voice Agent` |
| `NEXT_PUBLIC_DEBUG` | No | Enable debug mode | `false` |

## SSL/TLS Configuration

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://localhost:8000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
    }
}
```

## Monitoring & Logging

### Health Checks
```python
# Backend health endpoint
@app.get("/health")
async def health_check():
    checks = {
        "groq": check_groq_api(),
        "elevenlabs": check_elevenlabs_api(),
        "websocket": check_websocket_server()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

### Logging Configuration
```python
# logging.conf
[loggers]
keys=root,app,websocket

[handlers]
keys=console,file

[formatters]
keys=default

[logger_root]
level=INFO
handlers=console,file

[handler_console]
class=StreamHandler
formatter=default
args=(sys.stdout,)

[handler_file]
class=FileHandler
formatter=default
args=('app.log', 'a')

[formatter_default]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Monitoring with Prometheus
```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Start metrics server
start_http_server(9090)
```

## Scaling Considerations

### Horizontal Scaling
```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-agent
  template:
    metadata:
      labels:
        app: voice-agent
    spec:
      containers:
      - name: backend
        image: voice-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: groq
```

### Load Balancing
```yaml
# kubernetes-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: voice-agent-service
spec:
  type: LoadBalancer
  selector:
    app: voice-agent
  ports:
    - port: 80
      targetPort: 8000
  sessionAffinity: ClientIP
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```bash
# Check CORS settings
curl -I https://api.example.com \
  -H "Origin: https://app.example.com"

# Verify WebSocket upgrade
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  https://api.example.com/socket.io/
```

#### API Key Issues
```python
# Test API keys
python -c "
from src.services.groq_whisper import GroqWhisperClient
client = GroqWhisperClient()
print(client.test_connection())
"
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats

# Increase container memory
docker run -m 2g voice-agent
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Environment variable
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Security Best Practices

1. **Use HTTPS/WSS in production**
2. **Rotate API keys regularly**
3. **Implement rate limiting**
4. **Use environment variables for secrets**
5. **Enable CORS only for trusted origins**
6. **Implement request validation**
7. **Use secure WebSocket connections**
8. **Monitor for suspicious activity**

## Backup & Recovery

### Database Backup
```bash
# Backup conversation logs
pg_dump -U postgres -d voice_agent > backup.sql

# Restore
psql -U postgres -d voice_agent < backup.sql
```

### Configuration Backup
```bash
# Backup environment
railway variables export > railway-vars.json

# Restore
railway variables import railway-vars.json
```

---

*For additional deployment options, see the infrastructure code in the `deploy/` directory.*