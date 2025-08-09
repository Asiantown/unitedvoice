# United Airlines Voice Agent Frontend

A premium, AI-powered voice interface for United Airlines customer service built with Next.js 14, React 18, and cutting-edge web technologies. This frontend provides a seamless, 11.ai-inspired user experience with advanced voice interactions, real-time audio visualization, and comprehensive mobile support.

## Features

### Core Voice Features
- **Advanced Voice Interface**: Real-time speech-to-text with confidence scoring
- **Audio Waveform Visualization**: Dynamic audio processing with 32-band frequency visualization
- **Multi-State Animations**: Smooth transitions between idle, listening, processing, and speaking states
- **WebSocket Integration**: Real-time bidirectional communication with voice backend
- **HTTP Fallback**: Automatic fallback to REST API when WebSocket is unavailable

### Premium UI/UX
- **11.ai-Inspired Design**: Dark theme with elegant glass morphism effects
- **Particle Effects**: Dynamic orbital particles and energy orbs responding to voice states  
- **Smooth Animations**: 60fps optimized animations using Framer Motion
- **Mobile-First Responsive**: Optimized for all screen sizes with touch gestures
- **Keyboard Shortcuts**: Space to record, Escape to close, arrow keys for navigation
- **Sound Effects**: Optional audio feedback for all interactions

### Advanced Interactions
- **Touch Gestures**: Swipe to close, pull to refresh, double-tap to expand
- **Smart Loading States**: Skeleton loaders, typing indicators, connection status
- **Error Recovery**: Automatic retry mechanisms with exponential backoff
- **Performance Monitoring**: Real-time FPS and memory usage tracking
- **Battery Adaptation**: Performance scaling based on device battery level

### Conversation Management  
- **Multi-Tab Interface**: Separate views for conversation, booking, and flight results
- **Message Threading**: Real-time chat with confidence scores and metadata
- **State Persistence**: Conversation state maintained across sessions
- **Export Capabilities**: Save conversation history and booking details

## Architecture

### Project Structure
```
src/
├── app/                    # Next.js 14 app router
│   ├── api/               # API routes (health, audio upload, websocket)
│   ├── globals.css        # Global styles and animations
│   ├── layout.tsx         # Root layout with providers
│   └── page.tsx           # Main application entry point
├── components/
│   ├── ui/                # Reusable UI components
│   │   ├── CircularVisualizer.tsx  # Advanced voice visualizer
│   │   └── LoadingStates.tsx       # Loading/error components
│   ├── voice/             # Voice-specific components  
│   │   ├── VoiceInterface.tsx      # Main voice interface
│   │   ├── ConversationDisplay.tsx # Chat message display
│   │   ├── BookingSummary.tsx      # Booking information
│   │   └── FlightOptions.tsx       # Flight search results
│   └── layout/            # Layout components
│       └── Header.tsx     # Application header
├── hooks/                 # Custom React hooks
│   ├── useSocket.ts       # WebSocket connection management
│   ├── useGestures.ts     # Touch gesture and keyboard handling
│   ├── useSoundEffects.ts # Audio feedback system
│   ├── usePerformance.ts  # Performance monitoring utilities  
│   └── useConnectionStatus.ts  # Network connectivity tracking
├── store/                 # State management
│   └── useAppStore.ts     # Zustand global state store
├── types/                 # TypeScript type definitions
│   └── index.ts           # Shared types and interfaces
├── utils/                 # Utility functions
│   ├── formatters.ts      # Data formatting utilities
│   └── mockData.ts        # Development mock data
└── lib/                   # Configuration and constants
    └── config.ts          # Application configuration
```

### Key Technologies
- **Next.js 14**: React framework with App Router
- **React 18**: Latest React with concurrent features  
- **TypeScript**: Full type safety throughout
- **Tailwind CSS**: Utility-first styling with custom design system
- **Framer Motion**: Advanced animations and gesture handling
- **Zustand**: Lightweight state management
- **Socket.IO**: Real-time WebSocket communication
- **Web Audio API**: Audio processing and visualization

## Development

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Modern browser with WebRTC support

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Development Commands
```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server  
npm start

# Lint code
npm run lint
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Performance Optimization

### Built-in Optimizations
- **Memoized Components**: React.memo on all major components
- **Throttled Callbacks**: Prevents excessive function calls  
- **Lazy Loading**: Components loaded on-demand
- **Animation Optimization**: RequestAnimationFrame for 60fps
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Automatic route-based splitting

### Mobile Optimizations
- **Touch-First Design**: Optimized for mobile interactions
- **Viewport Adaptation**: Responsive breakpoints for all devices
- **Performance Scaling**: Reduced animations on low-power devices
- **Offline Support**: Service worker for basic offline functionality

## Deployment

### Production Build
```bash
# Create optimized production build
npm run build

# Test production build locally
npm start
```

### Vercel Deployment (Recommended)
```bash
# Deploy to Vercel
npx vercel --prod

# Or connect GitHub repository for automatic deployments
```

## API Integration

### WebSocket Events
```typescript
// Outgoing Events
socket.emit('audio_data', { audio: base64Audio, format: 'webm' });
socket.emit('reset_conversation');
socket.emit('get_session_state');

// Incoming Events  
socket.on('transcription', (data) => { /* Handle transcription */ });
socket.on('agent_response', (data) => { /* Handle AI response */ });
socket.on('status_update', (data) => { /* Handle status changes */ });
```

### REST API Fallback
```typescript
// Audio upload fallback
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.webm');

const response = await fetch('/api/audio/upload', {
  method: 'POST',
  body: formData,
});
```

## Browser Support

### Minimum Requirements
- **Chrome 90+**: Full feature support
- **Firefox 88+**: Full feature support
- **Safari 14+**: Limited WebRTC support
- **Edge 90+**: Full feature support

### Progressive Enhancement
- **WebRTC**: Voice recording with microphone access
- **WebSocket**: Real-time communication (HTTP fallback available)
- **Service Worker**: Offline support and caching
- **Web Audio API**: Audio visualization (graceful degradation)

## Troubleshooting

### Common Issues

**Microphone not working**
- Check browser permissions
- Ensure HTTPS in production
- Verify getUserMedia support

**WebSocket connection fails**  
- Check firewall settings
- Verify WebSocket URL
- Falls back to HTTP automatically

**Poor performance on mobile**
- Enable performance monitoring
- Check battery adaptation settings
- Reduce animation complexity

**Audio visualization not showing**
- Verify Web Audio API support
- Check audio data processing
- Enable debug mode for logging

---

Built with ❤️ by the United Airlines Digital Experience Team
