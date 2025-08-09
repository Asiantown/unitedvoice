'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Mic, Volume2, VolumeX, Wifi, WifiOff, Play, AlertCircle } from 'lucide-react';
import { io, Socket } from 'socket.io-client';

/**
 * Represents a message in the conversation
 */
interface Message {
  /** The text content of the message */
  text: string;
  /** Who sent the message */
  sender: 'user' | 'agent';
  /** Unique identifier for the message */
  id: string;
  /** Base64 encoded audio data */
  audio?: string;
  /** Audio format (mp3, webm, etc.) */
  audioFormat?: string;
}

/**
 * Configuration for audio recording
 */
interface AudioConfig {
  sampleRate: number;
  channelCount: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
}

/**
 * Pending audio data structure
 */
interface PendingAudio {
  audio: string;
  format: string;
}

/**
 * Main voice interface page for the United Voice Agent
 * Handles voice recording, WebSocket communication, and audio playback
 */
export default function VoicePage(): React.JSX.Element {
  // Component state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<string>('Connecting...');
  const [volume] = useState<number>(0.8);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [audioEnabled, setAudioEnabled] = useState<boolean>(false);
  const [pendingAudio, setPendingAudio] = useState<PendingAudio | null>(null);
  
  const socketRef = useRef<Socket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const isMutedRef = useRef(false);
  const audioEnabledRef = useRef(false);
  const audioElementsRef = useRef<Set<HTMLAudioElement>>(new Set());

  /**
   * Scrolls the conversation panel to the bottom
   */
  const scrollToBottom = useCallback((): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /**
   * Stops all currently playing audio elements and clears the tracking set
   */
  const stopAllAudio = useCallback((): void => {
    audioElementsRef.current.forEach((audio: HTMLAudioElement) => {
      try {
        audio.pause();
        audio.currentTime = 0;
        // Remove event listeners to prevent cleanup issues
        audio.onended = null;
        audio.onerror = null;
        audio.onpause = null;
      } catch (error) {
        // Silently handle errors to avoid console spam in production
        if (process.env.NODE_ENV === 'development') {
          console.warn('Error stopping audio element:', error);
        }
      }
    });
    audioElementsRef.current.clear();
  }, []);

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

  /**
   * Initializes the audio context on user interaction
   * Required for modern browsers' autoplay policies
   */
  const initializeAudio = useCallback(async (): Promise<void> => {
    try {
      if (!audioContextRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContextClass();
        
        if (audioContextRef.current.state === 'suspended') {
          await audioContextRef.current.resume();
        }
      }
      
      setAudioEnabled(true);
      
      // Play any pending audio
      if (pendingAudio) {
        await playAudioSafely(pendingAudio.audio, pendingAudio.format);
        setPendingAudio(null);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to initialize audio:', error);
      }
      setStatus('Audio initialization failed');
    }
  }, [pendingAudio]);

  // Audio recording configuration
  const audioConfig = useMemo<AudioConfig>(() => ({
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
  }), []);

  // WebSocket connection URL
  const wsUrl = useMemo(() => 
    process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', []);

  // Connect to WebSocket
  useEffect(() => {
    socketRef.current = io(wsUrl, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      setStatus('Connected');
    });

    socketRef.current.on('disconnect', () => {
      setIsConnected(false);
      setStatus('Disconnected');
    });

    socketRef.current.on('connected', () => {
      // Server greeting received - connection established
    });

    socketRef.current.on('agent_response', (data: {
      text: string;
      audio?: string;
      audio_format?: string;
    }) => {
      const messageId = `${Date.now()}-${Math.random().toString(36).substring(2, 11)}-agent`;
      
      const newMessage: Message = {
        text: data.text,
        sender: 'agent',
        id: messageId,
        audio: data.audio,
        audioFormat: data.audio_format || 'mp3'
      };
      
      // Prevent duplicate messages within a 2-second window
      setMessages(prev => {
        const recentDuplicate = prev.find(msg => 
          msg.sender === 'agent' && 
          msg.text === data.text && 
          Math.abs(parseInt(msg.id.split('-')[0]) - Date.now()) < 2000
        );
        
        return recentDuplicate ? prev : [...prev, newMessage];
      });
      
      // Handle audio playback
      if (data.audio && !isMutedRef.current) {
        if (audioEnabledRef.current) {
          playAudioSafely(data.audio, data.audio_format || 'mp3');
        } else {
          setPendingAudio({ audio: data.audio, format: data.audio_format || 'mp3' });
        }
      }
    });

    socketRef.current.on('transcription', (data: { text: string }) => {
      const messageId = `${Date.now()}-${Math.random().toString(36).substring(2, 11)}-user`;
      
      const newMessage: Message = { 
        text: data.text, 
        sender: 'user',
        id: messageId
      };
      
      // Prevent duplicate transcriptions within a 1-second window
      setMessages(prev => {
        const recentDuplicate = prev.find(msg => 
          msg.sender === 'user' && 
          msg.text === data.text && 
          Math.abs(parseInt(msg.id.split('-')[0]) - Date.now()) < 1000
        );
        
        return recentDuplicate ? prev : [...prev, newMessage];
      });
    });

    socketRef.current.on('status_update', (data: { message: string }) => {
      setStatus(data.message);
    });

    socketRef.current.on('error', (error: { message?: string }) => {
      const errorMessage = error.message || 'Connection failed';
      setStatus(`Error: ${errorMessage}`);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('Socket error:', error);
      }
    });

    return () => {
      socketRef.current?.disconnect();
      stopAllAudio();
    };
  }, [wsUrl, stopAllAudio]);

  /**
   * Safely plays audio from base64 data with proper cleanup
   * @param base64Audio - Base64 encoded audio data
   * @param format - Audio format (mp3, webm, etc.)
   */
  const playAudioSafely = useCallback(async (base64Audio: string, format: string = 'mp3'): Promise<void> => {
    try {
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
      
      // Cleanup handlers
      const cleanup = () => {
        URL.revokeObjectURL(audioUrl);
        audioElementsRef.current.delete(audio);
      };
      
      audio.onended = cleanup;
      audio.onerror = cleanup;
      audio.onpause = () => {
        // Only clean up if the audio was stopped at beginning (interrupted)
        if (audio.currentTime === 0) {
          cleanup();
        }
      };
      
      // Attempt to play the audio
      try {
        await audio.play();
      } catch (playError) {
        // Handle autoplay policy restrictions
        audioElementsRef.current.delete(audio);
        URL.revokeObjectURL(audioUrl);
        setPendingAudio({ audio: base64Audio, format });
        
        if (process.env.NODE_ENV === 'development') {
          console.warn('Audio autoplay blocked, queuing for user interaction:', playError);
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Audio playback error:', error);
      }
    }
  }, [volume]);

  /**
   * Plays audio for a specific message
   * @param msg - The message containing audio data
   */
  const playMessageAudio = useCallback(async (msg: Message): Promise<void> => {
    stopAllAudio();
    
    if (msg.audio && msg.audioFormat) {
      if (!audioEnabled) {
        await initializeAudio();
      }
      await playAudioSafely(msg.audio, msg.audioFormat);
    }
  }, [audioEnabled, initializeAudio, playAudioSafely, stopAllAudio]);

  /**
   * Starts audio recording with proper permission handling
   */
  const startRecording = useCallback(async (): Promise<void> => {
    try {
      stopAllAudio();
      
      if (!audioEnabled) {
        await initializeAudio();
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: audioConfig });

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
        sendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus('Recording...');
    } catch (error) {
      setStatus('Microphone access denied');
      
      if (process.env.NODE_ENV === 'development') {
        console.error('Error starting recording:', error);
      }
    }
  }, [audioEnabled, audioConfig, initializeAudio, stopAllAudio]);

  /**
   * Stops the current recording session
   */
  const stopRecording = useCallback((): void => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('Processing...');
    }
  }, [isRecording]);

  /**
   * Sends audio data to the backend via WebSocket
   * @param audioBlob - The recorded audio blob
   */
  const sendAudio = useCallback((audioBlob: Blob): void => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result?.toString();
      const base64Audio = result?.split(',')[1];
      
      if (base64Audio && socketRef.current?.connected) {
        socketRef.current.emit('audio_data', {
          audio: base64Audio,
          format: 'webm',
          timestamp: new Date().toISOString(),
          size: audioBlob.size
        });
      } else {
        setStatus('Connection lost - please try again');
      }
    };
    
    reader.onerror = () => {
      setStatus('Failed to process audio');
    };
    
    reader.readAsDataURL(audioBlob);
  }, []);

  /**
   * Handle keyboard shortcuts for voice recording
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      // Prevent recording if user is typing in an input field
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      if (e.code === 'Space' && !e.repeat && !isRecording && isConnected) {
        e.preventDefault();
        stopAllAudio();
        startRecording();
      }
    };

    const handleKeyUp = (e: KeyboardEvent): void => {
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
  }, [isRecording, isConnected, startRecording, stopRecording, stopAllAudio]);

  return (
    <div className="min-h-screen text-white flex bg-[#0a0a0a]">
      {/* Main Center Section */}
      <div className="flex-1 flex flex-col items-center justify-center px-12 py-32">
        {/* Title */}
        <h1 className="text-6xl font-bold text-white mb-16 text-center" role="banner">
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
          <button
            className={`w-70 h-70 rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-300 ${
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
            disabled={!isConnected}
            onClick={() => {
              if (!audioEnabled) initializeAudio();
            }}
            aria-label={isRecording ? 'Stop recording' : 'Start voice interaction'}
            role="button"
            tabIndex={0}
          >
            {/* Inner content */}
            <div className="flex flex-col items-center justify-center">
              {isRecording ? (
                <div className="flex items-center gap-2" aria-label="Recording in progress">
                  {/* Waveform bars when recording */}
                  {Array.from({ length: 5 }, (_, i) => (
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
                <Mic className="w-16 h-16 text-white opacity-80" aria-hidden="true" />
              )}
            </div>
          </button>
        </div>
        
        {/* Start Call Button */}
        <button
          className="w-56 h-16 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 
                     text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 
                     shadow-lg hover:shadow-xl mt-20 flex items-center justify-center gap-3 
                     focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          disabled={!isConnected}
          onClick={() => {
            if (!audioEnabled) initializeAudio();
          }}
          aria-label="Start voice call with United Voice Agent"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
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
        <div className="fixed bottom-6 left-6 flex items-center gap-4" role="status" aria-live="polite">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" aria-hidden="true" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" aria-hidden="true" />
            )}
            <span 
              className={`text-xs px-2 py-1 rounded ${
                isConnected 
                  ? 'text-green-400' 
                  : 'text-red-400'
              }`}
              aria-label={`Connection status: ${status}`}
            >
              {status}
            </span>
          </div>
          
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1 rounded bg-gray-800/50 hover:bg-gray-700/50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300"
            aria-label={isMuted ? 'Unmute audio' : 'Mute audio'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" aria-hidden="true" /> : <Volume2 className="w-4 h-4" aria-hidden="true" />}
          </button>
        </div>
      </div>

      {/* Conversation Panel on Right */}
      <aside 
        className="w-96 min-h-screen p-6 border-l border-gray-800/50 bg-[rgba(10,10,10,0.8)] backdrop-blur-[10px]"
        role="complementary"
        aria-label="Conversation history"
      >
        <h2 className="text-lg font-semibold mb-6 text-gray-300">Conversation</h2>
        <div 
          className="h-full overflow-y-auto space-y-4 pr-2"
          role="log"
          aria-live="polite"
          aria-label="Conversation messages"
        >
          {messages.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-sm">Start a conversation...</p>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs ${msg.sender === 'agent' ? 'space-y-2' : ''}`}>
                  <div 
                    className={`px-4 py-3 rounded-2xl ${
                      msg.sender === 'user' 
                        ? 'bg-blue-600 text-white ml-8' 
                        : 'bg-gray-800/80 text-gray-100 mr-8'
                    }`}
                    role={msg.sender === 'user' ? 'comment' : 'article'}
                    aria-label={`Message from ${msg.sender === 'user' ? 'you' : 'agent'}`}
                  >
                    <p className="text-sm">{msg.text}</p>
                  </div>
                  {/* Play button for agent messages with audio */}
                  {msg.sender === 'agent' && msg.audio && (
                    <button
                      onClick={() => playMessageAudio(msg)}
                      className="flex items-center gap-1 px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-full text-xs text-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300"
                      aria-label="Play audio response"
                    >
                      <Play className="w-3 h-3" aria-hidden="true" />
                      Play voice
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
      </aside>
    </div>
  );
}