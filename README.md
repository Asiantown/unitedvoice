# United Voice Agent 🎤 ✈️

AI-powered voice booking agent for United Airlines - Real-time voice conversations with intelligent flight booking assistance.

## 🚀 Live Demo

**Production URL**: [https://unitedvoice-p41.vercel.app](https://unitedvoice-p41.vercel.app)

## ✨ Features

- **Voice-First Interface**: Natural voice conversations with AI agent
- **Real-Time Communication**: WebSocket-based instant responses
- **Flight Booking Flow**: Complete United Airlines booking experience
- **Multi-Modal Input**: Voice or text input options
- **High-Quality Voice**: ElevenLabs text-to-speech
- **Intelligent Understanding**: Groq-powered language processing

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 15.4 with TypeScript
- **UI**: Tailwind CSS with glass morphism design
- **Real-Time**: Socket.IO client
- **Deployment**: Vercel

### Backend
- **Framework**: Python FastAPI with Socket.IO
- **AI/ML**: Groq (Whisper & LLaMA), ElevenLabs TTS
- **Deployment**: Railway
- **WebSocket**: Real-time bidirectional communication

## 📦 Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/Asiantown/unitedvoice.git
cd unitedvoice
```

2. **Set environment variables** (see .env.example)

3. **Deploy to Railway** (Backend) and **Vercel** (Frontend)

## 🔑 Environment Variables

### Backend (Railway)
- GROQ_API_KEY
- ELEVENLABS_API_KEY
- CORS_ORIGINS
- ENVIRONMENT=production

### Frontend (Vercel)
- NEXT_PUBLIC_WS_URL

---

Built with ❤️ for United Airlines customers
