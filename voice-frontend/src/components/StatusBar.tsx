'use client';

import React, { useState, useEffect } from 'react';
import { useConnectionStatus, useRecordingStatus } from '@/store/voiceStore';
import { 
  Wifi, 
  WifiOff, 
  Circle, 
  Timer, 
  Activity, 
  AlertCircle,
  CheckCircle,
  Loader2,
  Signal,
  SignalHigh,
  SignalLow,
  SignalMedium
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface StatusBarProps {
  className?: string;
  showNetworkQuality?: boolean;
  showSessionDuration?: boolean;
  compact?: boolean;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  className = '',
  showNetworkQuality = true,
  showSessionDuration = true,
  compact = false,
}) => {
  const { connectionState, error, lastConnectedAt } = useConnectionStatus();
  const { recordingState, isHoldingToTalk, recordingDuration } = useRecordingStatus();
  
  const [sessionDuration, setSessionDuration] = useState(0);
  const [networkQuality, setNetworkQuality] = useState<'poor' | 'fair' | 'good' | 'excellent'>('good');
  const [latency, setLatency] = useState<number>(0);

  // Calculate session duration
  useEffect(() => {
    if (!lastConnectedAt) return;

    const interval = setInterval(() => {
      setSessionDuration(Math.floor((Date.now() - lastConnectedAt) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [lastConnectedAt]);

  // Simulate network quality monitoring
  useEffect(() => {
    const checkNetworkQuality = async () => {
      if (connectionState !== 'connected') return;

      const start = Date.now();
      
      try {
        // Simple network test - in real implementation, this would ping the WebSocket server
        await fetch('/api/ping', { method: 'HEAD' }).catch(() => {});
        const latencyMs = Date.now() - start;
        setLatency(latencyMs);
        
        // Determine quality based on latency
        if (latencyMs < 50) setNetworkQuality('excellent');
        else if (latencyMs < 150) setNetworkQuality('good');
        else if (latencyMs < 300) setNetworkQuality('fair');
        else setNetworkQuality('poor');
      } catch {
        setNetworkQuality('poor');
        setLatency(999);
      }
    };

    const interval = setInterval(checkNetworkQuality, 5000);
    checkNetworkQuality(); // Initial check

    return () => clearInterval(interval);
  }, [connectionState]);

  // Format duration
  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Get connection status info
  const getConnectionInfo = () => {
    switch (connectionState) {
      case 'connected':
        return {
          icon: CheckCircle,
          text: 'Connected',
          color: 'text-accent-green',
          bgColor: 'bg-accent-green/10',
          borderColor: 'border-accent-green/30'
        };
      case 'connecting':
      case 'reconnecting':
        return {
          icon: Loader2,
          text: connectionState === 'connecting' ? 'Connecting' : 'Reconnecting',
          color: 'text-accent-blue',
          bgColor: 'bg-accent-blue/10',
          borderColor: 'border-accent-blue/30'
        };
      case 'error':
        return {
          icon: AlertCircle,
          text: 'Connection Error',
          color: 'text-accent-pink',
          bgColor: 'bg-accent-pink/10',
          borderColor: 'border-accent-pink/30'
        };
      default:
        return {
          icon: WifiOff,
          text: 'Disconnected',
          color: 'text-foreground-muted',
          bgColor: 'bg-card',
          borderColor: 'border-border'
        };
    }
  };

  // Get recording state info
  const getRecordingInfo = () => {
    switch (recordingState) {
      case 'recording':
        return {
          icon: Circle,
          text: isHoldingToTalk ? 'Hold to Talk' : 'Recording',
          color: 'text-accent-pink',
          pulse: true
        };
      case 'processing':
        return {
          icon: Loader2,
          text: 'Processing',
          color: 'text-accent-blue',
          spin: true
        };
      case 'uploading':
        return {
          icon: Activity,
          text: 'Uploading',
          color: 'text-accent-orange',
          pulse: true
        };
      default:
        return {
          icon: Circle,
          text: 'Ready',
          color: 'text-foreground-muted',
          pulse: false
        };
    }
  };

  // Get network quality icon
  const getNetworkIcon = () => {
    switch (networkQuality) {
      case 'excellent':
        return { icon: Signal, color: 'text-accent-green' };
      case 'good':
        return { icon: SignalHigh, color: 'text-accent-blue' };
      case 'fair':
        return { icon: SignalMedium, color: 'text-accent-orange' };
      default:
        return { icon: SignalLow, color: 'text-accent-pink' };
    }
  };

  const connectionInfo = getConnectionInfo();
  const recordingInfo = getRecordingInfo();
  const networkInfo = getNetworkIcon();

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass border rounded-lg p-3 ${connectionInfo.borderColor} ${className}`}
    >
      <div className={`flex items-center ${compact ? 'gap-3' : 'gap-4'} text-sm`}>
        {/* Connection Status */}
        <motion.div 
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${connectionInfo.bgColor} ${connectionInfo.borderColor} border`}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.1 }}
        >
          <motion.div
            animate={connectionState === 'connecting' || connectionState === 'reconnecting' ? { rotate: 360 } : {}}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <connectionInfo.icon className={`w-3 h-3 ${connectionInfo.color}`} />
          </motion.div>
          <span className={`font-medium ${connectionInfo.color}`}>
            {connectionInfo.text}
          </span>
        </motion.div>

        {/* Recording Status */}
        <motion.div 
          className="flex items-center gap-2"
          animate={recordingInfo.pulse ? { scale: [1, 1.05, 1] } : {}}
          transition={recordingInfo.pulse ? { duration: 1, repeat: Infinity } : {}}
        >
          <motion.div
            animate={recordingInfo.spin ? { rotate: 360 } : {}}
            transition={recordingInfo.spin ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
          >
            <recordingInfo.icon className={`w-3 h-3 ${recordingInfo.color}`} />
          </motion.div>
          <span className={`font-medium ${recordingInfo.color}`}>
            {recordingInfo.text}
          </span>
          
          {/* Recording Duration */}
          {recordingState === 'recording' && recordingDuration > 0 && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-xs text-foreground-muted font-mono bg-card px-2 py-0.5 rounded"
            >
              {formatDuration(Math.floor(recordingDuration / 1000))}
            </motion.span>
          )}
        </motion.div>

        {/* Network Quality */}
        {showNetworkQuality && connectionState === 'connected' && (
          <motion.div 
            className="flex items-center gap-2"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <networkInfo.icon className={`w-3 h-3 ${networkInfo.color}`} />
            {!compact && (
              <span className={`text-xs font-medium capitalize ${networkInfo.color}`}>
                {networkQuality}
              </span>
            )}
            {latency > 0 && (
              <span className="text-xs text-foreground-muted font-mono">
                {latency}ms
              </span>
            )}
          </motion.div>
        )}

        {/* Session Duration */}
        {showSessionDuration && lastConnectedAt && (
          <motion.div 
            className="flex items-center gap-2 ml-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Timer className="w-3 h-3 text-foreground-muted" />
            <span className="text-xs text-foreground-muted font-mono">
              {formatDuration(sessionDuration)}
            </span>
          </motion.div>
        )}

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="flex items-center gap-2 text-accent-pink bg-accent-pink/10 px-2 py-1 rounded border border-accent-pink/30"
            >
              <AlertCircle className="w-3 h-3 flex-shrink-0" />
              <span className="text-xs font-medium truncate max-w-32">
                {error}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Detailed Status (Non-compact mode) */}
      {!compact && connectionState === 'connected' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ delay: 0.3 }}
          className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-foreground-muted"
        >
          <div className="flex items-center gap-4">
            <span>Network: {networkQuality}</span>
            <span>Latency: {latency}ms</span>
            {recordingState !== 'idle' && (
              <span className="capitalize">Audio: {recordingState}</span>
            )}
          </div>
          
          {lastConnectedAt && (
            <span>
              Connected at {new Date(lastConnectedAt).toLocaleTimeString()}
            </span>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};