import { useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useVoiceStore } from '@/store/voiceStore';

interface UseWebSocketConfig {
  url?: string;
  autoConnect?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
}

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

export const useWebSocket = (config: UseWebSocketConfig = {}) => {
  const {
    url = 'http://localhost:8000',
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

  // Initialize socket connection
  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return socketRef.current;
    }

    console.log('Connecting to WebSocket server:', url);
    setConnectionState('connecting');

    const socket = io(url, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts,
      reconnectionDelay,
      reconnectionDelayMax: 5000,
      // maxReconnectionAttempts: reconnectionAttempts, // Not a valid socket.io option
    });

    // Connection event handlers
    socket.on('connect', () => {
      console.log('WebSocket connected:', socket.id);
      setConnectionState('connected');
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnectionState('disconnected');
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect - attempt to reconnect
        socket.connect();
      }
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setConnectionState('error');
      setError(`Connection failed: ${error.message}`);
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log(`WebSocket reconnected after ${attemptNumber} attempts`);
      setConnectionState('connected');
      setError(null);
    });

    socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`WebSocket reconnection attempt ${attemptNumber}`);
      setConnectionState('reconnecting');
    });

    socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error);
      setError(`Reconnection failed: ${error.message}`);
    });

    socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed - max attempts reached');
      setConnectionState('error');
      setError('Connection failed - unable to reconnect to server');
    });

    // Voice agent event handlers
    socket.on('transcription_result', (data) => {
      console.log('Transcription result:', data);
      addTranscription({
        text: data.text,
        isFinal: data.is_final,
        confidence: data.confidence,
        timestamp: Date.now(),
      });
    });

    socket.on('agent_response', (data) => {
      console.log('Agent response:', data);
      addAgentResponse({
        text: data.text,
        audioUrl: data.audio_url,
        metadata: data.metadata,
        timestamp: Date.now(),
      });
    });

    socket.on('tts_audio', (data) => {
      console.log('TTS audio received:', data.format);
      addAudioToQueue({
        audioData: data.audio_data,
        format: data.format,
        metadata: data.metadata,
        timestamp: Date.now(),
      });
    });

    socket.on('agent_state_change', (data) => {
      console.log('Agent state change:', data.state);
      setAgentState(data.state, data.metadata);
    });

    // Audio event handlers
    socket.on('audio_received', (data) => {
      console.log('Audio received confirmation:', data);
      if (!data.success) {
        setError(`Audio processing failed: ${data.message}`);
      }
    });

    socket.on('audio_processing', (data) => {
      console.log('Audio processing status:', data);
      // Could be used to show processing progress in UI
    });

    // System event handlers
    socket.on('system_status', (data) => {
      console.log('System status:', data);
      if (data.status === 'error') {
        setError(data.message || 'System error occurred');
      }
    });

    socket.on('error', (data) => {
      console.error('WebSocket error event:', data);
      setError(`Server error: ${data.error}`);
    });

    socketRef.current = socket;
    return socket;
  }, [url, reconnectionAttempts, reconnectionDelay, setConnectionState, setError, addTranscription, addAgentResponse, addAudioToQueue, setAgentState]);

  // Disconnect socket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      console.log('Disconnecting WebSocket');
      socketRef.current.disconnect();
      socketRef.current = null;
      setConnectionState('disconnected');
    }
  }, [setConnectionState]);

  // Send audio data
  const sendAudioData = useCallback((audioData: string, format: string = 'webm') => {
    if (!socketRef.current?.connected) {
      console.warn('Cannot send audio data - socket not connected');
      setError('Not connected to server');
      return false;
    }

    try {
      socketRef.current.emit('audio_data', {
        audio: audioData,
        format,
        timestamp: Date.now(),
      });
      console.log('Audio data sent to server');
      return true;
    } catch (error) {
      console.error('Failed to send audio data:', error);
      setError('Failed to send audio data');
      return false;
    }
  }, [setError]);

  // Send text message
  const sendTextMessage = useCallback((text: string) => {
    if (!socketRef.current?.connected) {
      console.warn('Cannot send text message - socket not connected');
      setError('Not connected to server');
      return false;
    }

    try {
      socketRef.current.emit('text_message', {
        text,
        timestamp: Date.now(),
      });
      console.log('Text message sent to server:', text);
      return true;
    } catch (error) {
      console.error('Failed to send text message:', error);
      setError('Failed to send text message');
      return false;
    }
  }, [setError]);

  // Send start recording signal
  const startRecording = useCallback(() => {
    if (!socketRef.current?.connected) {
      console.warn('Cannot start recording - socket not connected');
      return false;
    }

    try {
      socketRef.current.emit('start_recording', {
        timestamp: Date.now(),
      });
      console.log('Start recording signal sent');
      return true;
    } catch (error) {
      console.error('Failed to send start recording signal:', error);
      return false;
    }
  }, []);

  // Send stop recording signal
  const stopRecording = useCallback(() => {
    if (!socketRef.current?.connected) {
      console.warn('Cannot stop recording - socket not connected');
      return false;
    }

    try {
      socketRef.current.emit('stop_recording', {
        timestamp: Date.now(),
      });
      console.log('Stop recording signal sent');
      return true;
    } catch (error) {
      console.error('Failed to send stop recording signal:', error);
      return false;
    }
  }, []);

  // Generic emit function for custom events
  const emit = useCallback((event: string, data: Record<string, unknown>) => {
    if (!socketRef.current?.connected) {
      console.warn(`Cannot emit ${event} - socket not connected`);
      return false;
    }

    try {
      socketRef.current.emit(event, data);
      console.log(`Event emitted: ${event}`, data);
      return true;
    } catch (error) {
      console.error(`Failed to emit ${event}:`, error);
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