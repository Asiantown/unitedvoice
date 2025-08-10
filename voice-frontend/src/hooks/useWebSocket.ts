import { useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useVoiceStore } from '@/store/voiceStore';

/**
 * Configuration options for the WebSocket hook
 */
interface UseWebSocketConfig {
  /** WebSocket server URL */
  url?: string;
  /** Whether to auto-connect on mount */
  autoConnect?: boolean;
  /** Number of reconnection attempts */
  reconnectionAttempts?: number;
  /** Delay between reconnection attempts in milliseconds */
  reconnectionDelay?: number;
}

/**
 * Data structure for audio transmission
 */
interface AudioData {
  audio: string;
  format: string;
  timestamp: number;
}

/**
 * Data structure for text messages
 */
interface TextMessage {
  text: string;
  timestamp: number;
}

/**
 * All possible WebSocket event handlers
 * These match the server-side events for type safety
 */
interface WebSocketEvents {
  // Connection events
  connect: () => void;
  disconnect: (reason: string) => void;
  connect_error: (error: Error) => void;
  reconnect: (attemptNumber: number) => void;
  reconnect_attempt: (attemptNumber: number) => void;
  reconnect_error: (error: Error) => void;
  reconnect_failed: () => void;

  // Voice agent events
  transcription_result: (data: { text: string; is_final: boolean; confidence?: number }) => void;
  agent_response: (data: { text: string; audio_url?: string; metadata?: Record<string, unknown> }) => void;
  tts_audio: (data: { audio_data: string; format: string; metadata?: Record<string, unknown> }) => void;
  agent_state_change: (data: { state: string; metadata?: Record<string, unknown> }) => void;
  
  // Audio events
  audio_received: (data: { success: boolean; message?: string }) => void;
  audio_processing: (data: { status: string; progress?: number }) => void;
  
  // System events
  system_status: (data: { status: string; message?: string }) => void;
  error: (data: { error: string; code?: string; details?: Record<string, unknown> }) => void;
}

/**
 * Custom hook for managing WebSocket connections to the voice agent server
 * Provides connection management, event handling, and automatic reconnection
 * 
 * @param config - Configuration options for the WebSocket connection
 * @returns WebSocket methods and connection state
 */
export const useWebSocket = (config: UseWebSocketConfig = {}) => {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000',
    autoConnect = true,
    reconnectionAttempts = 5,
    reconnectionDelay = 1000,
  } = config;

  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    setConnectionState,
    setError,
    addTranscription,
    addAgentResponse,
    addAudioToQueue,
    setAgentState,
    connectionState,
  } = useVoiceStore();

  /**
   * Initializes and connects to the WebSocket server
   * @returns The connected socket instance
   */
  const connect = useCallback((): Socket | null => {
    if (socketRef.current?.connected) {
      return socketRef.current;
    }

    setConnectionState('connecting');

    const socket = io(url, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts,
      reconnectionDelay,
      reconnectionDelayMax: 5000,
    });

    // Connection event handlers
    socket.on('connect', () => {
      setConnectionState('connected');
      setError(null);
      
      if (process.env.NODE_ENV === 'development') {
        // WebSocket connected successfully
      }
    });

    socket.on('disconnect', (reason: string) => {
      setConnectionState('disconnected');
      
      if (process.env.NODE_ENV === 'development') {
        // WebSocket disconnected
      }
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect - attempt to reconnect
        socket.connect();
      }
    });

    socket.on('connect_error', (error: Error) => {
      setConnectionState('error');
      setError(`Connection failed: ${error.message}`);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('WebSocket connection error:', error);
      }
    });

    socket.on('reconnect', (attemptNumber: number) => {
      setConnectionState('connected');
      setError(null);
      
      if (process.env.NODE_ENV === 'development') {
        // WebSocket reconnected successfully
      }
    });

    socket.on('reconnect_attempt', (attemptNumber: number) => {
      setConnectionState('reconnecting');
      
      if (process.env.NODE_ENV === 'development') {
        // Attempting WebSocket reconnection
      }
    });

    socket.on('reconnect_error', (error: Error) => {
      setError(`Reconnection failed: ${error.message}`);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('WebSocket reconnection error:', error);
      }
    });

    socket.on('reconnect_failed', () => {
      setConnectionState('error');
      setError('Connection failed - unable to reconnect to server');
      
      if (process.env.NODE_ENV === 'development') {
        console.error('WebSocket reconnection failed - max attempts reached');
      }
    });

    // Voice agent event handlers
    socket.on('transcription_result', (data: { text: string; is_final: boolean; confidence?: number }) => {
      if (process.env.NODE_ENV === 'development') {
        // Transcription received
      }
      
      addTranscription({
        text: data.text,
        isFinal: data.is_final,
        confidence: data.confidence,
        timestamp: Date.now(),
      });
    });

    socket.on('agent_response', (data: { text: string; audio_url?: string; metadata?: Record<string, unknown> }) => {
      if (process.env.NODE_ENV === 'development') {
        // Agent response received
      }
      
      addAgentResponse({
        text: data.text,
        audioUrl: data.audio_url,
        metadata: data.metadata,
        timestamp: Date.now(),
      });
    });

    socket.on('tts_audio', (data: { audio_data: string; format: string; metadata?: Record<string, unknown> }) => {
      if (process.env.NODE_ENV === 'development') {
        // TTS audio received
      }
      
      addAudioToQueue({
        audioData: data.audio_data,
        format: data.format,
        metadata: data.metadata,
        timestamp: Date.now(),
      });
    });

    socket.on('agent_state_change', (data: { state: string; metadata?: Record<string, unknown> }) => {
      if (process.env.NODE_ENV === 'development') {
        // Agent state updated
      }
      
      setAgentState(data.state, data.metadata);
    });

    // Audio event handlers
    socket.on('audio_received', (data: { success: boolean; message?: string }) => {
      if (process.env.NODE_ENV === 'development') {
        // Audio received by server
      }
      
      if (!data.success && data.message) {
        setError(`Audio processing failed: ${data.message}`);
      }
    });

    socket.on('audio_processing', (data: { status: string; progress?: number }) => {
      if (process.env.NODE_ENV === 'development') {
        // Audio processing status updated
      }
      // Could be used to show processing progress in UI
    });

    // System event handlers
    socket.on('system_status', (data: { status: string; message?: string }) => {
      if (process.env.NODE_ENV === 'development') {
        // System status updated
      }
      
      if (data.status === 'error') {
        setError(data.message || 'System error occurred');
      }
    });

    socket.on('error', (data: { error: string; code?: string; details?: Record<string, unknown> }) => {
      setError(`Server error: ${data.error}`);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('WebSocket error event:', data);
      }
    });

    socketRef.current = socket;
    return socket;
  }, [url, reconnectionAttempts, reconnectionDelay, setConnectionState, setError, addTranscription, addAgentResponse, addAudioToQueue, setAgentState]);

  /**
   * Disconnects from the WebSocket server and cleans up resources
   */
  const disconnect = useCallback((): void => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      if (process.env.NODE_ENV === 'development') {
        // Disconnecting WebSocket
      }
      
      socketRef.current.disconnect();
      socketRef.current = null;
      setConnectionState('disconnected');
    }
  }, [setConnectionState]);

  /**
   * Sends audio data to the server
   * @param audioData - Base64 encoded audio data
   * @param format - Audio format (default: 'webm')
   * @returns Success status
   */
  const sendAudioData = useCallback((audioData: string, format: string = 'webm'): boolean => {
    if (!socketRef.current?.connected) {
      setError('Not connected to server');
      return false;
    }

    try {
      const audioPayload: AudioData = {
        audio: audioData,
        format,
        timestamp: Date.now(),
      };
      
      socketRef.current.emit('audio_data', audioPayload);
      
      if (process.env.NODE_ENV === 'development') {
        // Audio data sent successfully
      }
      
      return true;
    } catch (error) {
      const errorMessage = 'Failed to send audio data';
      setError(errorMessage);
      
      if (process.env.NODE_ENV === 'development') {
        console.error(errorMessage, error);
      }
      
      return false;
    }
  }, [setError]);

  /**
   * Sends a text message to the server
   * @param text - The message text to send
   * @returns Success status
   */
  const sendTextMessage = useCallback((text: string): boolean => {
    if (!socketRef.current?.connected) {
      setError('Not connected to server');
      return false;
    }

    try {
      const textPayload: TextMessage = {
        text,
        timestamp: Date.now(),
      };
      
      socketRef.current.emit('text_message', textPayload);
      
      if (process.env.NODE_ENV === 'development') {
        // Text message sent successfully
      }
      
      return true;
    } catch (error) {
      const errorMessage = 'Failed to send text message';
      setError(errorMessage);
      
      if (process.env.NODE_ENV === 'development') {
        console.error(errorMessage, error);
      }
      
      return false;
    }
  }, [setError]);

  /**
   * Signals the server to start recording
   * @returns Success status
   */
  const startRecording = useCallback((): boolean => {
    if (!socketRef.current?.connected) {
      return false;
    }

    try {
      socketRef.current.emit('start_recording', {
        timestamp: Date.now(),
      });
      
      if (process.env.NODE_ENV === 'development') {
        // Recording started
      }
      
      return true;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to send start recording signal:', error);
      }
      return false;
    }
  }, []);

  /**
   * Signals the server to stop recording
   * @returns Success status
   */
  const stopRecording = useCallback((): boolean => {
    if (!socketRef.current?.connected) {
      return false;
    }

    try {
      socketRef.current.emit('stop_recording', {
        timestamp: Date.now(),
      });
      
      if (process.env.NODE_ENV === 'development') {
        // Recording stopped
      }
      
      return true;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to send stop recording signal:', error);
      }
      return false;
    }
  }, []);

  /**
   * Generic emit function for custom events
   * @param event - Event name
   * @param data - Event data
   * @returns Success status
   */
  const emit = useCallback((event: string, data: Record<string, unknown>): boolean => {
    if (!socketRef.current?.connected) {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Cannot emit ${event} - socket not connected`);
      }
      return false;
    }

    try {
      socketRef.current.emit(event, data);
      
      if (process.env.NODE_ENV === 'development') {
        // Event emitted successfully
      }
      
      return true;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error(`Failed to emit ${event}:`, error);
      }
      return false;
    }
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, autoConnect]);

  return {
    socket: socketRef.current,
    connect,
    disconnect,
    sendAudioData,
    sendTextMessage,
    startRecording,
    stopRecording,
    emit,
    isConnected: connectionState === 'connected',
    connectionState,
  };
};