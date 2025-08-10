'use client'

import { useRef, useEffect, useState, useCallback } from 'react'

export interface AudioVisualizerData {
  audioLevel: number
  frequency: number
  volume: number
  isActive: boolean
  frequencyData: Uint8Array | null
}

export interface UseAudioVisualizerOptions {
  fftSize?: number
  smoothingTimeConstant?: number
  minDecibels?: number
  maxDecibels?: number
  updateInterval?: number
}

export function useAudioVisualizer(
  audioElement?: HTMLAudioElement | null,
  options: UseAudioVisualizerOptions = {}
) {
  const {
    fftSize = 256,
    smoothingTimeConstant = 0.8,
    minDecibels = -90,
    maxDecibels = -10,
    updateInterval = 16 // ~60fps
  } = options
  
  const [visualizerData, setVisualizerData] = useState<AudioVisualizerData>({
    audioLevel: 0,
    frequency: 0,
    volume: 0,
    isActive: false,
    frequencyData: null
  })
  
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  
  const initializeAudioContext = useCallback(async () => {
    if (!audioElement || audioContextRef.current) return
    
    try {
      // Create audio context
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      const audioContext = new AudioContextClass()
      
      // Create analyser
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = fftSize
      analyser.smoothingTimeConstant = smoothingTimeConstant
      analyser.minDecibels = minDecibels
      analyser.maxDecibels = maxDecibels
      
      // Create source and connect
      const source = audioContext.createMediaElementSource(audioElement)
      source.connect(analyser)
      analyser.connect(audioContext.destination)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      sourceRef.current = source
      
      // Resume context if suspended (required by some browsers)
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }
      
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to initialize audio context:', error)
      }
    }
  }, [audioElement, fftSize, smoothingTimeConstant, minDecibels, maxDecibels])
  
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return
    
    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    
    // Get frequency data
    analyserRef.current.getByteFrequencyData(dataArray)
    
    // Calculate audio level (0-1)
    let sum = 0
    let maxVal = 0
    for (let i = 0; i < bufferLength; i++) {
      const value = dataArray[i]
      sum += value
      maxVal = Math.max(maxVal, value)
    }
    
    const average = sum / bufferLength
    const audioLevel = Math.min(average / 128, 1) // Normalize to 0-1
    const volume = Math.min(maxVal / 255, 1)
    
    // Calculate dominant frequency
    let maxFreqIndex = 0
    let maxFreqValue = 0
    for (let i = 1; i < bufferLength / 2; i++) {
      if (dataArray[i] > maxFreqValue) {
        maxFreqValue = dataArray[i]
        maxFreqIndex = i
      }
    }
    
    const frequency = (maxFreqIndex * (audioContextRef.current?.sampleRate || 44100)) / (2 * bufferLength)
    
    setVisualizerData({
      audioLevel,
      frequency,
      volume,
      isActive: audioLevel > 0.01,
      frequencyData: dataArray
    })
  }, [])
  
  const startAnalysis = useCallback(() => {
    if (intervalRef.current) return
    
    intervalRef.current = setInterval(analyzeAudio, updateInterval)
  }, [analyzeAudio, updateInterval])
  
  const stopAnalysis = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    setVisualizerData({
      audioLevel: 0,
      frequency: 0,
      volume: 0,
      isActive: false,
      frequencyData: null
    })
  }, [])
  
  // Initialize when audio element is available
  useEffect(() => {
    if (audioElement) {
      initializeAudioContext()
      
      const handlePlay = () => startAnalysis()
      const handlePause = () => stopAnalysis()
      const handleEnded = () => stopAnalysis()
      
      audioElement.addEventListener('play', handlePlay)
      audioElement.addEventListener('pause', handlePause)
      audioElement.addEventListener('ended', handleEnded)
      
      return () => {
        audioElement.removeEventListener('play', handlePlay)
        audioElement.removeEventListener('pause', handlePause)
        audioElement.removeEventListener('ended', handleEnded)
      }
    }
  }, [audioElement, initializeAudioContext, startAnalysis, stopAnalysis])
  
  // Cleanup
  useEffect(() => {
    return () => {
      stopAnalysis()
      
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
      
      audioContextRef.current = null
      analyserRef.current = null
      sourceRef.current = null
    }
  }, [stopAnalysis])
  
  return visualizerData
}

// Hook for microphone input
export function useMicrophoneVisualizer(options: UseAudioVisualizerOptions = {}) {
  const {
    fftSize = 256,
    smoothingTimeConstant = 0.8,
    minDecibels = -90,
    maxDecibels = -10,
    updateInterval = 16
  } = options
  
  const [visualizerData, setVisualizerData] = useState<AudioVisualizerData>({
    audioLevel: 0,
    frequency: 0,
    volume: 0,
    isActive: false,
    frequencyData: null
  })
  
  const [isListening, setIsListening] = useState(false)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  
  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      const audioContext = new AudioContextClass()
      
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = fftSize
      analyser.smoothingTimeConstant = smoothingTimeConstant
      analyser.minDecibels = minDecibels
      analyser.maxDecibels = maxDecibels
      
      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      streamRef.current = stream
      
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }
      
      setIsListening(true)
      
      // Start analysis
      intervalRef.current = setInterval(() => {
        if (!analyserRef.current) return
        
        const bufferLength = analyserRef.current.frequencyBinCount
        const dataArray = new Uint8Array(bufferLength)
        analyserRef.current.getByteFrequencyData(dataArray)
        
        let sum = 0
        let maxVal = 0
        for (let i = 0; i < bufferLength; i++) {
          const value = dataArray[i]
          sum += value
          maxVal = Math.max(maxVal, value)
        }
        
        const average = sum / bufferLength
        const audioLevel = Math.min(average / 128, 1)
        const volume = Math.min(maxVal / 255, 1)
        
        // Calculate dominant frequency
        let maxFreqIndex = 0
        let maxFreqValue = 0
        for (let i = 1; i < bufferLength / 2; i++) {
          if (dataArray[i] > maxFreqValue) {
            maxFreqValue = dataArray[i]
            maxFreqIndex = i
          }
        }
        
        const frequency = (maxFreqIndex * (audioContextRef.current?.sampleRate || 44100)) / (2 * bufferLength)
        
        setVisualizerData({
          audioLevel,
          frequency,
          volume,
          isActive: audioLevel > 0.01,
          frequencyData: dataArray
        })
      }, updateInterval)
      
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to start microphone:', error)
      }
    }
  }, [fftSize, smoothingTimeConstant, minDecibels, maxDecibels, updateInterval])
  
  const stopListening = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
    }
    
    audioContextRef.current = null
    analyserRef.current = null
    setIsListening(false)
    
    setVisualizerData({
      audioLevel: 0,
      frequency: 0,
      volume: 0,
      isActive: false,
      frequencyData: null
    })
  }, [])
  
  useEffect(() => {
    return () => {
      stopListening()
    }
  }, [stopListening])
  
  return {
    ...visualizerData,
    isListening,
    startListening,
    stopListening
  }
}