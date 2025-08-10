/**
 * Audio processing utilities for the voice frontend
 */

export interface AudioFormat {
  mimeType: string;
  extension: string;
  supported: boolean;
}

export interface AudioProcessingOptions {
  sampleRate?: number;
  channels?: number;
  bitRate?: number;
  format?: string;
  chunkSize?: number;
}

export interface AudioChunk {
  data: string; // base64 encoded
  format: string;
  timestamp: number;
  sequenceNumber: number;
  isLast: boolean;
}

// Supported audio formats in order of preference
export const SUPPORTED_FORMATS: AudioFormat[] = [
  {
    mimeType: 'audio/webm;codecs=opus',
    extension: 'webm',
    supported: false, // Will be set dynamically
  },
  {
    mimeType: 'audio/webm',
    extension: 'webm',
    supported: false,
  },
  {
    mimeType: 'audio/ogg;codecs=opus',
    extension: 'ogg',
    supported: false,
  },
  {
    mimeType: 'audio/mp4',
    extension: 'mp4',
    supported: false,
  },
  {
    mimeType: 'audio/wav',
    extension: 'wav',
    supported: false,
  },
];

// Default audio processing options
export const DEFAULT_AUDIO_OPTIONS: Required<AudioProcessingOptions> = {
  sampleRate: 16000, // 16kHz for speech recognition
  channels: 1, // Mono
  bitRate: 128000, // 128kbps
  format: 'audio/webm;codecs=opus',
  chunkSize: 1024 * 64, // 64KB chunks
};

/**
 * Initialize audio format support detection
 */
export function initializeAudioFormats(): AudioFormat[] {
  const formats = SUPPORTED_FORMATS.map(format => ({
    ...format,
    supported: typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(format.mimeType),
  }));

  if (process.env.NODE_ENV === 'development') {
    console.log('Supported audio formats:', formats.filter(f => f.supported));
  }
  return formats;
}

/**
 * Get the best supported audio format
 */
export function getBestSupportedFormat(): AudioFormat {
  const formats = initializeAudioFormats();
  const supported = formats.find(format => format.supported);
  
  if (!supported) {
    throw new Error('No supported audio format found');
  }
  
  return supported;
}

/**
 * Convert audio blob to base64 string
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onloadend = () => {
      const result = reader.result as string;
      // Remove the data URL prefix (e.g., "data:audio/webm;base64,")
      const base64 = result.split(',')[1];
      if (!base64) {
        reject(new Error('Failed to convert blob to base64'));
        return;
      }
      resolve(base64);
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read blob'));
    };
    
    reader.readAsDataURL(blob);
  });
}

/**
 * Convert base64 string to audio blob
 */
export function base64ToBlob(base64: string, mimeType: string): Blob {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
}

/**
 * Create audio URL from base64 data
 */
export function createAudioUrl(base64: string, mimeType: string): string {
  const blob = base64ToBlob(base64, mimeType);
  return URL.createObjectURL(blob);
}

/**
 * Validate audio format
 */
export function validateAudioFormat(mimeType: string): boolean {
  if (typeof MediaRecorder === 'undefined') {
    return false;
  }
  
  return MediaRecorder.isTypeSupported(mimeType);
}

/**
 * Split audio blob into chunks for streaming
 */
export async function splitAudioIntoChunks(
  blob: Blob,
  options: AudioProcessingOptions = {}
): Promise<AudioChunk[]> {
  const { chunkSize = DEFAULT_AUDIO_OPTIONS.chunkSize, format = blob.type } = options;
  
  const arrayBuffer = await blob.arrayBuffer();
  const totalSize = arrayBuffer.byteLength;
  const chunks: AudioChunk[] = [];
  
  for (let offset = 0; offset < totalSize; offset += chunkSize) {
    const end = Math.min(offset + chunkSize, totalSize);
    const chunkBuffer = arrayBuffer.slice(offset, end);
    const chunkBlob = new Blob([chunkBuffer], { type: format });
    const base64 = await blobToBase64(chunkBlob);
    
    chunks.push({
      data: base64,
      format,
      timestamp: Date.now(),
      sequenceNumber: chunks.length,
      isLast: end >= totalSize,
    });
  }
  
  return chunks;
}

/**
 * Get audio duration from blob
 */
export function getAudioDuration(blob: Blob): Promise<number> {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    const url = URL.createObjectURL(blob);
    
    audio.addEventListener('loadedmetadata', () => {
      URL.revokeObjectURL(url);
      resolve(audio.duration);
    });
    
    audio.addEventListener('error', () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load audio metadata'));
    });
    
    audio.src = url;
  });
}

/**
 * Normalize audio level (0-1 to decibels)
 */
export function levelToDecibels(level: number): number {
  if (level === 0) return -Infinity;
  return 20 * Math.log10(level);
}

/**
 * Decibels to normalized level (0-1)
 */
export function decibelsToLevel(db: number): number {
  if (db === -Infinity) return 0;
  return Math.pow(10, db / 20);
}

/**
 * Calculate RMS (Root Mean Square) from audio data
 */
export function calculateRMS(audioData: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < audioData.length; i++) {
    sum += audioData[i] * audioData[i];
  }
  return Math.sqrt(sum / audioData.length);
}

/**
 * Detect silence in audio data
 */
export function detectSilence(
  audioData: Float32Array,
  threshold: number = 0.01
): boolean {
  const rms = calculateRMS(audioData);
  return rms < threshold;
}

/**
 * Apply audio filters/processing
 */
export class AudioProcessor {
  private audioContext: AudioContext | null = null;
  private gainNode: GainNode | null = null;
  private filterNode: BiquadFilterNode | null = null;

  constructor() {
    this.initialize();
  }

  private initialize() {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('AudioContext not supported:', error);
      }
    }
  }

  /**
   * Create audio processing chain
   */
  createProcessingChain(source: MediaStreamAudioSourceNode) {
    if (!this.audioContext) {
      throw new Error('AudioContext not available');
    }

    // Create gain node for volume control
    this.gainNode = this.audioContext.createGain();
    
    // Create filter node for noise reduction
    this.filterNode = this.audioContext.createBiquadFilter();
    this.filterNode.type = 'highpass';
    this.filterNode.frequency.value = 100; // Remove low-frequency noise
    
    // Connect the chain
    source.connect(this.filterNode);
    this.filterNode.connect(this.gainNode);
    
    return this.gainNode;
  }

  /**
   * Set gain level
   */
  setGain(level: number) {
    if (this.gainNode) {
      this.gainNode.gain.value = level;
    }
  }

  /**
   * Set filter frequency
   */
  setFilterFrequency(frequency: number) {
    if (this.filterNode) {
      this.filterNode.frequency.value = frequency;
    }
  }

  /**
   * Clean up resources
   */
  cleanup() {
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    this.audioContext = null;
    this.gainNode = null;
    this.filterNode = null;
  }
}

/**
 * Audio quality analyzer
 */
export class AudioQualityAnalyzer {
  private analyser: AnalyserNode | null = null;
  private dataArray: Uint8Array | null = null;
  private freqArray: Float32Array | null = null;

  constructor(audioContext: AudioContext, source: AudioNode) {
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    this.analyser.smoothingTimeConstant = 0.8;
    
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.freqArray = new Float32Array(this.analyser.frequencyBinCount);
    
    source.connect(this.analyser);
  }

  /**
   * Get current audio quality metrics
   */
  getQualityMetrics() {
    if (!this.analyser || !this.dataArray || !this.freqArray) {
      return null;
    }

    // @ts-expect-error - ArrayBuffer type compatibility issue
    this.analyser.getByteFrequencyData(this.dataArray);
    // @ts-expect-error - ArrayBuffer type compatibility issue  
    this.analyser.getFloatFrequencyData(this.freqArray);

    // Calculate various quality metrics
    const volume = this.calculateVolume();
    const snr = this.calculateSNR();
    const clarity = this.calculateClarity();
    
    return {
      volume,
      snr,
      clarity,
      quality: this.calculateOverallQuality(volume, snr, clarity),
    };
  }

  private calculateVolume(): number {
    if (!this.dataArray) return 0;
    
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      sum += this.dataArray[i];
    }
    return sum / this.dataArray.length / 255;
  }

  private calculateSNR(): number {
    if (!this.freqArray) return 0;
    
    // Simple SNR estimation based on frequency distribution
    let signal = 0;
    let noise = 0;
    
    // Assume speech is primarily in 300-3400 Hz range
    const speechStart = Math.floor(300 / (44100 / 2) * this.freqArray.length);
    const speechEnd = Math.floor(3400 / (44100 / 2) * this.freqArray.length);
    
    for (let i = 0; i < this.freqArray.length; i++) {
      const power = Math.pow(10, this.freqArray[i] / 10);
      
      if (i >= speechStart && i <= speechEnd) {
        signal += power;
      } else {
        noise += power;
      }
    }
    
    return signal > 0 && noise > 0 ? 10 * Math.log10(signal / noise) : 0;
  }

  private calculateClarity(): number {
    if (!this.freqArray) return 0;
    
    // Measure frequency distribution sharpness
    let peaks = 0;
    let total = 0;
    
    for (let i = 1; i < this.freqArray.length - 1; i++) {
      const current = this.freqArray[i];
      const prev = this.freqArray[i - 1];
      const next = this.freqArray[i + 1];
      
      total++;
      if (current > prev && current > next && current > -60) {
        peaks++;
      }
    }
    
    return total > 0 ? peaks / total : 0;
  }

  private calculateOverallQuality(volume: number, snr: number, clarity: number): number {
    // Weighted combination of quality metrics
    const volumeWeight = 0.3;
    const snrWeight = 0.5;
    const clarityWeight = 0.2;
    
    // Normalize SNR to 0-1 range (assuming reasonable range is -10 to 30 dB)
    const normalizedSNR = Math.max(0, Math.min(1, (snr + 10) / 40));
    
    const quality = (volume * volumeWeight) + 
                   (normalizedSNR * snrWeight) + 
                   (clarity * clarityWeight);
    
    return Math.max(0, Math.min(1, quality));
  }

  cleanup() {
    this.analyser = null;
    this.dataArray = null;
    this.freqArray = null;
  }
}

/**
 * Utility function to create audio player from base64
 */
export function createAudioPlayer(base64: string, mimeType: string): HTMLAudioElement {
  const audio = new Audio();
  audio.src = createAudioUrl(base64, mimeType);
  return audio;
}

/**
 * Preload audio for faster playback
 */
export function preloadAudio(base64: string, mimeType: string): Promise<HTMLAudioElement> {
  return new Promise((resolve, reject) => {
    const audio = createAudioPlayer(base64, mimeType);
    
    audio.addEventListener('canplaythrough', () => {
      resolve(audio);
    });
    
    audio.addEventListener('error', () => {
      reject(new Error('Failed to preload audio'));
    });
    
    audio.preload = 'auto';
  });
}