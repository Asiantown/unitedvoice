'use client';

import React, { useEffect, useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, X, AlertCircle } from 'lucide-react';

import { StatusBar } from '@/components/StatusBar';
import VoiceOrb from '@/components/VoiceOrb';
import { VoiceControls } from '@/components/VoiceControls';
import { ConversationPanel } from '@/components/ConversationPanel';
import { SettingsPanel } from '@/components/SettingsPanel';
import { AudioWaveform } from '@/components/AudioWaveform';
import { Button } from '@/components/ui/button';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useDeviceDetection } from '@/hooks/useDeviceDetection';
import { useConnectionStatus, useRecordingStatus } from '@/store/voiceStore';

/**
 * Props for the VoiceInterface component
 */
interface VoiceInterfaceProps {
  /** Optional CSS class name */
  className?: string;
}

/**
 * Configuration for keyboard shortcuts
 */
interface KeyboardShortcuts {
  settings: string;
  fullscreen: string;
  escape: string;
}

/**
 * Error Boundary Component for handling React errors gracefully
 */
class VoiceErrorBoundary extends React.Component<
  { 
    children: React.ReactNode; 
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; onError?: (error: Error, errorInfo: React.ErrorInfo) => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): { hasError: boolean; error: Error } {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    if (process.env.NODE_ENV === 'development') {
      console.error('Voice Interface Error:', error, errorInfo);
    }
    this.props.onError?.(error, errorInfo);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background" role="alert">
          <div className="glass-card p-8 max-w-md text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Something went wrong
            </h2>
            <p className="text-foreground-muted mb-4">
              The voice interface encountered an error. Please refresh the page to try again.
            </p>
            <Button
              onClick={() => window.location.reload()}
              variant="default"
              aria-label="Refresh the page"
            >
              Refresh Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Main voice interface component with error boundaries and accessibility
 * Provides the complete voice interaction UI including orb, controls, and conversation
 */
export const VoiceInterface: React.FC<VoiceInterfaceProps> = memo(({
  className = ''
}) => {
  // Component state
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [hasAudioPermission, setHasAudioPermission] = useState<boolean>(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Store selectors
  const { connectionState, error: wsError } = useConnectionStatus();
  const { recordingState } = useRecordingStatus();
  const isRecording = recordingState === 'recording';

  // Device detection
  const { deviceInfo, getControlInstructions } = useDeviceDetection();

  // WebSocket hook
  const {
    connect,
    disconnect,
    isConnected: wsConnected,
  } = useWebSocket();

  // Keyboard shortcuts configuration
  const keyboardShortcuts: KeyboardShortcuts = {
    settings: ',',
    fullscreen: 'F11',
    escape: 'Escape'
  };

  /**
   * Requests microphone permission from the user
   */
  const requestAudioPermission = useCallback(async (): Promise<void> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });
      
      // Stop the stream immediately, we just needed permission
      stream.getTracks().forEach(track => track.stop());
      
      setHasAudioPermission(true);
      setAudioError(null);
    } catch (error) {
      const errorMessage = 'Microphone access is required for voice functionality';
      setAudioError(errorMessage);
      setHasAudioPermission(false);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('Audio permission denied:', error);
      }
    }
  }, []);

  // Request audio permissions on mount
  useEffect(() => {
    requestAudioPermission();
  }, [requestAudioPermission]);

  /**
   * Toggles fullscreen mode
   */
  const toggleFullscreen = useCallback(async (): Promise<void> => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Fullscreen toggle failed:', error);
      }
    }
  }, []);

  // Initialize WebSocket connection when audio permission is granted
  useEffect(() => {
    if (hasAudioPermission && !wsConnected) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [hasAudioPermission, connect, disconnect, wsConnected]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      // Ignore shortcuts if user is in an input field
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Settings toggle (Cmd/Ctrl + ,)
      if ((event.metaKey || event.ctrlKey) && event.key === keyboardShortcuts.settings) {
        event.preventDefault();
        setIsSettingsOpen(prev => !prev);
      }
      
      // Fullscreen toggle (F11)
      if (event.key === keyboardShortcuts.fullscreen) {
        event.preventDefault();
        toggleFullscreen();
      }
      
      // Escape to close settings
      if (event.key === keyboardShortcuts.escape && isSettingsOpen) {
        event.preventDefault();
        setIsSettingsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, keyboardShortcuts, toggleFullscreen]);

  // Handle fullscreen state changes
  useEffect(() => {
    const handleFullscreenChange = (): void => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  /**
   * Handles errors from the error boundary
   */
  const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo): void => {
    // In production, this could send to error tracking service
    if (process.env.NODE_ENV === 'development') {
      console.error('Voice Interface Error:', error, errorInfo);
    }
  }, []);

  // Memoized error state
  const currentError = audioError || wsError;

  return (
    <VoiceErrorBoundary onError={handleError}>
      <main 
        className={`min-h-screen relative overflow-hidden bg-background ${className}`}
        role="main"
        aria-label="United Voice Agent Interface"
      >
        {/* Ambient background - decorative only */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent-purple/5 via-transparent to-accent-blue/5" aria-hidden="true" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.1),transparent_50%)]" aria-hidden="true" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.1),transparent_50%)]" aria-hidden="true" />

        {/* Status Bar */}
        <header className="relative z-20 p-4">
          <StatusBar
            showNetworkQuality={true}
            showSessionDuration={true}
            compact={false}
            className="mb-0"
          />
        </header>

        {/* Main Interface */}
        <div className="flex flex-1 min-h-0 relative z-10">
          {/* Central Voice Area */}
          <section className="flex-1 flex flex-col items-center justify-center relative px-4" aria-label="Voice interaction area">
            {/* 3D Orb */}
            <div className="mb-8 relative">
              <VoiceOrb 
                isRecording={isRecording}
                audioLevel={0} // This would come from audio processing
                isConnected={wsConnected && hasAudioPermission}
                size="large"
              />
              
              {/* Audio waveform overlay when recording */}
              <AnimatePresence>
                {isRecording && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="absolute -bottom-16 left-1/2 transform -translate-x-1/2"
                    role="img"
                    aria-label="Audio waveform visualization"
                  >
                    <AudioWaveform
                      isRecording={isRecording}
                      audioLevel={0.5} // This would come from real audio analysis
                      width={300}
                      height={60}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Voice Controls */}
            <div className="mb-8">
              <VoiceControls
                size="lg"
                showTimer={true}
                showWaveform={false} // We show the waveform separately above
                showConnectionStatus={false} // Shown in status bar instead
                disabled={!hasAudioPermission}
                className="mb-4"
              />
            </div>

            {/* Connection/Error Status */}
            <AnimatePresence>
              {currentError && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="glass-card p-4 max-w-md text-center border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/50"
                >
                  <AlertCircle className="w-5 h-5 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-red-600 dark:text-red-400">
                    {currentError}
                  </p>
                  {audioError && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2"
                      onClick={() => window.location.reload()}
                    >
                      Retry Permission
                    </Button>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Control Instructions/Keyboard Shortcuts Hint */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-center">
              <p className="text-xs text-foreground-muted">
                {deviceInfo.shouldUseTouchControls ? (
                  <>
                    Touch and hold mic to talk • 
                    <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">⌘,</kbd> for settings •
                    <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">F11</kbd> for fullscreen
                  </>
                ) : (
                  <>
                    Press <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Space</kbd> to talk • 
                    <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">⌘,</kbd> for settings •
                    <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">F11</kbd> for fullscreen
                  </>
                )}
              </p>
            </div>
          </section>

          {/* Conversation Panel */}
          <aside 
            className="w-80 xl:w-96 flex flex-col relative border-l border-border bg-card/30 backdrop-blur-sm"
            role="complementary"
            aria-label="Conversation history"
          >
            <div className="flex-1 min-h-0 p-4">
              <ConversationPanel
                showTranscription={true}
                autoScroll={true}
                maxMessages={100}
                className="h-full"
              />
            </div>
          </aside>
        </div>

        {/* Settings Button */}
        <motion.div
          className="fixed top-4 right-4 z-30"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsSettingsOpen(true)}
            className="glass-button"
            aria-label="Open settings panel"
          >
            <Settings className="w-4 h-4" aria-hidden="true" />
          </Button>
        </motion.div>

        {/* Settings Panel */}
        <AnimatePresence>
          {isSettingsOpen && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
                onClick={() => setIsSettingsOpen(false)}
              />
              
              {/* Settings Panel */}
              <motion.div
                initial={{ opacity: 0, x: 400 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 400 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className="fixed right-0 top-0 h-full w-80 xl:w-96 z-50 bg-card border-l border-border shadow-2xl"
              >
                {/* Settings Header */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                  <h2 className="text-lg font-semibold text-foreground">Settings</h2>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsSettingsOpen(false)}
                    aria-label="Close settings"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* Settings Content */}
                <div className="flex-1 overflow-auto">
                  <SettingsPanel 
                    isFullscreen={isFullscreen}
                    onToggleFullscreen={toggleFullscreen}
                    onClose={() => setIsSettingsOpen(false)}
                  />
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Decorative elements for ambience - purely visual */}
        <div className="fixed top-1/4 left-10 w-2 h-2 bg-accent-purple rounded-full animate-pulse opacity-30 pointer-events-none" aria-hidden="true" />
        <div className="fixed top-1/3 right-10 w-1 h-1 bg-accent-blue rounded-full animate-pulse opacity-20 pointer-events-none" aria-hidden="true" />
        <div className="fixed bottom-1/4 left-1/4 w-1.5 h-1.5 bg-accent-pink rounded-full animate-pulse opacity-25 pointer-events-none" aria-hidden="true" />
        <div className="fixed bottom-1/3 right-1/3 w-1 h-1 bg-accent-green rounded-full animate-pulse opacity-15 pointer-events-none" aria-hidden="true" />
      </main>
    </VoiceErrorBoundary>
  );
});