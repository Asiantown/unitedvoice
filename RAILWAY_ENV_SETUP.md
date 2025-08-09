# Railway Environment Variables Setup

## You're in the right place! Follow these steps:

### 1. Add Each Variable (in the Shared Variables section you're viewing)

Click in the fields and add these one by one:

| VARIABLE_NAME | VALUE |
|--------------|--------|
| `GROQ_API_KEY` | Your Groq API key from groq.com |
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key from elevenlabs.io |
| `CORS_ORIGINS` | `*` (for testing) or `https://your-app.vercel.app` (for production) |
| `PORT` | `8000` |
| `ENVIRONMENT` | `production` |

### 2. Optional Variables (if you have them):

| VARIABLE_NAME | VALUE |
|--------------|--------|
| `SERPAPI_API_KEY` | Your SerpAPI key (if you have one) |
| `GOOGLE_FLIGHTS_API_KEY` | Your Google Flights API key (if you have one) |
| `LOG_LEVEL` | `INFO` |
| `MAX_CONNECTIONS` | `1000` |

### 3. How to Add:
1. Type the variable name in the left field (e.g., `GROQ_API_KEY`)
2. Type or paste the value in the right field 
3. Click the "Add" button
4. Repeat for each variable

### 4. After Adding All Variables:
- The variables will automatically apply to your deployment
- You can continue with the deployment process

### Example:
```
VARIABLE_NAME: GROQ_API_KEY
VALUE: gsk_abc123xyz789...

VARIABLE_NAME: ELEVENLABS_API_KEY  
VALUE: xi_def456...

VARIABLE_NAME: CORS_ORIGINS
VALUE: *
```

### Important Notes:
- Don't include quotes around the values
- Make sure there are no extra spaces
- The variables will be encrypted and secure
- Changes take effect on the next deployment

Once you've added all the environment variables, you can continue with the deployment!