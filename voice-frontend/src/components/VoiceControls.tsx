'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useHoldToTalk } from '@/hooks/useHoldToTalk';
import { useConnectionStatus, useRecordingStatus, useAudioVisualization } from '@/store/voiceStore';
import { Mic, MicOff, Wifi, WifiOff, Volume2, VolumeX } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface WaveformVisualizerProps {
  audioData: Float32Array | null;
  isRecording: boolean;
  audioLevel: number;
  className?: string;
}

const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({ 
  audioData, 
  isRecording, 
  audioLevel,
  className = '' 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;
      
      ctx.clearRect(0, 0, width, height);
      
      if (!isRecording) {
        // Draw idle state - subtle pulsing circle
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = 20 + Math.sin(Date.now() * 0.003) * 5;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(59, 130, 246, ${0.3 + Math.sin(Date.now() * 0.005) * 0.1})`;
        ctx.fill();
        
        animationRef.current = requestAnimationFrame(draw);
        return;
      }
      
      // Recording state - waveform or level indicator
      if (audioData && audioData.length > 0) {
        // Draw waveform
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const sliceWidth = width / audioData.length;
        let x = 0;
        
        for (let i = 0; i < audioData.length; i++) {
          const v = audioData[i] * 0.5;
          const y = (v * height / 2) + height / 2;
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
          
          x += sliceWidth;
        }
        
        ctx.stroke();
      } else {
        // Draw audio level bars
        const barCount = 20;
        const barWidth = width / barCount;
        const maxHeight = height * 0.8;
        
        ctx.fillStyle = '#3b82f6';
        
        for (let i = 0; i < barCount; i++) {
          const barHeight = (audioLevel + Math.random() * 0.1) * maxHeight;
          const x = i * barWidth;
          const y = (height - barHeight) / 2;
          
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        }
      }
      
      if (isRecording) {
        animationRef.current = requestAnimationFrame(draw);
      }
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioData, isRecording, audioLevel]);

  return (
    <canvas
      ref={canvasRef}
      width={200}
      height={60}
      className={`${className} rounded-lg bg-gray-50 dark:bg-gray-800`}
    />
  );
};

interface RecordingTimerProps {
  startTime: number | null;
  isRecording: boolean;
}

const RecordingTimer: React.FC<RecordingTimerProps> = ({ startTime, isRecording }) => {
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isRecording && startTime) {
      interval = setInterval(() => {
        setDuration(Date.now() - startTime);
      }, 100);
    } else {
      setDuration(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording, startTime]);

  const formatDuration = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!isRecording) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="flex items-center gap-2 text-sm font-mono"
    >
      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
      <span>{formatDuration(duration)}</span>
    </motion.div>
  );
};

interface ConnectionStatusProps {
  connectionState: string;
  error: string | null;
  lastConnectedAt: number | null;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  connectionState, 
  error
}) => {
  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-500';
      case 'connecting':
      case 'reconnecting':
        return 'text-yellow-500';
      case 'error':
      case 'disconnected':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected':
        return <Wifi className="w-4 h-4" />;
      case 'connecting':
      case 'reconnecting':
        return <Wifi className="w-4 h-4 animate-pulse" />;
      default:
        return <WifiOff className="w-4 h-4" />;
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'error':
        return error || 'Connection Error';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return (
    <motion.div
      className={`flex items-center gap-2 text-sm ${getStatusColor()}`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      {getStatusIcon()}
      <span>{getStatusText()}</span>
    </motion.div>
  );
};

export interface VoiceControlsProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showTimer?: boolean;
  showWaveform?: boolean;
  showConnectionStatus?: boolean;
  disabled?: boolean;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  className = '',
  size = 'md',
  showTimer = true,
  showWaveform = true,
  showConnectionStatus = true,
  disabled = false,
}) => {
  const { connectionState, error } = useConnectionStatus();
  const { recordingState, isHoldingToTalk, recordingStartTime } = useRecordingStatus();
  const { waveformData } = useAudioVisualization();
  
  const {
    handleMouseDown,
    handleMouseUp,
    handleTouchStart,
    handleTouchEnd,
    audioLevel,
    isConnected,
    hasAudioPermission,
    startRecording: startManualRecording,
    stopRecording: stopManualRecording,
  } = useHoldToTalk({
    spacebarEnabled: true,
    mouseEnabled: true,
    touchEnabled: true,
  });

  const [isMuted] = useState(false);
  const isRecording = recordingState === 'recording';
  const isProcessing = recordingState === 'processing' || recordingState === 'uploading';

  // Button size configurations
  const sizeConfigs = {
    sm: {
      button: 'w-12 h-12',
      icon: 'w-4 h-4',
      container: 'gap-2',
    },
    md: {
      button: 'w-16 h-16',
      icon: 'w-6 h-6',
      container: 'gap-4',
    },
    lg: {
      button: 'w-20 h-20',
      icon: 'w-8 h-8',
      container: 'gap-6',
    },
  };

  const config = sizeConfigs[size];

  const getButtonVariant = () => {
    if (disabled || !isConnected) return 'secondary';
    if (isRecording) return 'destructive';
    return 'default';
  };

  const getButtonIcon = () => {
    if (!isConnected || disabled) return <MicOff className={config.icon} />;
    if (isMuted) return <VolumeX className={config.icon} />;
    if (isRecording) return <Volume2 className={`${config.icon} animate-pulse`} />;
    return <Mic className={config.icon} />;
  };

  const handleClick = (event: React.MouseEvent) => {
    if (disabled || !isConnected) return;
    
    // Prevent click if this was a hold-to-talk interaction
    if (isHoldingToTalk) {
      event.preventDefault();
      return;
    }
    
    // Toggle manual recording mode (for regular clicks)
    if (isRecording) {
      stopManualRecording();
    } else {
      startManualRecording();
    }
  };

  return (
    <div className={`flex flex-col items-center ${config.container} ${className}`}>
      {/* Connection Status */}
      {showConnectionStatus && (
        <ConnectionStatus
          connectionState={connectionState}
          error={error}
          lastConnectedAt={null}
        />
      )}

      {/* Main Voice Control Area */}
      <div className="flex flex-col items-center gap-4">
        {/* Waveform Visualization */}
        {showWaveform && (
          <AnimatePresence>
            {isRecording && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.2 }}
              >
                <WaveformVisualizer
                  audioData={waveformData}
                  isRecording={isRecording}
                  audioLevel={audioLevel}
                  className="mb-2"
                />
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {/* Main Talk Button */}
        <motion.div
          whileHover={!disabled && isConnected ? { scale: 1.05 } : {}}
          whileTap={!disabled && isConnected ? { scale: 0.95 } : {}}
          className="relative"
        >
          <Button
            variant={getButtonVariant()}
            size="icon"
            className={`${config.button} relative transition-all duration-200 ${
              isRecording ? 'animate-pulse ring-4 ring-red-300' : ''
            } ${
              disabled || !isConnected ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={disabled || !isConnected}
            onClick={handleClick}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp} // Prevent stuck state
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd} // Handle touch cancellation
            aria-label={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {getButtonIcon()}
            
            {/* Processing indicator */}
            {isProcessing && (
              <motion.div
                className="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            )}
          </Button>

          {/* Hold indicator */}
          {isHoldingToTalk && (
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0 }}
              className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-xs text-gray-500 whitespace-nowrap"
            >
              Hold to talk
            </motion.div>
          )}
        </motion.div>

        {/* Recording Timer */}
        {showTimer && (
          <AnimatePresence>
            <RecordingTimer
              startTime={recordingStartTime}
              isRecording={isRecording}
            />
          </AnimatePresence>
        )}
      </div>

      {/* Instructions */}
      <div className="text-center text-sm text-gray-500 max-w-xs">
        {disabled ? (
          'Voice controls disabled'
        ) : !isConnected ? (
          'Connecting to voice service...'
        ) : !hasAudioPermission ? (
          'Please allow microphone access'
        ) : isRecording ? (
          'Release to stop recording'
        ) : (
          <>
            <div>Press and hold <kbd className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs">Space</kbd> or click and hold to talk</div>
            <div className="text-xs mt-1">Click to toggle recording mode</div>
          </>
        )}
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="text-sm text-red-500 text-center max-w-xs"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};