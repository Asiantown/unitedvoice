'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wifi, 
  WifiOff, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Keyboard,
  Mouse,
  Smartphone,
  Headphones
} from 'lucide-react';

import { useConnectionStatus, useRecordingStatus, useAudioVisualization } from '@/store/voiceStore';
import { useHoldToTalk } from '@/hooks/useHoldToTalk';
import { Button } from '@/components/ui/button';

interface TestPanelProps {
  compact?: boolean;
  className?: string;
}

interface DiagnosticEvent {
  id: string;
  timestamp: number;
  type: 'info' | 'success' | 'warning' | 'error';
  category: 'connection' | 'audio' | 'interaction' | 'system';
  message: string;
  data?: Record<string, unknown>;
}

interface KeyboardState {
  spacePressed: boolean;
  lastSpacePress: number | null;
  lastSpaceRelease: number | null;
  pressCount: number;
}

interface MouseState {
  mousePressed: boolean;
  lastMousePress: number | null;
  lastMouseRelease: number | null;
  pressCount: number;
  targetElement: string | null;
}

interface TouchState {
  touchPressed: boolean;
  lastTouchStart: number | null;
  lastTouchEnd: number | null;
  touchCount: number;
  touchPoints: number;
}

interface AudioState {
  level: number;
  peak: number;
  averageLevel: number;
  samples: number[];
  isDetectingSound: boolean;
  lastSoundTime: number | null;
}

interface NetworkState {
  latency: number | null;
  lastPing: number | null;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown';
  packetLoss: number;
}

export const TestPanel: React.FC<TestPanelProps> = ({ 
  compact = false, 
  className = '' 
}) => {
  // Store hooks
  const { connectionState, error: connectionError, lastConnectedAt } = useConnectionStatus();
  const { recordingState, isHoldingToTalk, recordingStartTime, recordingDuration } = useRecordingStatus();
  const { waveformData, currentAudioLevel } = useAudioVisualization();
  
  // Hold-to-talk hook for additional testing
  const {
    handleMouseDown,
    handleMouseUp,
    handleTouchStart,
    handleTouchEnd,
    audioLevel,
    isConnected,
    hasAudioPermission,
  } = useHoldToTalk();

  // Internal state
  const [diagnosticEvents, setDiagnosticEvents] = useState<DiagnosticEvent[]>([]);
  const [keyboardState, setKeyboardState] = useState<KeyboardState>({
    spacePressed: false,
    lastSpacePress: null,
    lastSpaceRelease: null,
    pressCount: 0
  });
  const [mouseState, setMouseState] = useState<MouseState>({
    mousePressed: false,
    lastMousePress: null,
    lastMouseRelease: null,
    pressCount: 0,
    targetElement: null
  });
  const [touchState, setTouchState] = useState<TouchState>({
    touchPressed: false,
    lastTouchStart: null,
    lastTouchEnd: null,
    touchCount: 0,
    touchPoints: 0
  });
  const [audioState, setAudioState] = useState<AudioState>({
    level: 0,
    peak: 0,
    averageLevel: 0,
    samples: [],
    isDetectingSound: false,
    lastSoundTime: null
  });
  const [networkState, setNetworkState] = useState<NetworkState>({
    latency: null,
    lastPing: null,
    connectionQuality: 'unknown',
    packetLoss: 0
  });

  const eventIdCounter = useRef(0);
  const audioSamplesRef = useRef<number[]>([]);

  // Add diagnostic event
  const addEvent = (
    type: DiagnosticEvent['type'],
    category: DiagnosticEvent['category'],
    message: string,
    data?: Record<string, unknown>
  ) => {
    const event: DiagnosticEvent = {
      id: `${Date.now()}-${++eventIdCounter.current}`,
      timestamp: Date.now(),
      type,
      category,
      message,
      data
    };

    setDiagnosticEvents(prev => {
      const newEvents = [event, ...prev];
      return newEvents.slice(0, compact ? 20 : 50); // Limit events
    });
  };

  // Clear events
  const clearEvents = () => {
    setDiagnosticEvents([]);
  };

  // Keyboard event monitoring
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'Space' && !event.repeat) {
        const now = Date.now();
        setKeyboardState(prev => ({
          ...prev,
          spacePressed: true,
          lastSpacePress: now,
          pressCount: prev.pressCount + 1
        }));
        
        addEvent('info', 'interaction', 'Spacebar pressed', {
          timestamp: now,
          repeat: event.repeat,
          pressCount: keyboardState.pressCount + 1
        });
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === 'Space') {
        const now = Date.now();
        const duration = keyboardState.lastSpacePress ? now - keyboardState.lastSpacePress : 0;
        
        setKeyboardState(prev => ({
          ...prev,
          spacePressed: false,
          lastSpaceRelease: now
        }));

        addEvent('success', 'interaction', `Spacebar released (held for ${duration}ms)`, {
          timestamp: now,
          duration,
          holdTime: duration
        });
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, [keyboardState.lastSpacePress, keyboardState.pressCount]);

  // Mouse event monitoring
  useEffect(() => {
    const handleMouseDownGlobal = (event: MouseEvent) => {
      const now = Date.now();
      const target = event.target as HTMLElement;
      const targetInfo = target.tagName + (target.className ? `.${target.className.split(' ')[0]}` : '');
      
      setMouseState(prev => ({
        ...prev,
        mousePressed: true,
        lastMousePress: now,
        pressCount: prev.pressCount + 1,
        targetElement: targetInfo
      }));

      addEvent('info', 'interaction', `Mouse pressed on ${targetInfo}`, {
        timestamp: now,
        target: targetInfo,
        button: event.button,
        pressCount: mouseState.pressCount + 1
      });
    };

    const handleMouseUpGlobal = (event: MouseEvent) => {
      const now = Date.now();
      const duration = mouseState.lastMousePress ? now - mouseState.lastMousePress : 0;
      
      setMouseState(prev => ({
        ...prev,
        mousePressed: false,
        lastMouseRelease: now
      }));

      addEvent('success', 'interaction', `Mouse released (held for ${duration}ms)`, {
        timestamp: now,
        duration,
        button: event.button,
        holdTime: duration
      });
    };

    document.addEventListener('mousedown', handleMouseDownGlobal);
    document.addEventListener('mouseup', handleMouseUpGlobal);

    return () => {
      document.removeEventListener('mousedown', handleMouseDownGlobal);
      document.removeEventListener('mouseup', handleMouseUpGlobal);
    };
  }, [mouseState.lastMousePress, mouseState.pressCount]);

  // Touch event monitoring
  useEffect(() => {
    const handleTouchStartGlobal = (event: TouchEvent) => {
      const now = Date.now();
      
      setTouchState(prev => ({
        ...prev,
        touchPressed: true,
        lastTouchStart: now,
        touchCount: prev.touchCount + 1,
        touchPoints: event.touches.length
      }));

      addEvent('info', 'interaction', `Touch started (${event.touches.length} points)`, {
        timestamp: now,
        touchPoints: event.touches.length,
        touchCount: touchState.touchCount + 1
      });
    };

    const handleTouchEndGlobal = (event: TouchEvent) => {
      const now = Date.now();
      const duration = touchState.lastTouchStart ? now - touchState.lastTouchStart : 0;
      
      setTouchState(prev => ({
        ...prev,
        touchPressed: false,
        lastTouchEnd: now
      }));

      addEvent('success', 'interaction', `Touch ended (held for ${duration}ms)`, {
        timestamp: now,
        duration,
        remainingTouches: event.touches.length,
        holdTime: duration
      });
    };

    document.addEventListener('touchstart', handleTouchStartGlobal);
    document.addEventListener('touchend', handleTouchEndGlobal);

    return () => {
      document.removeEventListener('touchstart', handleTouchStartGlobal);
      document.removeEventListener('touchend', handleTouchEndGlobal);
    };
  }, [touchState.lastTouchStart, touchState.touchCount]);

  // Audio level monitoring
  useEffect(() => {
    if (currentAudioLevel !== undefined) {
      const now = Date.now();
      const level = currentAudioLevel || audioLevel || 0;
      
      // Update samples
      audioSamplesRef.current.push(level);
      if (audioSamplesRef.current.length > 100) {
        audioSamplesRef.current = audioSamplesRef.current.slice(-100);
      }

      const averageLevel = audioSamplesRef.current.reduce((a, b) => a + b, 0) / audioSamplesRef.current.length;
      const isDetectingSound = level > 0.1; // Threshold for sound detection
      
      setAudioState(prev => ({
        ...prev,
        level,
        peak: Math.max(prev.peak, level),
        averageLevel,
        samples: audioSamplesRef.current,
        isDetectingSound,
        lastSoundTime: isDetectingSound ? now : prev.lastSoundTime
      }));

      // Log significant audio events
      if (isDetectingSound && !audioState.isDetectingSound) {
        addEvent('info', 'audio', `Sound detected (level: ${(level * 100).toFixed(1)}%)`, {
          level,
          averageLevel,
          timestamp: now
        });
      }
    }
  }, [currentAudioLevel, audioLevel, audioState.isDetectingSound]);

  // Connection state monitoring
  useEffect(() => {
    const stateMessages = {
      'connecting': 'Connecting to server...',
      'connected': 'Successfully connected to server',
      'reconnecting': 'Reconnecting to server...',
      'disconnected': 'Disconnected from server',
      'error': 'Connection error occurred'
    };

    const eventTypes: Record<string, DiagnosticEvent['type']> = {
      'connected': 'success',
      'connecting': 'info',
      'reconnecting': 'warning',
      'disconnected': 'warning',
      'error': 'error'
    };

    if (connectionState in stateMessages) {
      addEvent(
        eventTypes[connectionState],
        'connection',
        stateMessages[connectionState as keyof typeof stateMessages],
        { 
          connectionState, 
          hasError: !!connectionError,
          error: connectionError 
        }
      );
    }
  }, [connectionState, connectionError]);

  // Recording state monitoring
  useEffect(() => {
    const stateMessages = {
      'idle': 'Recording idle',
      'recording': 'Recording started',
      'uploading': 'Uploading audio data',
      'processing': 'Processing audio on server'
    };

    if (recordingState in stateMessages) {
      addEvent(
        recordingState === 'recording' ? 'success' : 'info',
        'audio',
        stateMessages[recordingState as keyof typeof stateMessages],
        { 
          recordingState,
          isHoldingToTalk,
          duration: recordingDuration 
        }
      );
    }
  }, [recordingState, isHoldingToTalk, recordingDuration]);

  // Network latency testing
  useEffect(() => {
    if (!isConnected) return;

    const testLatency = async () => {
      const start = performance.now();
      try {
        await fetch('http://localhost:8000/health', { method: 'HEAD' });
        const latency = performance.now() - start;
        
        setNetworkState(prev => ({
          ...prev,
          latency,
          lastPing: Date.now(),
          connectionQuality: 
            latency < 100 ? 'excellent' :
            latency < 200 ? 'good' :
            latency < 500 ? 'fair' : 'poor'
        }));
      } catch (error) {
        setNetworkState(prev => ({
          ...prev,
          latency: null,
          connectionQuality: 'poor'
        }));
      }
    };

    const interval = setInterval(testLatency, 5000);
    testLatency(); // Initial test

    return () => clearInterval(interval);
  }, [isConnected]);

  const getStatusColor = (type: DiagnosticEvent['type']) => {
    switch (type) {
      case 'success': return 'text-green-600 dark:text-green-400';
      case 'error': return 'text-red-600 dark:text-red-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      default: return 'text-blue-600 dark:text-blue-400';
    }
  };

  const getStatusIcon = (type: DiagnosticEvent['type']) => {
    const iconProps = { className: "w-3 h-3" };
    switch (type) {
      case 'success': return <CheckCircle {...iconProps} />;
      case 'error': return <XCircle {...iconProps} />;
      case 'warning': return <AlertTriangle {...iconProps} />;
      default: return <Info {...iconProps} />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString(undefined, { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 1
    });
  };

  const StatCard = ({ 
    title, 
    value, 
    icon, 
    color = 'text-gray-600 dark:text-gray-400',
    onClick 
  }: {
    title: string;
    value: string;
    icon: React.ReactNode;
    color?: string;
    onClick?: () => void;
  }) => (
    <div 
      className={`bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 ${onClick ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 mb-1">
        <div className={color}>{icon}</div>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{title}</span>
      </div>
      <div className="text-sm font-mono text-gray-900 dark:text-gray-100">{value}</div>
    </div>
  );

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
      <div className="p-4">
        {!compact && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Real-time Diagnostics
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={clearEvents}
              className="text-xs"
            >
              Clear
            </Button>
          </div>
        )}

        {/* Status Overview */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <StatCard
            title="Connection"
            value={connectionState || 'unknown'}
            icon={isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            color={isConnected ? 'text-green-500' : 'text-red-500'}
          />
          
          <StatCard
            title="Audio"
            value={hasAudioPermission ? 'enabled' : 'disabled'}
            icon={hasAudioPermission ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
            color={hasAudioPermission ? 'text-green-500' : 'text-red-500'}
          />
          
          <StatCard
            title="Recording"
            value={recordingState || 'idle'}
            icon={recordingState === 'recording' ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            color={recordingState === 'recording' ? 'text-red-500' : 'text-gray-500'}
          />
          
          <StatCard
            title="Audio Level"
            value={`${(audioState.level * 100).toFixed(0)}%`}
            icon={<Activity className="w-4 h-4" />}
            color={audioState.isDetectingSound ? 'text-blue-500' : 'text-gray-500'}
          />
        </div>

        {/* Interaction State */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <StatCard
            title="Space"
            value={keyboardState.spacePressed ? 'held' : 'released'}
            icon={<Keyboard className="w-3 h-3" />}
            color={keyboardState.spacePressed ? 'text-blue-500' : 'text-gray-500'}
          />
          
          <StatCard
            title="Mouse"
            value={mouseState.mousePressed ? 'held' : 'released'}
            icon={<Mouse className="w-3 h-3" />}
            color={mouseState.mousePressed ? 'text-blue-500' : 'text-gray-500'}
          />
          
          <StatCard
            title="Touch"
            value={touchState.touchPressed ? `${touchState.touchPoints}pts` : 'released'}
            icon={<Smartphone className="w-3 h-3" />}
            color={touchState.touchPressed ? 'text-blue-500' : 'text-gray-500'}
          />
        </div>

        {/* Network State */}
        {networkState.latency && (
          <div className="mb-4">
            <StatCard
              title="Network Latency"
              value={`${networkState.latency.toFixed(0)}ms (${networkState.connectionQuality})`}
              icon={<Wifi className="w-4 h-4" />}
              color={
                networkState.connectionQuality === 'excellent' ? 'text-green-500' :
                networkState.connectionQuality === 'good' ? 'text-blue-500' :
                networkState.connectionQuality === 'fair' ? 'text-yellow-500' : 'text-red-500'
              }
            />
          </div>
        )}

        {/* Audio Waveform Preview */}
        {!compact && recordingState === 'recording' && audioState.samples.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Audio Waveform
            </div>
            <div className="h-16 bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
              <div className="flex items-end h-full gap-0.5 justify-center">
                {audioState.samples.slice(-50).map((sample, index) => (
                  <div
                    key={index}
                    className="bg-blue-500 min-h-[2px] w-1"
                    style={{ height: `${Math.max(sample * 100, 2)}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Event Log */}
        <div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
            Event Log ({diagnosticEvents.length})
          </div>
          <div className={`space-y-2 ${compact ? 'max-h-40' : 'max-h-64'} overflow-auto`}>
            <AnimatePresence initial={false}>
              {diagnosticEvents.map((event) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="bg-gray-50 dark:bg-gray-700/50 rounded p-2"
                >
                  <div className="flex items-start gap-2">
                    <div className={getStatusColor(event.type)}>
                      {getStatusIcon(event.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-900 dark:text-gray-100">
                        {event.message}
                      </div>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-xs text-gray-500 capitalize">
                          {event.category}
                        </span>
                        <span className="text-xs text-gray-500 font-mono">
                          {formatTimestamp(event.timestamp)}
                        </span>
                      </div>
                      
                      {/* Additional data for debugging */}
                      {event.data && Object.keys(event.data).length > 0 && (
                        <details className="mt-1">
                          <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                            Debug data
                          </summary>
                          <pre className="text-xs text-gray-600 dark:text-gray-400 mt-1 p-1 bg-gray-100 dark:bg-gray-800 rounded overflow-auto">
                            {JSON.stringify(event.data, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {diagnosticEvents.length === 0 && (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                <Activity className="w-6 h-6 mx-auto mb-2 opacity-50" />
                <div className="text-xs">No events yet</div>
                <div className="text-xs">Start interacting to see diagnostics</div>
              </div>
            )}
          </div>
        </div>

        {/* Test Actions */}
        {!compact && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Manual Tests
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  addEvent('info', 'system', 'Manual connection test triggered');
                  // Trigger connection test
                }}
                className="text-xs"
              >
                Test Connection
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  addEvent('info', 'system', 'Manual audio test triggered');
                  // Trigger audio test
                }}
                className="text-xs"
              >
                Test Audio
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};