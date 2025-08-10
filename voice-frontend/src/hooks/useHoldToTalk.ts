import { useCallback, useEffect, useRef, useState } from 'react';
import { useVoiceStore } from '@/store/voiceStore';
import { useWebSocket } from './useWebSocket';

interface UseHoldToTalkConfig {
  spacebarEnabled?: boolean;
  mouseEnabled?: boolean;
  audioConstraints?: MediaStreamConstraints['audio'];
  recordingTimeLimit?: number; // in milliseconds
  silenceTimeout?: number; // auto-stop after silence (in milliseconds)
  minRecordingTime?: number; // minimum recording time (in milliseconds)
}

interface AudioSettings {
  sampleRate: number;
  channelCount: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
  autoGainControl: boolean;
}

const DEFAULT_AUDIO_SETTINGS: AudioSettings = {
  sampleRate: 16000, // 16kHz for speech recognition
  channelCount: 1, // Mono
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
};

export const useHoldToTalk = (config: UseHoldToTalkConfig = {}) => {
  const {
    spacebarEnabled = true,
    mouseEnabled = true,
    audioConstraints,
    recordingTimeLimit = 60000, // 60 seconds
    silenceTimeout = 5000, // 5 seconds
    minRecordingTime = 500, // 0.5 seconds
  } = config;

  // Store and WebSocket hooks
  const {
    recordingState,
    isHoldingToTalk,
    setRecordingState,
    setHoldingToTalk,
    setRecordingStartTime,
    updateRecordingDuration,
    setCurrentAudioLevel,
    setWaveformData,
    setError,
  } = useVoiceStore();

  const { sendAudioData, startRecording, stopRecording, isConnected } = useWebSocket();

  // Refs for media recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  
  // Timers and intervals
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const visualizationFrameRef = useRef<number | null>(null);

  // State for key/mouse tracking
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [isMousePressed, setIsMousePressed] = useState(false);
  const [hasStartedRecording, setHasStartedRecording] = useState(false);

  // Audio level monitoring for silence detection  
  const [averageAudioLevel, setAverageAudioLevel] = useState(0);

  // Initialize audio context and analyzer
  const initializeAudio = useCallback(async () => {
    try {
      const constraints: MediaStreamConstraints = {
        audio: audioConstraints || {
          ...DEFAULT_AUDIO_SETTINGS,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;

      // Set up audio context for visualization and level monitoring
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      analyserRef.current.fftSize = 2048;
      analyserRef.current.smoothingTimeConstant = 0.3;
      source.connect(analyserRef.current);

      // Set up MediaRecorder
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
        'audio/wav',
      ];

      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      if (!selectedMimeType) {
        throw new Error('No supported audio format found');
      }


      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: selectedMimeType,
        audioBitsPerSecond: 128000, // 128kbps
      });

      // Set up MediaRecorder event handlers
      mediaRecorderRef.current.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: selectedMimeType });
          audioChunksRef.current = []; // Clear chunks

          // Convert to base64 and send
          try {
            setRecordingState('uploading');
            const base64Audio = await blobToBase64(audioBlob);
            const success = sendAudioData(base64Audio, selectedMimeType);
            
            if (success) {
              setRecordingState('processing');
            } else {
              setRecordingState('idle');
              setError('Failed to send audio to server');
            }
          } catch (error) {
            setRecordingState('idle');
            setError('Failed to process audio');
          }
        } else {
          setRecordingState('idle');
        }
      };

      mediaRecorderRef.current.onerror = () => {
        setRecordingState('idle');
        setError('Recording failed');
      };

      return true;
    } catch (error) {
      setError(`Microphone access denied: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return false;
    }
  }, [audioConstraints, sendAudioData, setRecordingState, setError]);

  // Convert blob to base64
  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        // Remove the data URL prefix (e.g., "data:audio/webm;base64,")
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  // Audio visualization and level monitoring
  const updateAudioVisualization = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const waveformArray = new Float32Array(bufferLength);
    
    analyserRef.current.getByteFrequencyData(dataArray);
    analyserRef.current.getFloatTimeDomainData(waveformArray);

    // Calculate average audio level (0-1)
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength / 255;
    
    setCurrentAudioLevel(average);
    setAverageAudioLevel(average);
    setWaveformData(waveformArray);

    if (recordingState === 'recording') {
      visualizationFrameRef.current = requestAnimationFrame(updateAudioVisualization);
    }
  }, [recordingState, setCurrentAudioLevel, setWaveformData]);

  // Start recording
  const startRecordingInternal = useCallback(async () => {
    if (!isConnected) {
      setError('Not connected to server');
      return;
    }

    if (recordingState === 'recording') {
      return; // Already recording
    }

    // Initialize audio if not already done
    if (!mediaRecorderRef.current || !mediaStreamRef.current) {
      const initialized = await initializeAudio();
      if (!initialized) {
        return;
      }
    }

    try {
      // Clear any existing chunks
      audioChunksRef.current = [];
      
      // Start recording
      mediaRecorderRef.current?.start(100); // Record in 100ms chunks
      
      setRecordingState('recording');
      setRecordingStartTime(Date.now());
      setHasStartedRecording(true);
      
      // Notify server
      startRecording();

      // Start duration timer
      durationIntervalRef.current = setInterval(() => {
        updateRecordingDuration(Date.now() - (Date.now() - (Date.now() % 1000)));
      }, 100);

      // Start audio visualization
      updateAudioVisualization();

      // Set up recording time limit
      if (recordingTimeLimit > 0) {
        recordingTimerRef.current = setTimeout(() => {
          stopRecordingInternal();
        }, recordingTimeLimit);
      }

    } catch (error) {
      setRecordingState('idle');
      setError('Failed to start recording');
    }
  }, [
    isConnected,
    recordingState,
    initializeAudio,
    setRecordingState,
    setRecordingStartTime,
    setError,
    startRecording,
    updateRecordingDuration,
    updateAudioVisualization,
    recordingTimeLimit,
  ]);

  // Stop recording
  const stopRecordingInternal = useCallback(() => {
    if (recordingState !== 'recording') {
      return;
    }

    // Check minimum recording time
    const recordingDuration = Date.now() - (Date.now() % 1000);
    if (hasStartedRecording && recordingDuration < minRecordingTime) {
      setRecordingState('idle');
      setHasStartedRecording(false);
      return;
    }

    try {
      // Stop MediaRecorder
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }

      // Clear timers
      if (recordingTimerRef.current) {
        clearTimeout(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      // Stop animation frame
      if (visualizationFrameRef.current) {
        cancelAnimationFrame(visualizationFrameRef.current);
        visualizationFrameRef.current = null;
      }

      // Notify server
      stopRecording();

      setHasStartedRecording(false);
      setCurrentAudioLevel(0);
      setWaveformData(null);

    } catch (error) {
      setRecordingState('idle');
      setError('Failed to stop recording');
    }
  }, [
    recordingState,
    hasStartedRecording,
    minRecordingTime,
    setRecordingState,
    stopRecording,
    setCurrentAudioLevel,
    setWaveformData,
    setError,
  ]);

  // Handle hold state changes
  useEffect(() => {
    const shouldBeHolding = (spacebarEnabled && isSpacePressed) || 
                           (mouseEnabled && isMousePressed);

    setHoldingToTalk(shouldBeHolding);

    if (shouldBeHolding && recordingState === 'idle') {
      startRecordingInternal();
    } else if (!shouldBeHolding && recordingState === 'recording') {
      stopRecordingInternal();
    }
  }, [
    isSpacePressed,
    isMousePressed,
    spacebarEnabled,
    mouseEnabled,
    recordingState,
    setHoldingToTalk,
    startRecordingInternal,
    stopRecordingInternal,
  ]);

  // Spacebar handlers
  useEffect(() => {
    if (!spacebarEnabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'Space' && !event.repeat) {
        event.preventDefault();
        setIsSpacePressed(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === 'Space') {
        event.preventDefault();
        setIsSpacePressed(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, [spacebarEnabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clean up timers
      if (recordingTimerRef.current) clearTimeout(recordingTimerRef.current);
      if (durationIntervalRef.current) clearInterval(durationIntervalRef.current);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (visualizationFrameRef.current) cancelAnimationFrame(visualizationFrameRef.current);

      // Clean up media
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Mouse/touch handlers (to be used on button component)
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (!mouseEnabled) return;
    event.preventDefault();
    setIsMousePressed(true);
  }, [mouseEnabled]);

  const handleMouseUp = useCallback((event: React.MouseEvent) => {
    if (!mouseEnabled) return;
    event.preventDefault();
    setIsMousePressed(false);
  }, [mouseEnabled]);


  // Manual start/stop methods
  const startManualRecording = useCallback(() => {
    if (!isConnected) {
      setError('Not connected to server');
      return;
    }
    startRecordingInternal();
  }, [isConnected, startRecordingInternal, setError]);

  const stopManualRecording = useCallback(() => {
    stopRecordingInternal();
  }, [stopRecordingInternal]);

  return {
    // State
    isHoldingToTalk,
    recordingState,
    hasAudioPermission: !!mediaStreamRef.current,
    
    // Event handlers for components
    handleMouseDown,
    handleMouseUp,
    
    // Manual control
    startRecording: startManualRecording,
    stopRecording: stopManualRecording,
    
    // Audio info
    audioLevel: averageAudioLevel,
    isConnected,
  };
};