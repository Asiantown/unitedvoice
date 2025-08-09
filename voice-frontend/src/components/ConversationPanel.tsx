'use client';

import React, { useEffect, useRef, useState } from 'react';
import { MessageBubble } from './MessageBubble';
import { TranscriptionIndicator } from './TranscriptionIndicator';
import { useConversation } from '@/store/voiceStore';
import { AnimatePresence, motion } from 'framer-motion';
import { Copy, RotateCcw } from 'lucide-react';

export interface ConversationPanelProps {
  className?: string;
  showTranscription?: boolean;
  autoScroll?: boolean;
  maxMessages?: number;
}

export const ConversationPanel: React.FC<ConversationPanelProps> = ({
  className = '',
  showTranscription = true,
  autoScroll = true,
  maxMessages = 50,
}) => {
  const { conversation, transcriptions, agentState } = useConversation();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && isAtBottom && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [conversation, autoScroll, isAtBottom]);

  // Handle scroll events
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom && conversation.length > 0);
  };

  // Copy entire conversation
  const copyConversation = async () => {
    const conversationText = conversation
      .map((message) => `${message.type.toUpperCase()}: ${message.content}`)
      .join('\n\n');
    
    try {
      await navigator.clipboard.writeText(conversationText);
    } catch (error) {
      console.error('Failed to copy conversation:', error);
    }
  };

  // Scroll to bottom
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  };

  // Get current transcription (latest non-final one)
  const currentTranscription = transcriptions
    .filter((t) => !t.isFinal)
    .pop();

  // Limit conversation messages
  const displayMessages = conversation.slice(-maxMessages);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border glass">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-foreground">
            Conversation
          </h2>
          {conversation.length > 0 && (
            <span className="text-xs text-foreground-muted bg-card px-2 py-1 rounded-full">
              {conversation.length} messages
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={copyConversation}
            disabled={conversation.length === 0}
            className="p-2 text-foreground-muted hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 rounded-lg hover:bg-card-hover"
            title="Copy conversation"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
        style={{ scrollbarWidth: 'thin' }}
      >
        {displayMessages.length === 0 && !currentTranscription ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="w-16 h-16 mb-4 rounded-full bg-gradient-to-r from-accent-purple/20 to-accent-blue/20 flex items-center justify-center">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-accent-purple to-accent-blue" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              Ready to Chat
            </h3>
            <p className="text-sm text-foreground-muted max-w-md">
              Start a conversation by holding the voice button and speaking naturally. 
              I&apos;m here to help with your United Airlines needs.
            </p>
          </motion.div>
        ) : (
          <AnimatePresence mode="popLayout">
            {displayMessages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{
                  duration: 0.3,
                  delay: index * 0.05,
                  type: "spring",
                  stiffness: 300,
                  damping: 25
                }}
              >
                <MessageBubble
                  message={message}
                  showTimestamp={true}
                  enableTypewriter={message.type === 'agent'}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {/* Current Transcription */}
        {showTranscription && currentTranscription && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="sticky bottom-0 z-10"
          >
            <TranscriptionIndicator
              transcription={currentTranscription}
              className="mb-4"
            />
          </motion.div>
        )}
      </div>

      {/* Scroll to Bottom Button */}
      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToBottom}
            className="absolute bottom-20 right-6 p-3 glass rounded-full shadow-lg hover:glow transition-all duration-200 z-10"
          >
            <RotateCcw className="w-4 h-4 text-foreground transform rotate-90" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Agent Status Indicator */}
      {agentState !== 'idle' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 border-t border-border glass"
        >
          <div className="flex items-center gap-2 text-sm text-foreground-muted">
            <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            <span className="capitalize">
              Agent is {agentState.replace('_', ' ')}...
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};