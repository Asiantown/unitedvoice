'use client'

import { useState, useEffect } from 'react'
import OrbScene from './OrbScene'
import { type OrbState } from './VoiceOrb'
import { useMicrophoneVisualizer } from '../hooks/useAudioVisualizer'

interface VoiceOrbDemoProps {
  className?: string
}

export default function VoiceOrbDemo({ className = '' }: VoiceOrbDemoProps) {
  const [orbState, setOrbState] = useState<OrbState>('idle')
  const [simulatedAudio, setSimulatedAudio] = useState(0)
  const [simulatedFreq, setSimulatedFreq] = useState(0)
  const [useRealAudio, setUseRealAudio] = useState(false)
  
  // Real microphone audio
  const { 
    audioLevel: realAudioLevel, 
    frequency: realFrequency,
    isListening,
    startListening,
    stopListening
  } = useMicrophoneVisualizer()
  
  // Simulate audio when not using real microphone
  useEffect(() => {
    if (!useRealAudio) {
      const interval = setInterval(() => {
        const time = Date.now() * 0.001
        
        // Simulate different audio patterns based on state
        switch (orbState) {
          case 'idle':
            setSimulatedAudio(Math.sin(time * 2) * 0.1 + 0.05)
            setSimulatedFreq(200 + Math.sin(time) * 50)
            break
          case 'listening':
            setSimulatedAudio(Math.sin(time * 4) * 0.3 + 0.2)
            setSimulatedFreq(400 + Math.sin(time * 2) * 100)
            break
          case 'speaking':
            setSimulatedAudio(Math.sin(time * 8) * 0.8 + Math.random() * 0.4)
            setSimulatedFreq(800 + Math.sin(time * 3) * 300)
            break
          case 'thinking':
            setSimulatedAudio(Math.sin(time * 1.5) * 0.2 + 0.1)
            setSimulatedFreq(300 + Math.sin(time * 0.5) * 150)
            break
        }
      }, 50)
      
      return () => clearInterval(interval)
    }
  }, [orbState, useRealAudio])
  
  const currentAudioLevel = useRealAudio ? realAudioLevel : simulatedAudio
  const currentFrequency = useRealAudio ? realFrequency : simulatedFreq
  
  const handleMicrophoneToggle = async () => {
    if (useRealAudio) {
      stopListening()
      setUseRealAudio(false)
    } else {
      try {
        await startListening()
        setUseRealAudio(true)
      } catch (error) {
        console.error('Failed to start microphone:', error)
      }
    }
  }
  
  return (
    <div className={`relative ${className}`}>
      {/* 3D Scene */}
      <OrbScene
        orbState={orbState}
        audioLevel={currentAudioLevel}
        frequency={currentFrequency}
        className="w-full h-full"
      />
      
      {/* Controls Overlay */}
      <div className="absolute top-4 left-4 z-10 space-y-3">
        <div className="bg-black/20 backdrop-blur-sm rounded-lg p-4 text-white">
          <h3 className="text-sm font-semibold mb-3">Voice Orb Controls</h3>
          
          {/* State Controls */}
          <div className="space-y-2 mb-4">
            <div className="text-xs text-gray-300">State:</div>
            <div className="flex gap-2 flex-wrap">
              {(['idle', 'listening', 'speaking', 'thinking'] as OrbState[]).map((state) => (
                <button
                  key={state}
                  onClick={() => setOrbState(state)}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    orbState === state
                      ? 'bg-blue-500 text-white'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  {state}
                </button>
              ))}
            </div>
          </div>
          
          {/* Audio Controls */}
          <div className="space-y-2">
            <div className="text-xs text-gray-300">Audio Input:</div>
            <button
              onClick={handleMicrophoneToggle}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                useRealAudio && isListening
                  ? 'bg-red-500 text-white'
                  : 'bg-green-500/20 text-green-300 hover:bg-green-500/30'
              }`}
            >
              {useRealAudio && isListening ? 'Stop Microphone' : 'Use Microphone'}
            </button>
          </div>
        </div>
        
        {/* Audio Level Display */}
        <div className="bg-black/20 backdrop-blur-sm rounded-lg p-4 text-white">
          <div className="text-xs text-gray-300 mb-2">Audio Levels:</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs w-12">Level:</span>
              <div className="flex-1 h-2 bg-gray-600 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-pink-500 transition-all duration-100"
                  style={{ width: `${Math.min(currentAudioLevel * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs w-8">{Math.round(currentAudioLevel * 100)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs w-12">Freq:</span>
              <span className="text-xs">{Math.round(currentFrequency)}Hz</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Info Overlay */}
      <div className="absolute bottom-4 right-4 z-10">
        <div className="bg-black/20 backdrop-blur-sm rounded-lg p-3 text-white text-xs max-w-xs">
          <p className="text-gray-300">
            Premium 3D voice orb with holographic materials, audio-reactive animations, 
            and particle effects. Built with Three.js and React Three Fiber.
          </p>
        </div>
      </div>
    </div>
  )
}