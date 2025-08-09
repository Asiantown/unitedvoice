'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Wifi, WifiOff, User, Bot, Keyboard, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import io, { Socket } from 'socket.io-client';
import VoiceOrbWrapper from '@/components/VoiceOrbWrapper';
import { SoundEffects } from '@/lib/soundEffects';

// Force dynamic rendering to avoid SSG issues with Three.js
export const dynamic = 'force-dynamic';

interface Message {
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  id: string;
}

// Floating particles component
const FloatingParticles = ({ count = 50 }: { count?: number }) => {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-blue-400/20 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -20, 0],
            x: [0, Math.random() * 10 - 5, 0],
            opacity: [0.2, 0.8, 0.2],
            scale: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 2,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

// Loading screen component
const LoadingScreen = ({ isVisible }: { isVisible: boolean }) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8 }}
          className="fixed inset-0 z-50 bg-black flex items-center justify-center"
        >
          <div className="text-center">
            <motion.div
              animate={{ 
                rotate: 360,
                scale: [1, 1.1, 1] 
              }}
              transition={{ 
                rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                scale: { duration: 1, repeat: Infinity, ease: "easeInOut" }
              }}
              className="w-24 h-24 mx-auto mb-6 rounded-full glow-blue"
              style={{
                background: 'linear-gradient(45deg, #4a90ff, #a855f7, #ec4899)',
              }}
            />
            <motion.h2
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-2xl font-bold text-gradient mb-2"
            >
              United Voice Agent
            </motion.h2>
            <motion.p
              animate={{ opacity: [0.3, 0.7, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
              className="text-gray-400"
            >
              Initializing premium experience...
            </motion.p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Enhanced keyboard indicator
const KeyboardIndicator = ({ isRecording, recordingTime }: { isRecording: boolean; recordingTime: number }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1 }}
      className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-40"
    >
      <div className="glass-ultra px-6 py-3 rounded-2xl flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Keyboard className="w-4 h-4 text-blue-400" />
          <motion.kbd
            animate={isRecording ? { 
              boxShadow: [
                "0 0 0 0 rgba(59, 130, 246, 0.7)",
                "0 0 0 8px rgba(59, 130, 246, 0)",
              ]
            } : {}}
            transition={{ duration: 1, repeat: isRecording ? Infinity : 0 }}
            className="px-3 py-1 bg-gray-900 border border-blue-500/50 rounded text-blue-300 font-mono"
          >
            SPACE
          </motion.kbd>
          <span className="text-sm text-gray-300">
            {isRecording ? 'Release to send' : 'Hold to talk'}
          </span>
        </div>
        
        <AnimatePresence>
          {isRecording && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="flex items-center gap-2 border-l border-gray-600 pl-4"
            >
              <Clock className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-300 font-mono">
                {recordingTime.toFixed(1)}s
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

// Enhanced error state component
const EnhancedErrorState = ({ error, onRetry }: { error: string; onRetry: () => void }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm"
    >
      <div className="glass-ultra rounded-3xl p-8 max-w-md mx-4 text-center">
        <motion.div
          animate={{ 
            rotate: [0, 10, -10, 0],
            scale: [1, 1.1, 1]
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center"
        >
          <MicOff className="w-8 h-8 text-red-400" />
        </motion.div>
        
        <h3 className="text-xl font-bold mb-4 text-gradient-purple">
          Connection Issue
        </h3>
        
        <p className="text-gray-300 mb-6 leading-relaxed">
          {error}
        </p>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onRetry}
          className="glass-button-enhanced px-6 py-3 rounded-xl text-white font-medium hover:glow-blue transition-all"
        >
          Try Again
        </motion.button>
      </div>
    </motion.div>
  );
};

export default function VoicePremiumPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState('Connecting...');
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showTypingIndicator, setShowTypingIndicator] = useState(false);
  const [soundEffectsEnabled, setSoundEffectsEnabled] = useState(true);
  
  const socketRef = useRef<Socket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingTimeRef = useRef<NodeJS.Timeout | null>(null);
  const soundEffects = useRef<SoundEffects | null>(null);

  // Initialize sound effects on client side only
  useEffect(() => {
    if (typeof window !== 'undefined') {
      soundEffects.current = SoundEffects.getInstance();
    }
  }, []);

  // Initialize loading screen
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Recording time tracker
  useEffect(() => {
    if (isRecording) {
      const startTime = Date.now();
      recordingTimeRef.current = setInterval(() => {
        setRecordingTime((Date.now() - startTime) / 1000);
      }, 100);
    } else {
      if (recordingTimeRef.current) {
        clearInterval(recordingTimeRef.current);
        recordingTimeRef.current = null;
      }
      setRecordingTime(0);
    }

    return () => {
      if (recordingTimeRef.current) {
        clearInterval(recordingTimeRef.current);
      }
    };
  }, [isRecording]);

  // Initialize audio context for level monitoring
  const initializeAudioContext = useCallback(async (stream: MediaStream) => {
    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      
      const updateAudioLevel = () => {
        if (!analyserRef.current) return;
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((acc, value) => acc + value, 0) / dataArray.length;
        setAudioLevel(average / 255);
        
        if (isRecording) {
          requestAnimationFrame(updateAudioLevel);
        }
      };
      
      updateAudioLevel();
    } catch (error) {
      console.warn('Audio context initialization failed:', error);
    }
  }, [isRecording]);

  // Enhanced audio playback
  const playAudioResponse = useCallback(async (audioData: string) => {
    setAudioError(null);
    setShowTypingIndicator(false);
    
    if (isMuted) return;
    
    try {
      const binaryString = atob(audioData);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const formats = [
        { type: 'audio/mpeg', ext: 'mp3' },
        { type: 'audio/wav', ext: 'wav' },
        { type: 'audio/ogg', ext: 'ogg' },
        { type: 'audio/webm', ext: 'webm' }
      ];
      
      let audioPlayed = false;
      
      for (const format of formats) {
        if (audioPlayed) break;
        
        try {
          const blob = new Blob([bytes], { type: format.type });
          const url = URL.createObjectURL(blob);
          
          const audio = new Audio();
          audio.volume = volume;
          audio.preload = 'auto';
          
          const canPlay = audio.canPlayType(format.type);
          if (canPlay === '' || canPlay === 'no') {
            URL.revokeObjectURL(url);
            continue;
          }
          
          await new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
              URL.revokeObjectURL(url);
              reject(new Error(`Audio load timeout for ${format.ext}`));
            }, 3000);
            
            audio.oncanplaythrough = () => {
              clearTimeout(timeoutId);
              resolve(void 0);
            };
            
            audio.onerror = (e) => {
              clearTimeout(timeoutId);
              URL.revokeObjectURL(url);
              reject(new Error(`${format.ext} format not supported`));
            };
            
            audio.src = url;
          });
          
          await audio.play();
          audioPlayed = true;
          audioRef.current = audio;
          
          audio.onended = () => {
            URL.revokeObjectURL(url);
            audioRef.current = null;
          };
          
        } catch (formatError) {
          continue;
        }
      }
      
      if (!audioPlayed) {
        try {
          const dataUrl = `data:audio/mpeg;base64,${audioData}`;
          const audio = new Audio(dataUrl);
          audio.volume = volume;
          await audio.play();
          audioRef.current = audio;
          audioPlayed = true;
          
          audio.onended = () => {
            audioRef.current = null;
          };
        } catch (dataUrlError) {
          throw new Error('All audio playback methods failed');
        }
      }
      
    } catch (error) {
      console.error('Audio playback error:', error);
      setAudioError('Failed to play audio response');
    }
  }, [volume, isMuted]);

  // Connect to WebSocket
  useEffect(() => {
    setStatus('Connecting...');
    
    socketRef.current = io('http://localhost:8000', {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      setStatus('Connected');
      setAudioError(null);
    });

    socketRef.current.on('disconnect', (reason) => {
      setIsConnected(false);
      setStatus(`Disconnected: ${reason}`);
    });

    socketRef.current.on('connect_error', (error) => {
      setIsConnected(false);
      setStatus('Connection failed');
      console.error('Socket connection error:', error);
    });

    socketRef.current.on('agent_response', (data: any) => {
      const message: Message = {
        text: data.text,
        sender: 'agent',
        timestamp: new Date(),
        id: `agent-${Date.now()}-${Math.random()}`
      };
      
      setMessages(prev => [...prev, message]);
      setIsProcessing(false);
      setShowTypingIndicator(false);
      
      if (data.audio) {
        playAudioResponse(data.audio);
      }
    });

    socketRef.current.on('transcription', (data: any) => {
      const message: Message = {
        text: data.text,
        sender: 'user',
        timestamp: new Date(),
        id: `user-${Date.now()}-${Math.random()}`
      };
      
      setMessages(prev => [...prev, message]);
      setIsProcessing(true);
      setShowTypingIndicator(true);
    });

    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      socketRef.current?.disconnect();
    };
  }, [playAudioResponse]);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      await initializeAudioContext(stream);

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
          ? 'audio/webm;codecs=opus'
          : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/wav'
      });
      
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mediaRecorderRef.current?.mimeType || 'audio/webm' 
        });
        sendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
        setAudioLevel(0);
        
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
      };

      mediaRecorderRef.current.start(100);
      setIsRecording(true);
      setStatus('Listening...');
      setAudioError(null);
    } catch (error) {
      console.error('Error starting recording:', error);
      setStatus('Microphone access denied');
      setAudioError('Please allow microphone access to use voice chat');
    }
  }, [initializeAudioContext]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('Processing...');
      setIsProcessing(true);
    }
  }, [isRecording]);

  // Send audio to backend
  const sendAudio = useCallback((audioBlob: Blob) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = reader.result?.toString().split(',')[1];
      if (base64Audio && socketRef.current && isConnected) {
        socketRef.current.emit('audio_data', {
          audio: base64Audio,
          format: audioBlob.type || 'audio/webm',
          timestamp: new Date().toISOString(),
          size: audioBlob.size,
          duration: 0,
        });
      } else if (!isConnected) {
        setStatus('Connection lost - please reconnect');
        setIsProcessing(false);
      }
    };
    
    reader.onerror = () => {
      console.error('Failed to read audio blob');
      setStatus('Audio processing failed');
      setIsProcessing(false);
    };
    
    reader.readAsDataURL(audioBlob);
  }, [isConnected]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat && !isRecording && isConnected) {
        e.preventDefault();
        startRecording();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && isRecording) {
        e.preventDefault();
        stopRecording();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isRecording, isConnected, startRecording, stopRecording]);

  const retryConnection = useCallback(() => {
    setAudioError(null);
    window.location.reload();
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Loading Screen */}
      <LoadingScreen isVisible={isLoading} />

      {/* Enhanced Error State */}
      <AnimatePresence>
        {audioError && (
          <EnhancedErrorState 
            error={audioError} 
            onRetry={retryConnection}
          />
        )}
      </AnimatePresence>

      {/* Ultra-premium animated gradient background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black" />
        <motion.div 
          animate={{ 
            background: [
              'radial-gradient(circle at 20% 50%, rgba(139,92,246,0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 50%, rgba(59,130,246,0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 50% 80%, rgba(236,72,153,0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 50%, rgba(139,92,246,0.15) 0%, transparent 50%)',
            ]
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-0"
        />
        <motion.div
          animate={{ 
            rotate: [0, 360],
            scale: [1, 1.1, 1] 
          }}
          transition={{ 
            rotate: { duration: 60, repeat: Infinity, ease: "linear" },
            scale: { duration: 8, repeat: Infinity, ease: "easeInOut" }
          }}
          className="absolute inset-0 opacity-30"
          style={{
            background: 'conic-gradient(from 0deg, transparent, rgba(139,92,246,0.1), transparent, rgba(59,130,246,0.1), transparent)',
          }}
        />
        
        {/* Floating Particles */}
        <FloatingParticles count={40} />
      </div>
      
      {/* Main Content */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoading ? 0 : 1 }}
        transition={{ duration: 1, delay: isLoading ? 0 : 0.5 }}
        className="relative z-10 min-h-screen flex flex-col"
      >
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="text-center pt-12 pb-8"
        >
          <motion.h1 
            animate={{ 
              textShadow: [
                "0 0 20px rgba(139,92,246,0.5)",
                "0 0 40px rgba(59,130,246,0.5)",
                "0 0 20px rgba(139,92,246,0.5)",
              ]
            }}
            transition={{ duration: 3, repeat: Infinity }}
            className="text-6xl md:text-7xl font-bold mb-6 text-gradient"
          >
            United Voice Agent
          </motion.h1>
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
            className="inline-block glass-ultra px-6 py-3 rounded-2xl mb-8"
          >
            <p className="text-gray-300 text-lg font-medium">
              Premium Voice Experience
            </p>
          </motion.div>
          
          {/* Enhanced Status Bar */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.4, duration: 0.6 }}
            className="flex items-center justify-center gap-8 mb-6"
          >
            <div className="flex items-center gap-3">
              <motion.div
                animate={isConnected ? { scale: [1, 1.2, 1] } : {}}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {isConnected ? (
                  <Wifi className="w-5 h-5 text-green-400" />
                ) : (
                  <WifiOff className="w-5 h-5 text-red-400" />
                )}
              </motion.div>
              <span className={`text-sm font-medium ${
                isConnected ? 'text-green-400' : 'text-red-400'
              }`}>
                {status}
              </span>
            </div>
            
            <div className="flex items-center gap-3">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsMuted(!isMuted)}
                className="p-2 rounded-xl glass-ultra hover:glow-blue transition-all"
              >
                {isMuted ? (
                  <VolumeX className="w-5 h-5 text-gray-400" />
                ) : (
                  <Volume2 className="w-5 h-5 text-blue-400" />
                )}
              </motion.button>
              <div className="glass-ultra rounded-xl px-4 py-2">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                  className="w-20 accent-blue-500"
                  disabled={isMuted}
                />
              </div>
            </div>
          </motion.div>
        </motion.div>
        
        {/* Main Content Area */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="w-full max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
            {/* Enhanced Voice Orb */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.5, rotateY: -90 }}
              animate={{ opacity: 1, scale: 1, rotateY: 0 }}
              transition={{ 
                duration: 1.2, 
                delay: 1.6,
                type: "spring",
                stiffness: 100
              }}
              className="flex justify-center lg:justify-end order-2 lg:order-1"
            >
              <div className="relative w-96 h-96 lg:w-[28rem] lg:h-[28rem]">
                {/* Outer glow rings */}
                <motion.div
                  animate={{ 
                    rotate: [0, 360],
                    scale: isRecording ? [1, 1.2, 1] : [1, 1.05, 1] 
                  }}
                  transition={{ 
                    rotate: { duration: 20, repeat: Infinity, ease: "linear" },
                    scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                  }}
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'conic-gradient(from 0deg, transparent, rgba(139,92,246,0.3), transparent)',
                    filter: 'blur(2px)',
                  }}
                />
                
                <motion.div
                  animate={!isRecording ? { 
                    scale: [1, 1.1, 1],
                    opacity: [0.5, 1, 0.5] 
                  } : {}}
                  transition={{ 
                    duration: 3, 
                    repeat: Infinity, 
                    ease: "easeInOut" 
                  }}
                  className="absolute inset-4 rounded-full glow-blue opacity-20"
                />
                
                <VoiceOrbWrapper
                  state={isRecording ? 'listening' : isProcessing ? 'thinking' : 'idle'}
                  audioLevel={audioLevel}
                  size="xl"
                  isRecording={isRecording}
                  isConnected={isConnected}
                  className="w-full h-full"
                />
                
                {/* Floating Record Button */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onMouseDown={() => isConnected && !isRecording && startRecording()}
                    onMouseUp={() => isRecording && stopRecording()}
                    onMouseLeave={() => isRecording && stopRecording()}
                    onTouchStart={(e) => {
                      e.preventDefault();
                      isConnected && !isRecording && startRecording();
                    }}
                    onTouchEnd={(e) => {
                      e.preventDefault();
                      isRecording && stopRecording();
                    }}
                    disabled={!isConnected}
                    className={`pointer-events-auto p-6 rounded-full glass-ultra transition-all duration-300 ${
                      isRecording 
                        ? 'glow-pink scale-110' 
                        : isConnected
                          ? 'glow-blue hover:scale-105'
                          : 'opacity-50 cursor-not-allowed'
                    }`}
                    style={{
                      boxShadow: isRecording 
                        ? '0 0 40px rgba(236,72,153,0.6), 0 0 80px rgba(236,72,153,0.4)'
                        : '0 0 30px rgba(59,130,246,0.4)',
                    }}
                  >
                    <AnimatePresence mode="wait">
                      {isRecording ? (
                        <motion.div
                          key="recording"
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          className="w-8 h-8 bg-red-500 rounded-full recording-indicator"
                        />
                      ) : isProcessing ? (
                        <motion.div
                          key="processing"
                          initial={{ scale: 0, rotate: 0 }}
                          animate={{ scale: 1, rotate: 360 }}
                          exit={{ scale: 0 }}
                          transition={{ rotate: { duration: 1, repeat: Infinity, ease: "linear" } }}
                          className="w-8 h-8"
                        >
                          <div className="w-full h-full border-3 border-blue-500 border-t-transparent rounded-full" />
                        </motion.div>
                      ) : (
                        <motion.div
                          key="idle"
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                        >
                          <Mic className="w-8 h-8 text-blue-400" />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.button>
                </div>
              </div>
            </motion.div>
            
            {/* Enhanced Messages Panel */}
            <motion.div 
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 1.8 }}
              className="order-1 lg:order-2 h-full max-h-[700px] flex flex-col"
            >
              <div className="glass-ultra rounded-3xl p-8 flex-1 flex flex-col min-h-[500px]">
                <h2 className="text-2xl font-bold mb-6 text-gradient-blue flex items-center gap-3">
                  <Bot className="w-6 h-6" />
                  Conversation
                </h2>
                
                <div className="flex-1 overflow-y-auto space-y-6 pr-3">
                  <AnimatePresence>
                    {messages.length === 0 ? (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-center h-full text-gray-400 text-center"
                      >
                        <div>
                          <motion.div 
                            animate={{ 
                              scale: [1, 1.1, 1],
                              rotate: [0, 5, -5, 0]
                            }}
                            transition={{ duration: 3, repeat: Infinity }}
                            className="w-20 h-20 mx-auto mb-6 rounded-full glass-ultra flex items-center justify-center glow-blue"
                          >
                            <Mic className="w-10 h-10 text-blue-400" />
                          </motion.div>
                          <p className="text-lg font-medium">Ready to chat!</p>
                          <p className="text-sm mt-2 opacity-70">Hold the microphone or press SPACE to start</p>
                        </div>
                      </motion.div>
                    ) : (
                      messages.map((msg, index) => (
                        <motion.div
                          key={msg.id}
                          initial={{ opacity: 0, y: 30, scale: 0.9 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: -30, scale: 0.9 }}
                          transition={{ duration: 0.4, delay: index * 0.1 }}
                          className={`flex items-start gap-4 ${
                            msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
                          }`}
                        >
                          <motion.div 
                            whileHover={{ scale: 1.1 }}
                            className={`flex-shrink-0 w-10 h-10 rounded-full glass-ultra flex items-center justify-center ${
                              msg.sender === 'user' ? 'glow-purple' : 'glow-blue'
                            }`}
                          >
                            {msg.sender === 'user' ? (
                              <User className="w-5 h-5 text-purple-400" />
                            ) : (
                              <Bot className="w-5 h-5 text-blue-400" />
                            )}
                          </motion.div>
                          
                          <motion.div 
                            whileHover={{ y: -2 }}
                            className={`flex-1 max-w-[85%] ${
                              msg.sender === 'user' 
                                ? 'message-bubble-user-premium text-white' 
                                : 'message-bubble-agent-premium text-gray-100'
                            } px-6 py-4 rounded-2xl`}
                          >
                            <p className="leading-relaxed">{msg.text}</p>
                            <p className="text-xs opacity-70 mt-2">
                              {msg.timestamp.toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </p>
                          </motion.div>
                        </motion.div>
                      ))
                    )}
                  </AnimatePresence>
                  
                  {/* Enhanced Typing Indicator */}
                  <AnimatePresence>
                    {showTypingIndicator && (
                      <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -30 }}
                        className="flex items-start gap-4"
                      >
                        <div className="flex-shrink-0 w-10 h-10 rounded-full glass-ultra flex items-center justify-center glow-blue">
                          <Bot className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="message-bubble-agent-premium px-6 py-4 rounded-2xl">
                          <div className="flex items-center gap-3">
                            <div className="flex gap-1">
                              {[0, 1, 2].map((i) => (
                                <motion.div
                                  key={i}
                                  animate={{ scale: [1, 1.5, 1] }}
                                  transition={{
                                    duration: 1,
                                    repeat: Infinity,
                                    delay: i * 0.2,
                                  }}
                                  className="w-2 h-2 bg-blue-400 rounded-full"
                                />
                              ))}
                            </div>
                            <span className="text-sm text-gray-400">AI is thinking...</span>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Enhanced Audio Level Visualizer */}
        <AnimatePresence>
          {audioLevel > 0 && isRecording && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="fixed bottom-32 left-1/2 transform -translate-x-1/2 z-30"
            >
              <div className="glass-ultra rounded-2xl px-8 py-4">
                <div className="flex items-center justify-center gap-1">
                  <span className="text-xs text-gray-400 mr-4">Audio Level:</span>
                  {Array.from({ length: 32 }).map((_, i) => (
                    <motion.div
                      key={i}
                      animate={{
                        height: i < audioLevel * 32 
                          ? `${20 + (audioLevel * 20)}px`
                          : '4px',
                        backgroundColor: i < audioLevel * 32 
                          ? `hsl(${240 + i * 3}, 80%, 60%)`
                          : '#374151'
                      }}
                      transition={{ duration: 0.1 }}
                      className="w-1 rounded-full"
                      style={{ minHeight: '4px' }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Keyboard Indicator */}
      <KeyboardIndicator isRecording={isRecording} recordingTime={recordingTime} />
    </div>
  );
}