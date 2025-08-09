/**
 * Audio Player Service for Voice Agent
 * Handles playback of audio responses with visualization
 */

export interface AudioPlayerOptions {
  volume?: number;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: Error) => void;
  visualize?: boolean;
}

export class AudioPlayerService {
  private audioContext: AudioContext | null = null;
  private currentAudio: HTMLAudioElement | null = null;
  private analyser: AnalyserNode | null = null;
  private visualizationCallbacks: ((data: Uint8Array) => void)[] = [];
  private isPlaying = false;

  constructor() {
    // Initialize Web Audio API if available
    if (typeof window !== 'undefined') {
      try {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      } catch (error) {
        console.warn('Web Audio API not available:', error);
      }
    }
  }

  /**
   * Play audio from base64 data
   */
  async playAudio(
    audioData: string, 
    format: string = 'mp3', 
    options: AudioPlayerOptions = {}
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Stop any currently playing audio
        this.stopAudio();

        // Create audio element
        const audio = new Audio();
        const dataUrl = `data:audio/${format};base64,${audioData}`;
        
        audio.src = dataUrl;
        audio.volume = options.volume ?? 0.8;
        
        // Set up event listeners
        audio.onloadstart = () => {
          console.log('Audio loading started');
        };

        audio.oncanplay = () => {
          console.log('Audio can start playing');
        };

        audio.onplay = () => {
          this.isPlaying = true;
          options.onStart?.();
          console.log('Audio playback started');
        };

        audio.onended = () => {
          this.isPlaying = false;
          this.currentAudio = null;
          options.onEnd?.();
          console.log('Audio playback ended');
          resolve();
        };

        audio.onerror = (error) => {
          this.isPlaying = false;
          this.currentAudio = null;
          const audioError = new Error(`Audio playback failed: ${audio.error?.message || 'Unknown error'}`);
          options.onError?.(audioError);
          console.error('Audio playback error:', error);
          reject(audioError);
        };

        audio.onpause = () => {
          this.isPlaying = false;
          console.log('Audio playback paused');
        };

        // Set up visualization if requested and Web Audio API is available
        if (options.visualize && this.audioContext && this.audioContext.state !== 'closed') {
          this.setupVisualization(audio);
        }

        this.currentAudio = audio;
        
        // Start playback
        audio.play().catch(error => {
          console.error('Failed to start audio playback:', error);
          reject(error);
        });

      } catch (error) {
        console.error('Error setting up audio playback:', error);
        reject(error);
      }
    });
  }

  /**
   * Stop currently playing audio
   */
  stopAudio(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.isPlaying = false;
  }

  /**
   * Check if audio is currently playing
   */
  getIsPlaying(): boolean {
    return this.isPlaying;
  }

  /**
   * Set up audio visualization
   */
  private setupVisualization(audio: HTMLAudioElement): void {
    if (!this.audioContext) return;

    try {
      // Resume audio context if suspended
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      // Create audio source and analyser
      const source = this.audioContext.createMediaElementSource(audio);
      this.analyser = this.audioContext.createAnalyser();
      
      // Configure analyser
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;
      
      // Connect audio graph
      source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
      
      // Start visualization loop
      this.visualizationLoop();

    } catch (error) {
      console.warn('Failed to set up audio visualization:', error);
    }
  }

  /**
   * Visualization loop
   */
  private visualizationLoop(): void {
    if (!this.analyser || !this.isPlaying) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const updateVisualization = () => {
      if (!this.analyser || !this.isPlaying) return;
      
      this.analyser.getByteFrequencyData(dataArray);
      
      // Notify all visualization callbacks
      this.visualizationCallbacks.forEach(callback => {
        try {
          callback(dataArray);
        } catch (error) {
          console.warn('Visualization callback error:', error);
        }
      });
      
      requestAnimationFrame(updateVisualization);
    };

    updateVisualization();
  }

  /**
   * Add visualization callback
   */
  onVisualizationData(callback: (data: Uint8Array) => void): () => void {
    this.visualizationCallbacks.push(callback);
    
    // Return cleanup function
    return () => {
      const index = this.visualizationCallbacks.indexOf(callback);
      if (index > -1) {
        this.visualizationCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get audio context state
   */
  getAudioContextState(): string {
    return this.audioContext?.state || 'not-available';
  }

  /**
   * Resume audio context (required after user interaction)
   */
  async resumeAudioContext(): Promise<void> {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      try {
        await this.audioContext.resume();
        console.log('Audio context resumed');
      } catch (error) {
        console.warn('Failed to resume audio context:', error);
      }
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.stopAudio();
    this.visualizationCallbacks = [];
    
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
  }
}

// Global audio player instance
let globalAudioPlayer: AudioPlayerService | null = null;

export function getAudioPlayer(): AudioPlayerService {
  if (!globalAudioPlayer) {
    globalAudioPlayer = new AudioPlayerService();
  }
  return globalAudioPlayer;
}

export function cleanupAudioPlayer(): void {
  if (globalAudioPlayer) {
    globalAudioPlayer.cleanup();
    globalAudioPlayer = null;
  }
}