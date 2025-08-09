'use client';

import React, { useState, useEffect } from 'react';
import { TranscriptionEntry } from '@/store/voiceStore';
import { Mic, MicOff, AlertCircle, Volume2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TranscriptionIndicatorProps {
  transcription?: TranscriptionEntry;
  isListening?: boolean;
  error?: string | null;
  className?: string;
  compact?: boolean;
}

export const TranscriptionIndicator: React.FC<TranscriptionIndicatorProps> = ({
  transcription,
  isListening = false,
  error,
  className = '',
  compact = false,
}) => {
  const [dots, setDots] = useState('');

  // Animate processing dots
  useEffect(() => {
    if (!isListening && !transcription?.text) return;

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isListening, transcription?.text]);

  // Get confidence color
  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-foreground-muted';
    if (confidence >= 0.8) return 'text-accent-green';
    if (confidence >= 0.6) return 'text-accent-orange';
    return 'text-accent-pink';
  };

  // Get confidence level text
  const getConfidenceText = (confidence?: number) => {
    if (!confidence) return 'Processing';
    if (confidence >= 0.8) return 'High confidence';
    if (confidence >= 0.6) return 'Medium confidence';
    return 'Low confidence';
  };

  // Show error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={`glass border border-accent-pink/30 rounded-lg p-3 ${className}`}
      >
        <div className="flex items-center gap-2 text-accent-pink">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">Transcription Error</p>
            <p className="text-xs opacity-80 truncate">{error}</p>
          </div>
        </div>
      </motion.div>
    );
  }

  // Show empty state when not listening and no transcription
  if (!isListening && !transcription?.text) {
    return null;
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={transcription?.id || 'listening'}
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.2, type: "spring", stiffness: 200 }}
        className={`glass border border-accent-blue/30 rounded-lg ${compact ? 'p-2' : 'p-3'} ${className}`}
      >
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div className="flex-shrink-0 mt-0.5">
            <motion.div
              animate={isListening ? { scale: [1, 1.1, 1] } : {}}
              transition={isListening ? { duration: 1, repeat: Infinity } : {}}
              className={`w-5 h-5 rounded-full flex items-center justify-center ${
                isListening 
                  ? 'bg-accent-green text-white' 
                  : transcription?.isFinal
                  ? 'bg-accent-blue text-white'
                  : 'bg-accent-orange text-white'
              }`}
            >
              {isListening ? (
                <Mic className="w-3 h-3" />
              ) : transcription?.isFinal ? (
                <Volume2 className="w-3 h-3" />
              ) : (
                <div className="w-2 h-2 rounded-full bg-current animate-pulse" />
              )}
            </motion.div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Status Text */}
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${
                  isListening 
                    ? 'text-accent-green' 
                    : transcription?.isFinal
                    ? 'text-accent-blue'
                    : 'text-accent-orange'
                }`}>
                  {isListening 
                    ? `Listening${dots}` 
                    : transcription?.isFinal
                    ? 'Final'
                    : `Processing${dots}`
                  }
                </span>
                
                {/* Real-time confidence indicator */}
                {transcription?.confidence !== undefined && (
                  <div className="flex items-center gap-1">
                    <div className="w-6 h-1 bg-border rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${transcription.confidence * 100}%` }}
                        transition={{ duration: 0.3 }}
                        className={`h-full rounded-full ${
                          transcription.confidence >= 0.8 
                            ? 'bg-accent-green' 
                            : transcription.confidence >= 0.6 
                            ? 'bg-accent-orange' 
                            : 'bg-accent-pink'
                        }`}
                      />
                    </div>
                    <span className={`text-xs ${getConfidenceColor(transcription.confidence)}`}>
                      {Math.round(transcription.confidence * 100)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Timestamp */}
              {transcription?.timestamp && (
                <span className="text-xs text-foreground-muted">
                  {new Date(transcription.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </span>
              )}
            </div>

            {/* Transcription Text */}
            {transcription?.text && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2 }}
                className="text-sm text-foreground leading-relaxed"
              >
                <span className={transcription.isFinal ? 'text-foreground' : 'text-foreground-muted'}>
                  {transcription.text}
                </span>
                {!transcription.isFinal && (
                  <motion.span
                    animate={{ opacity: [0, 1] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                    className="inline-block w-2 h-4 bg-accent-blue ml-1"
                  />
                )}
              </motion.div>
            )}

            {/* Listening prompt */}
            {isListening && !transcription?.text && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-sm text-foreground-muted italic"
              >
                Speak now, I&apos;m listening...
              </motion.p>
            )}

            {/* Confidence explanation */}
            {transcription?.confidence !== undefined && !compact && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ delay: 0.1 }}
                className="mt-2 text-xs text-foreground-muted"
              >
                {getConfidenceText(transcription.confidence)}
              </motion.div>
            )}
          </div>
        </div>

        {/* Processing animation background */}
        {!transcription?.isFinal && (transcription?.text || isListening) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.1, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 bg-gradient-to-r from-accent-blue/20 via-accent-purple/20 to-accent-green/20 rounded-lg pointer-events-none"
          />
        )}

        {/* Subtle glow effect */}
        <div className={`absolute inset-0 rounded-lg pointer-events-none ${
          isListening
            ? 'shadow-[0_0_15px_rgba(16,185,129,0.2)]'
            : transcription?.isFinal
            ? 'shadow-[0_0_15px_rgba(59,130,246,0.2)]'
            : 'shadow-[0_0_15px_rgba(245,158,11,0.2)]'
        }`} />
      </motion.div>
    </AnimatePresence>
  );
};