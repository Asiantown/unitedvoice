'use client';

import React, { useEffect, useRef, useState, useCallback, memo } from 'react';
import { MessageBubble } from './MessageBubble';
import { TranscriptionIndicator } from './TranscriptionIndicator';
import { useConversation } from '@/store/voiceStore';
import { AnimatePresence, motion } from 'framer-motion';
import { Copy, RotateCcw } from 'lucide-react';

/**
 * Props for the ConversationPanel component
 */
export interface ConversationPanelProps {
  /** Optional CSS class name */
  className?: string;
  /** Whether to show real-time transcription */
  showTranscription?: boolean;
  /** Whether to auto-scroll to new messages */
  autoScroll?: boolean;
  /** Maximum number of messages to display */
  maxMessages?: number;
}

/**
 * Conversation panel component that displays chat messages and real-time transcription
 * Supports auto-scrolling, message copying, and transcription display
 */
export const ConversationPanel: React.FC<ConversationPanelProps> = memo(({
  className = '',
  showTranscription = true,
  autoScroll = true,
  maxMessages = 50,
}) => {
  // Store selectors
  const { conversation, transcriptions, agentState } = useConversation();
  
  // Component refs and state
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState<boolean>(true);
  const [showScrollButton, setShowScrollButton] = useState<boolean>(false);

  /**
   * Scrolls to the bottom of the conversation
   */
  const scrollToBottom = useCallback((): void => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, []);

  /**
   * Handles scroll events to update bottom detection and scroll button visibility
   */
  const handleScroll = useCallback((): void => {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom && conversation.length > 0);
  }, [conversation.length]);

  /**
   * Copies the entire conversation to clipboard
   */
  const copyConversation = useCallback(async (): Promise<void> => {
    if (conversation.length === 0) return;

    const conversationText = conversation
      .map((message) => `${message.type.toUpperCase()}: ${message.content}`)
      .join('\n\n');
    
    try {
      await navigator.clipboard.writeText(conversationText);
      // Could show a toast notification here
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to copy conversation:', error);
      }
      // Could show an error toast here
    }
  }, [conversation]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && isAtBottom) {
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        scrollToBottom();
      }, 0);
    }
  }, [conversation, autoScroll, isAtBottom, scrollToBottom]);

  // Get current transcription (latest non-final one)
  const currentTranscription = transcriptions
    .filter((t) => !t.isFinal)
    .pop();

  // Limit conversation messages to prevent performance issues
  const displayMessages = conversation.slice(-maxMessages);

  return (
    <section className={`flex flex-col h-full ${className}`} role="log" aria-label="Conversation history">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-border glass">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-foreground">
            Conversation
          </h2>
          {conversation.length > 0 && (
            <span 
              className="text-xs text-foreground-muted bg-card px-2 py-1 rounded-full"
              aria-label={`${conversation.length} messages in conversation`}
            >
              {conversation.length} messages
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={copyConversation}
            disabled={conversation.length === 0}
            className="p-2 text-foreground-muted hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 rounded-lg hover:bg-card-hover focus:outline-none focus:ring-2 focus:ring-blue-300"
            aria-label="Copy conversation to clipboard"
            title="Copy conversation"
          >
            <Copy className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Messages Container */}
      <main
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
        style={{ scrollbarWidth: 'thin' }}
        aria-live="polite"
        aria-label="Conversation messages"
        tabIndex={0}
        role="main"
      >
        {displayMessages.length === 0 && !currentTranscription ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
            role="status"
          >
            <div className="w-16 h-16 mb-4 rounded-full bg-gradient-to-r from-accent-purple/20 to-accent-blue/20 flex items-center justify-center" aria-hidden="true">
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
            role="status"
            aria-live="polite"
            aria-label="Live transcription"
          >
            <TranscriptionIndicator
              transcription={currentTranscription}
              className="mb-4"
            />
          </motion.div>
        )}
      </main>

      {/* Scroll to Bottom Button */}
      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToBottom}
            className="absolute bottom-20 right-6 p-3 glass rounded-full shadow-lg hover:glow transition-all duration-200 z-10 focus:outline-none focus:ring-2 focus:ring-blue-300"
            aria-label="Scroll to bottom of conversation"
            title="Scroll to bottom"
          >
            <RotateCcw className="w-4 h-4 text-foreground transform rotate-90" aria-hidden="true" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Agent Status Indicator */}
      {agentState !== 'idle' && (
        <motion.footer
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 border-t border-border glass"
          role="status"
          aria-live="polite"
          aria-label={`Agent status: ${agentState.replace('_', ' ')}`}
        >
          <div className="flex items-center gap-2 text-sm text-foreground-muted">
            <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" aria-hidden="true" />
            <span className="capitalize">
              Agent is {agentState.replace('_', ' ')}...
            </span>
          </div>
        </motion.footer>
      )}
    </section>
  );
});