'use client';

import dynamic from 'next/dynamic';
import { OrbState } from './VoiceOrb';

interface VoiceOrbProps {
  state?: OrbState
  audioLevel?: number
  size?: 'small' | 'medium' | 'large' | 'xl' | number
  frequency?: number
  isRecording?: boolean
  isConnected?: boolean
  className?: string
}

// Dynamically import VoiceOrb with SSR disabled
const VoiceOrb = dynamic(() => import('./VoiceOrb'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-32 h-32 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full border border-blue-500/30 animate-pulse">
      <div className="w-16 h-16 bg-blue-500/40 rounded-full animate-ping" />
    </div>
  ),
});

export default function VoiceOrbWrapper(props: VoiceOrbProps) {
  return <VoiceOrb {...props} />;
}

// Re-export the type for convenience
export type { OrbState };