'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ConversationEntry } from '@/store/voiceStore';
import { Play, Pause, Copy, Check, Volume2, User, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface MessageBubbleProps {
  message: ConversationEntry;
  showTimestamp?: boolean;
  enableTypewriter?: boolean;
  className?: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showTimestamp = true,
  enableTypewriter = false,
  className = '',
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [isTypewriterComplete, setIsTypewriterComplete] = useState(!enableTypewriter);
  const audioRef = useRef<HTMLAudioElement>(null);
  const typewriterRef = useRef<NodeJS.Timeout | null>(null);

  const isUser = message.type === 'user';
  const isAgent = message.type === 'agent';
  const isSystem = message.type === 'system';

  // Typewriter effect
  useEffect(() => {
    if (!enableTypewriter || isTypewriterComplete) {
      setDisplayedText(message.content);
      return;
    }

    let index = 0;
    setDisplayedText('');
    
    const typeWriter = () => {
      if (index < message.content.length) {
        setDisplayedText(message.content.slice(0, index + 1));
        index++;
        typewriterRef.current = setTimeout(typeWriter, 30 + Math.random() * 20); // Variable speed
      } else {
        setIsTypewriterComplete(true);
      }
    };

    typeWriter();

    return () => {
      if (typewriterRef.current) {
        clearTimeout(typewriterRef.current);
      }
    };
  }, [message.content, enableTypewriter, isTypewriterComplete]);

  // Audio playback
  const togglePlayback = async () => {
    if (!message.audioUrl || !audioRef.current) return;

    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        await audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Audio playback error:', error);
      }
    }
  };

  // Copy message
  const copyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Copy failed:', error);
      }
    }
  };

  // Format timestamp
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Get avatar icon
  const AvatarIcon = () => {
    if (isUser) return <User className="w-4 h-4" />;
    if (isAgent) return <Bot className="w-4 h-4" />;
    return <Volume2 className="w-4 h-4" />;
  };

  // Get bubble styles
  const getBubbleStyles = () => {
    if (isUser) {
      return 'ml-auto bg-gradient-to-r from-accent-purple to-accent-blue text-white';
    }
    if (isAgent) {
      return 'mr-auto glass border-accent-blue/20';
    }
    return 'mx-auto glass border-accent-green/20 text-accent-green';
  };

  // Get container styles
  const getContainerStyles = () => {
    if (isUser) return 'flex-row-reverse';
    return 'flex-row';
  };

  return (
    <motion.div
      layout
      className={`flex items-start gap-3 group ${getContainerStyles()} ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-gradient-to-r from-accent-purple to-accent-pink' 
            : isAgent
            ? 'bg-gradient-to-r from-accent-blue to-accent-green'
            : 'bg-gradient-to-r from-accent-green to-accent-orange'
        } shadow-lg`}
      >
        <AvatarIcon />
      </motion.div>

      {/* Message Content */}
      <div className={`flex flex-col max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Main Bubble */}
        <motion.div
          layout
          className={`relative px-4 py-3 rounded-2xl shadow-lg backdrop-blur-lg ${getBubbleStyles()} ${
            isUser ? 'rounded-br-sm' : 'rounded-bl-sm'
          }`}
        >
          {/* Message Text */}
          <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {displayedText}
            {enableTypewriter && !isTypewriterComplete && (
              <motion.span
                animate={{ opacity: [0, 1] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="inline-block w-2 h-4 bg-current ml-1"
              />
            )}
          </div>

          {/* Action Buttons */}
          <div className={`flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}>
            {/* Audio Playback */}
            {message.audioUrl && (
              <>
                <button
                  onClick={togglePlayback}
                  className="p-1.5 rounded-lg hover:bg-white/10 transition-colors duration-200 text-current"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                </button>
                <audio
                  ref={audioRef}
                  src={message.audioUrl}
                  onEnded={() => setIsPlaying(false)}
                  onError={() => setIsPlaying(false)}
                />
              </>
            )}

            {/* Copy Button */}
            <button
              onClick={copyMessage}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors duration-200 text-current"
              title="Copy message"
            >
              <AnimatePresence mode="wait">
                {isCopied ? (
                  <motion.div
                    key="check"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                  >
                    <Check className="w-3 h-3" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="copy"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                  >
                    <Copy className="w-3 h-3" />
                  </motion.div>
                )}
              </AnimatePresence>
            </button>
          </div>

          {/* Glassmorphism Border Effect */}
          {!isUser && (
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-accent-blue/10 via-transparent to-accent-green/10 pointer-events-none" />
          )}
        </motion.div>

        {/* Timestamp */}
        {showTimestamp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className={`text-xs text-foreground-muted mt-1 px-2 ${
              isUser ? 'text-right' : 'text-left'
            }`}
          >
            {formatTime(message.timestamp)}
          </motion.div>
        )}

        {/* Message Status/Metadata */}
        {message.metadata && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.3 }}
            className="text-xs text-foreground-muted mt-1 px-2 max-w-full"
          >
            {typeof message.metadata.confidence === 'number' && (
              <div className={`flex items-center gap-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div className="w-12 h-1 bg-border rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${message.metadata.confidence * 100}%` }}
                    transition={{ delay: 0.4, duration: 0.5 }}
                    className={`h-full rounded-full ${
                      message.metadata.confidence > 0.8 
                        ? 'bg-accent-green' 
                        : message.metadata.confidence > 0.6 
                        ? 'bg-accent-orange' 
                        : 'bg-accent-pink'
                    }`}
                  />
                </div>
                <span>{Math.round(message.metadata.confidence * 100)}%</span>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};