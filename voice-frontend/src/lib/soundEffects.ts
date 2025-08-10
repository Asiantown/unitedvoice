// Sound effects for voice interface interactions

export class SoundEffects {
  private static instance: SoundEffects;
  private audioContext: AudioContext | null = null;
  private enabled: boolean = true;

  private constructor() {
    this.initializeAudioContext();
  }

  public static getInstance(): SoundEffects {
    if (!SoundEffects.instance) {
      SoundEffects.instance = new SoundEffects();
    }
    return SoundEffects.instance;
  }

  private initializeAudioContext() {
    try {
      if (typeof window === 'undefined') {
        this.enabled = false;
        return;
      }
      this.audioContext = new (window.AudioContext || (window as unknown as typeof window.AudioContext))();
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Audio context not supported:', error);
      }
      this.enabled = false;
    }
  }

  public setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  private createOscillator(
    frequency: number, 
    type: OscillatorType = 'sine', 
    duration: number = 0.1,
    volume: number = 0.1
  ) {
    if (!this.audioContext || !this.enabled) return;

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = type;
    
    gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(volume, this.audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);

    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration);
  }

  private createChord(frequencies: number[], duration: number = 0.2, volume: number = 0.05) {
    frequencies.forEach(freq => {
      this.createOscillator(freq, 'sine', duration, volume);
    });
  }

  // Recording start sound - ascending chord
  public playRecordingStart() {
    if (!this.enabled) return;
    this.createChord([220, 277.18, 329.63], 0.15, 0.06); // A3, C#4, E4
  }

  // Recording stop sound - descending chord
  public playRecordingStop() {
    if (!this.enabled) return;
    this.createChord([329.63, 277.18, 220], 0.2, 0.06); // E4, C#4, A3
  }

  // Success/connection sound - major chord
  public playSuccess() {
    if (!this.enabled) return;
    this.createChord([261.63, 329.63, 392], 0.3, 0.08); // C4, E4, G4
  }

  // Error sound - dissonant chord
  public playError() {
    if (!this.enabled) return;
    this.createChord([220, 233.08, 246.94], 0.4, 0.08); // A3, A#3, B3
  }

  // Notification/message received sound - bell-like
  public playNotification() {
    if (!this.enabled) return;
    this.createOscillator(523.25, 'sine', 0.1, 0.05); // C5
    setTimeout(() => {
      this.createOscillator(659.25, 'sine', 0.1, 0.04); // E5
    }, 50);
  }

  // Hover sound - subtle click
  public playHover() {
    if (!this.enabled) return;
    this.createOscillator(800, 'square', 0.05, 0.02);
  }

  // Button click sound
  public playClick() {
    if (!this.enabled) return;
    this.createOscillator(1000, 'square', 0.05, 0.03);
  }

  // Typing indicator sound - gentle pulse
  public playTyping() {
    if (!this.enabled) return;
    this.createOscillator(400, 'sine', 0.08, 0.02);
  }

  // Connection established sound - ascending tones
  public playConnectionEstablished() {
    if (!this.enabled) return;
    [293.66, 369.99, 440, 523.25].forEach((freq, index) => {
      setTimeout(() => {
        this.createOscillator(freq, 'sine', 0.1, 0.04);
      }, index * 50);
    });
  }

  // Ambient background sound - very subtle
  public playAmbientTone() {
    if (!this.enabled) return;
    this.createOscillator(55, 'sine', 2, 0.005); // Very low A1
  }
}