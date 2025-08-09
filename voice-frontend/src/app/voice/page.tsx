'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, Loader2, Volume2, VolumeX, Wifi, WifiOff, Play, AlertCircle } from 'lucide-react';
import io, { Socket } from 'socket.io-client';

interface Message {
  text: string;
  sender: 'user' | 'agent';
  id: string;
  audio?: string;
  audioFormat?: string;
}

export default function VoicePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState('Connecting...');
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [pendingAudio, setPendingAudio] = useState<{audio: string, format: string} | null>(null);
  
  const socketRef = useRef<Socket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const isMutedRef = useRef(false);
  const audioEnabledRef = useRef(false);
  const audioElementsRef = useRef<Set<HTMLAudioElement>>(new Set());

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Stop all currently playing audio elements
  const stopAllAudio = () => {
    console.log(`🔇 Stopping ${audioElementsRef.current.size} audio elements`);
    audioElementsRef.current.forEach(audio => {
      // Force stop regardless of state
      try {
        audio.pause();
        audio.currentTime = 0;
        // Remove event listeners to prevent cleanup issues
        audio.onended = null;
        audio.onerror = null;
        audio.onpause = null;
      } catch (e) {
        console.error('Error stopping audio:', e);
      }
    });
    // Clear the tracking set after stopping all audio
    audioElementsRef.current.clear();
    console.log('✅ All audio stopped and cleared');
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Sync refs with state values
  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  useEffect(() => {
    audioEnabledRef.current = audioEnabled;
  }, [audioEnabled]);

  // Initialize audio context on user interaction
  const initializeAudio = async () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
    }
    setAudioEnabled(true);
    console.log('✅ Audio initialized');
    
    // Play any pending audio
    if (pendingAudio) {
      playAudioSafely(pendingAudio.audio, pendingAudio.format);
      setPendingAudio(null);
    }
  };

  // Connect to WebSocket
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
    console.log('Connecting to WebSocket at:', wsUrl);
    socketRef.current = io(wsUrl, {
      transports: ['websocket', 'polling'],
    });

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      setStatus('Connected');
      console.log('✅ Connected to backend');
    });

    socketRef.current.on('disconnect', () => {
      setIsConnected(false);
      setStatus('Disconnected');
      console.log('❌ Disconnected from backend');
    });

    socketRef.current.on('connected', (data: any) => {
      console.log('Server greeting:', data);
    });

    socketRef.current.on('agent_response', (data: any) => {
      console.log('Agent response received:', data);
      
      // Create a unique ID using timestamp and random component to prevent duplicates
      const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}-agent`;
      
      const newMessage: Message = {
        text: data.text,
        sender: 'agent',
        id: messageId,
        audio: data.audio,
        audioFormat: data.audio_format || 'mp3'
      };
      
      // Check for duplicate messages before adding
      setMessages(prev => {
        // Check if we already have this exact message text recently (within last 2 seconds)
        const recentDuplicate = prev.find(msg => 
          msg.sender === 'agent' && 
          msg.text === data.text && 
          Math.abs(parseInt(msg.id.split('-')[0]) - Date.now()) < 2000
        );
        
        if (recentDuplicate) {
          console.log('🚫 Duplicate agent message filtered:', data.text);
          return prev;
        }
        
        return [...prev, newMessage];
      });
      
      // Handle audio - use refs instead of state values
      if (data.audio && !isMutedRef.current) {
        if (audioEnabledRef.current) {
          playAudioSafely(data.audio, data.audio_format || 'mp3');
        } else {
          // Store audio to play after user enables it
          setPendingAudio({ audio: data.audio, format: data.audio_format || 'mp3' });
        }
      }
    });

    socketRef.current.on('transcription', (data: any) => {
      console.log('Transcription received:', data);
      
      // Create a unique ID using timestamp and random component
      const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}-user`;
      
      const newMessage: Message = { 
        text: data.text, 
        sender: 'user',
        id: messageId
      };
      
      // Check for duplicate transcriptions before adding
      setMessages(prev => {
        // Check if we already have this exact transcription recently (within last 1 second)
        const recentDuplicate = prev.find(msg => 
          msg.sender === 'user' && 
          msg.text === data.text && 
          Math.abs(parseInt(msg.id.split('-')[0]) - Date.now()) < 1000
        );
        
        if (recentDuplicate) {
          console.log('🚫 Duplicate transcription filtered:', data.text);
          return prev;
        }
        
        return [...prev, newMessage];
      });
    });

    socketRef.current.on('status_update', (data: any) => {
      setStatus(data.message);
    });

    socketRef.current.on('error', (error: any) => {
      console.error('Socket error:', error);
      setStatus('Error: ' + (error.message || 'Connection failed'));
    });

    return () => {
      socketRef.current?.disconnect();
      // Clean up all audio elements on component unmount
      stopAllAudio();
      audioElementsRef.current.clear();
    };
  }, []); // Removed isMuted and audioEnabled from dependencies

  // Safe audio playback
  const playAudioSafely = async (base64Audio: string, format: string = 'mp3') => {
    try {
      console.log(`Playing audio (format: ${format})`);
      
      // Convert base64 to blob
      const byteCharacters = atob(base64Audio);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: `audio/${format}` });
      const audioUrl = URL.createObjectURL(blob);
      
      const audio = new Audio(audioUrl);
      audio.volume = volume;
      
      // Add audio element to tracking
      audioElementsRef.current.add(audio);
      
      // Clean up after playing
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        audioElementsRef.current.delete(audio);
      };
      
      // Handle errors and cleanup
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        audioElementsRef.current.delete(audio);
      };
      
      // Clean up when audio is paused (e.g., via interruption)
      audio.onpause = () => {
        // Only clean up if the audio was stopped at beginning (interrupted)
        if (audio.currentTime === 0) {
          URL.revokeObjectURL(audioUrl);
          audioElementsRef.current.delete(audio);
        }
      };
      
      // Play with user gesture context
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log('✅ Audio playing');
          })
          .catch(error => {
            console.error('Audio play failed:', error);
            // Clean up on play failure
            audioElementsRef.current.delete(audio);
            URL.revokeObjectURL(audioUrl);
            setPendingAudio({ audio: base64Audio, format });
          });
      }
    } catch (error) {
      console.error('Audio playback error:', error);
    }
  };

  // Play specific message audio
  const playMessageAudio = (msg: Message) => {
    // Stop any currently playing audio first
    stopAllAudio();
    
    if (msg.audio && msg.audioFormat) {
      if (!audioEnabled) {
        initializeAudio().then(() => {
          playAudioSafely(msg.audio!, msg.audioFormat!);
        });
      } else {
        playAudioSafely(msg.audio, msg.audioFormat);
      }
    }
  };

  // Start recording (also initializes audio)
  const startRecording = useCallback(async () => {
    try {
      // Stop all currently playing audio immediately
      stopAllAudio();
      
      // Initialize audio if not already done
      if (!audioEnabled) {
        await initializeAudio();
      }
      
      console.log('Starting recording...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus' 
        : 'audio/webm';
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Recording stopped, blob size:', audioBlob.size);
        sendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus('Recording...');
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Please allow microphone access');
    }
  }, [audioEnabled]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('Stopping recording...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('Processing...');
    }
  }, [isRecording]);

  // Send audio to backend
  const sendAudio = (audioBlob: Blob) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = reader.result?.toString().split(',')[1];
      if (base64Audio && socketRef.current) {
        socketRef.current.emit('audio_data', {
          audio: base64Audio,
          format: 'webm',
          timestamp: new Date().toISOString(),
          size: audioBlob.size
        });
        console.log('📤 Sent audio data:', audioBlob.size, 'bytes');
      }
    };
    reader.readAsDataURL(audioBlob);
  };

  // Handle spacebar press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat && !isRecording && isConnected) {
        e.preventDefault();
        // Stop all audio IMMEDIATELY when spacebar is pressed
        stopAllAudio();
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

  return (
    <div className="min-h-screen text-white flex" style={{ backgroundColor: '#0a0a0a' }}>
      {/* Main Center Section */}
      <div className="flex-1 flex flex-col items-center justify-center px-12 py-32">
        {/* Title */}
        <h1 className="text-6xl font-bold text-white mb-16 text-center">
          United Voice Agent
        </h1>
        
        {/* Subtitle */}
        <p className="text-xl text-gray-300 mb-24 text-center">
          How can I help you with your travel needs today?
        </p>
        
        {/* Audio Enable Notice */}
        {!audioEnabled && (
          <div className="mb-6 p-3 bg-yellow-900/50 border border-yellow-600 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              <span className="text-yellow-200 text-sm">
                Press spacebar to enable voice responses
              </span>
            </div>
          </div>
        )}

        {/* Pending Audio Notice */}
        {pendingAudio && (
          <div className="mb-6 p-3 bg-blue-900/50 border border-blue-600 rounded-lg">
            <button
              onClick={() => initializeAudio()}
              className="flex items-center gap-2 mx-auto text-blue-200 hover:text-blue-100"
            >
              <Play className="w-5 h-5" />
              <span className="text-sm">Click to play agent voice response</span>
            </button>
          </div>
        )}
        
        {/* Large Metallic Orb */}
        <div className="relative mb-8">
          <div 
            className={`w-70 h-70 rounded-full flex items-center justify-center transition-all duration-300 ${
              isRecording ? 'scale-110' : 'hover:scale-105'
            }`}
            style={{
              width: '280px',
              height: '280px',
              background: isRecording 
                ? 'radial-gradient(circle, #ff6b6b 0%, #ee5a52 50%, #d63031 100%)'
                : 'radial-gradient(circle, #74b9ff 0%, #6c5ce7 50%, #5a67d8 100%)',
              boxShadow: isRecording 
                ? '0 0 60px rgba(255, 107, 107, 0.6), 0 0 120px rgba(255, 107, 107, 0.3)'
                : '0 0 60px rgba(116, 185, 255, 0.4), 0 0 120px rgba(116, 185, 255, 0.2)'
            }}
          >
            {/* Inner content */}
            <div className="flex flex-col items-center justify-center">
              {isRecording ? (
                <div className="flex items-center gap-2">
                  {/* Waveform bars when recording */}
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 bg-white rounded-full animate-pulse"
                      style={{
                        height: `${20 + Math.sin(Date.now() / 200 + i) * 15}px`,
                        animationDelay: `${i * 0.1}s`,
                        animationDuration: '0.6s'
                      }}
                    />
                  ))}
                </div>
              ) : (
                <Mic className="w-16 h-16 text-white opacity-80" />
              )}
            </div>
          </div>
        </div>
        
        {/* Start Call Button */}
        <button
          className="w-56 h-16 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 
                     text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 
                     shadow-lg hover:shadow-xl mt-20 flex items-center justify-center gap-3"
          disabled={!isConnected}
          onClick={() => {
            if (!audioEnabled) initializeAudio();
          }}
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
          </svg>
          Start a call
        </button>
        
        {/* Hold SPACE instruction */}
        <p className="text-gray-400 text-sm mt-6">
          {isConnected 
            ? isRecording 
              ? 'Release to send message...' 
              : 'Hold SPACE to record'
            : 'Connecting to server...'}
        </p>

        {/* Connection Status and Volume Controls (minimal) */}
        <div className="fixed bottom-6 left-6 flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
            <span className={`text-xs px-2 py-1 rounded ${
              isConnected 
                ? 'text-green-400' 
                : 'text-red-400'
            }`}>
              {status}
            </span>
          </div>
          
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1 rounded bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Conversation Panel on Right */}
      <div 
        className="w-96 min-h-screen p-6 border-l border-gray-800/50"
        style={{ 
          backgroundColor: 'rgba(10, 10, 10, 0.8)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <h2 className="text-lg font-semibold mb-6 text-gray-300">Conversation</h2>
        <div className="h-full overflow-y-auto space-y-4 pr-2">
          {messages.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-sm">Start a conversation...</p>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs ${msg.sender === 'agent' ? 'space-y-2' : ''}`}>
                  <div className={`px-4 py-3 rounded-2xl ${
                    msg.sender === 'user' 
                      ? 'bg-blue-600 text-white ml-8' 
                      : 'bg-gray-800/80 text-gray-100 mr-8'
                  }`}>
                    <p className="text-sm">{msg.text}</p>
                  </div>
                  {/* Play button for agent messages with audio */}
                  {msg.sender === 'agent' && msg.audio && (
                    <button
                      onClick={() => playMessageAudio(msg)}
                      className="flex items-center gap-1 px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-full text-xs text-gray-300 transition-colors"
                    >
                      <Play className="w-3 h-3" />
                      Play voice
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}