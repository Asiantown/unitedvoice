import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Types for the voice store
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export type RecordingState = 'idle' | 'recording' | 'processing' | 'uploading';

export interface TranscriptionEntry {
  id: string;
  text: string;
  isFinal: boolean;
  confidence?: number;
  timestamp: number;
}

export interface AgentResponse {
  id: string;
  text: string;
  audioUrl?: string;
  metadata?: Record<string, unknown>;
  timestamp: number;
  isPlaying?: boolean;
}

export interface AudioQueueItem {
  id: string;
  audioData: string;
  format: string;
  metadata?: Record<string, unknown>;
  timestamp: number;
  played?: boolean;
}

export interface ConversationEntry {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: number;
  audioUrl?: string;
  metadata?: Record<string, unknown>;
}

export interface VoiceStoreState {
  // Connection state
  connectionState: ConnectionState;
  error: string | null;
  lastConnectedAt: number | null;

  // Recording state
  recordingState: RecordingState;
  isHoldingToTalk: boolean;
  recordingStartTime: number | null;
  recordingDuration: number;

  // Audio state
  currentAudioLevel: number;
  audioQueue: AudioQueueItem[];
  currentlyPlaying: string | null;

  // Conversation state
  transcriptions: TranscriptionEntry[];
  agentResponses: AgentResponse[];
  conversation: ConversationEntry[];
  agentState: string;
  agentStateMetadata: Record<string, unknown> | null;

  // UI state
  isRecordingIndicatorVisible: boolean;
  waveformData: Float32Array | null;
  
  // Actions
  setConnectionState: (state: ConnectionState) => void;
  setError: (error: string | null) => void;
  setRecordingState: (state: RecordingState) => void;
  setHoldingToTalk: (holding: boolean) => void;
  setRecordingStartTime: (time: number | null) => void;
  updateRecordingDuration: (duration: number) => void;
  setCurrentAudioLevel: (level: number) => void;
  setWaveformData: (data: Float32Array | null) => void;
  
  // Transcription actions
  addTranscription: (transcription: Omit<TranscriptionEntry, 'id'>) => void;
  clearTranscriptions: () => void;
  updateTranscription: (id: string, updates: Partial<TranscriptionEntry>) => void;
  
  // Agent response actions
  addAgentResponse: (response: Omit<AgentResponse, 'id'>) => void;
  clearAgentResponses: () => void;
  setResponsePlaying: (id: string, playing: boolean) => void;
  
  // Audio queue actions
  addAudioToQueue: (audio: Omit<AudioQueueItem, 'id'>) => void;
  removeFromQueue: (id: string) => void;
  clearAudioQueue: () => void;
  setCurrentlyPlaying: (id: string | null) => void;
  
  // Conversation actions
  addToConversation: (entry: Omit<ConversationEntry, 'id'>) => void;
  clearConversation: () => void;
  
  // Agent state actions
  setAgentState: (state: string, metadata?: Record<string, unknown>) => void;
  
  // Utility actions
  reset: () => void;
}

const initialState = {
  // Connection state
  connectionState: 'disconnected' as ConnectionState,
  error: null,
  lastConnectedAt: null,

  // Recording state
  recordingState: 'idle' as RecordingState,
  isHoldingToTalk: false,
  recordingStartTime: null,
  recordingDuration: 0,

  // Audio state
  currentAudioLevel: 0,
  audioQueue: [],
  currentlyPlaying: null,

  // Conversation state
  transcriptions: [],
  agentResponses: [],
  conversation: [],
  agentState: 'idle',
  agentStateMetadata: null,

  // UI state
  isRecordingIndicatorVisible: false,
  waveformData: null,
};

export const useVoiceStore = create<VoiceStoreState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // Connection actions
      setConnectionState: (state: ConnectionState) => {
        set((prev) => ({
          connectionState: state,
          lastConnectedAt: state === 'connected' ? Date.now() : prev.lastConnectedAt,
          error: state === 'connected' ? null : prev.error,
        }), false, 'setConnectionState');
      },

      setError: (error: string | null) => {
        set({ error }, false, 'setError');
      },

      // Recording actions
      setRecordingState: (state: RecordingState) => {
        set((prev) => ({
          recordingState: state,
          isRecordingIndicatorVisible: state === 'recording',
          recordingStartTime: state === 'recording' && !prev.recordingStartTime ? Date.now() : prev.recordingStartTime,
          recordingDuration: state === 'idle' ? 0 : prev.recordingDuration,
        }), false, 'setRecordingState');
      },

      setHoldingToTalk: (holding: boolean) => {
        set({ isHoldingToTalk: holding }, false, 'setHoldingToTalk');
      },

      setRecordingStartTime: (time: number | null) => {
        set({ recordingStartTime: time }, false, 'setRecordingStartTime');
      },

      updateRecordingDuration: (duration: number) => {
        set({ recordingDuration: duration }, false, 'updateRecordingDuration');
      },

      setCurrentAudioLevel: (level: number) => {
        set({ currentAudioLevel: level }, false, 'setCurrentAudioLevel');
      },

      setWaveformData: (data: Float32Array | null) => {
        set({ waveformData: data }, false, 'setWaveformData');
      },

      // Transcription actions
      addTranscription: (transcription: Omit<TranscriptionEntry, 'id'>) => {
        const id = `transcription-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const entry: TranscriptionEntry = { ...transcription, id };
        
        set((state) => ({
          transcriptions: [...state.transcriptions, entry],
        }), false, 'addTranscription');

        // Also add to conversation if it's final
        if (transcription.isFinal && transcription.text.trim()) {
          get().addToConversation({
            type: 'user',
            content: transcription.text,
            timestamp: transcription.timestamp,
          });
        }
      },

      clearTranscriptions: () => {
        set({ transcriptions: [] }, false, 'clearTranscriptions');
      },

      updateTranscription: (id: string, updates: Partial<TranscriptionEntry>) => {
        set((state) => ({
          transcriptions: state.transcriptions.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
        }), false, 'updateTranscription');
      },

      // Agent response actions
      addAgentResponse: (response: Omit<AgentResponse, 'id'>) => {
        const id = `response-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const entry: AgentResponse = { ...response, id };
        
        set((state) => ({
          agentResponses: [...state.agentResponses, entry],
        }), false, 'addAgentResponse');

        // Also add to conversation
        get().addToConversation({
          type: 'agent',
          content: response.text,
          timestamp: response.timestamp,
          audioUrl: response.audioUrl,
          metadata: response.metadata,
        });
      },

      clearAgentResponses: () => {
        set({ agentResponses: [] }, false, 'clearAgentResponses');
      },

      setResponsePlaying: (id: string, playing: boolean) => {
        set((state) => ({
          agentResponses: state.agentResponses.map((r) =>
            r.id === id ? { ...r, isPlaying: playing } : r
          ),
          currentlyPlaying: playing ? id : null,
        }), false, 'setResponsePlaying');
      },

      // Audio queue actions
      addAudioToQueue: (audio: Omit<AudioQueueItem, 'id'>) => {
        const id = `audio-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const item: AudioQueueItem = { ...audio, id };
        
        set((state) => ({
          audioQueue: [...state.audioQueue, item],
        }), false, 'addAudioToQueue');
      },

      removeFromQueue: (id: string) => {
        set((state) => ({
          audioQueue: state.audioQueue.filter((item) => item.id !== id),
        }), false, 'removeFromQueue');
      },

      clearAudioQueue: () => {
        set({ audioQueue: [] }, false, 'clearAudioQueue');
      },

      setCurrentlyPlaying: (id: string | null) => {
        set({ currentlyPlaying: id }, false, 'setCurrentlyPlaying');
      },

      // Conversation actions
      addToConversation: (entry: Omit<ConversationEntry, 'id'>) => {
        const id = `conversation-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const conversationEntry: ConversationEntry = { ...entry, id };
        
        set((state) => ({
          conversation: [...state.conversation, conversationEntry],
        }), false, 'addToConversation');
      },

      clearConversation: () => {
        set({ conversation: [] }, false, 'clearConversation');
      },

      // Agent state actions
      setAgentState: (state: string, metadata?: Record<string, unknown>) => {
        set({
          agentState: state,
          agentStateMetadata: metadata,
        }, false, 'setAgentState');
      },

      // Utility actions
      reset: () => {
        set(initialState, false, 'reset');
      },
    })),
    {
      name: 'voice-store',
      partialize: (state: any) => ({
        // Only persist certain parts of the state
        conversation: state.conversation,
        agentState: state.agentState,
      }),
    }
  )
);

// Selectors for common state combinations
export const useConnectionStatus = () => useVoiceStore((state) => ({
  connectionState: state.connectionState,
  error: state.error,
  lastConnectedAt: state.lastConnectedAt,
}));

export const useRecordingStatus = () => useVoiceStore((state) => ({
  recordingState: state.recordingState,
  isHoldingToTalk: state.isHoldingToTalk,
  recordingDuration: state.recordingDuration,
  recordingStartTime: state.recordingStartTime,
}));

export const useAudioVisualization = () => useVoiceStore((state) => ({
  currentAudioLevel: state.currentAudioLevel,
  waveformData: state.waveformData,
  isRecordingIndicatorVisible: state.isRecordingIndicatorVisible,
}));

export const useConversation = () => useVoiceStore((state) => ({
  conversation: state.conversation,
  transcriptions: state.transcriptions,
  agentResponses: state.agentResponses,
  agentState: state.agentState,
}));