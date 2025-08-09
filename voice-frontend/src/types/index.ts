// Core types for the United Voice Agent frontend

export interface VoiceState {
  isListening: boolean;
  isConnected: boolean;
  isMuted: boolean;
  volume: number;
  error: string | null;
}

export interface AudioConfig {
  sampleRate: number;
  bitDepth: number;
  channels: number;
  codec: 'pcm' | 'opus' | 'mp3';
}

export interface WebSocketMessage {
  type: 'audio' | 'text' | 'command' | 'status' | 'error';
  data: unknown;
  timestamp: number;
  id?: string;
}

export interface FlightSearchParams {
  from: string;
  to: string;
  departureDate: string;
  returnDate?: string;
  passengers: number;
  tripType: 'oneway' | 'roundtrip' | 'multicity';
  cabinClass: 'economy' | 'premium' | 'business' | 'first';
}

export interface Flight {
  id: string;
  airline: string;
  flightNumber: string;
  departure: {
    airport: string;
    city: string;
    time: string;
    date: string;
    terminal?: string;
    gate?: string;
  };
  arrival: {
    airport: string;
    city: string;
    time: string;
    date: string;
    terminal?: string;
    gate?: string;
  };
  duration: string;
  stops: number;
  price: {
    amount: number;
    currency: string;
    taxes: number;
    total: number;
  };
  aircraft: string;
  availability: {
    economy: number;
    premium: number;
    business: number;
    first: number;
  };
}

export interface ConversationMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  audioUrl?: string;
  isPlaying?: boolean;
  metadata?: Record<string, unknown>;
}

export interface BookingData {
  flights: Flight[];
  passengers: Passenger[];
  contactInfo: ContactInfo;
  paymentInfo?: PaymentInfo;
  preferences?: BookingPreferences;
  totalPrice: number;
  currency: string;
}

export interface Passenger {
  id: string;
  type: 'adult' | 'child' | 'infant';
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  nationality: string;
  passportNumber?: string;
  passportExpiry?: string;
  knownTravelerNumber?: string;
  redressNumber?: string;
  seatPreference?: string;
  mealPreference?: string;
  specialRequests?: string[];
}

export interface ContactInfo {
  email: string;
  phone: string;
  alternatePhone?: string;
  address?: {
    street: string;
    city: string;
    state: string;
    country: string;
    zipCode: string;
  };
}

export interface PaymentInfo {
  type: 'credit' | 'debit' | 'paypal' | 'miles';
  cardNumber?: string;
  expiryDate?: string;
  cvv?: string;
  cardholderName?: string;
  billingAddress?: ContactInfo['address'];
  milesAccountNumber?: string;
  milesAmount?: number;
}

export interface BookingPreferences {
  seatType: 'window' | 'aisle' | 'middle' | 'any';
  mealPreference: 'standard' | 'vegetarian' | 'vegan' | 'halal' | 'kosher' | 'none';
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  insurance: boolean;
  carRental: boolean;
  hotel: boolean;
}

export interface Theme {
  colors: {
    background: string;
    foreground: string;
    primary: string;
    secondary: string;
    accent: string;
    muted: string;
    border: string;
    error: string;
    warning: string;
    success: string;
  };
  fonts: {
    sans: string;
    mono: string;
  };
  spacing: Record<string, string>;
  borderRadius: Record<string, string>;
}

export interface UIState {
  isLoading: boolean;
  error: string | null;
  success: string | null;
  modal: {
    isOpen: boolean;
    type?: string;
    data?: unknown;
  };
  sidebar: {
    isOpen: boolean;
  };
  theme: 'light' | 'dark' | 'system';
}

export interface WaveformVisualizerProps {
  audioData: Float32Array;
  width: number;
  height: number;
  color: string;
  backgroundColor: string;
  isPlaying: boolean;
  progress: number;
}

export interface AudioVisualizerSettings {
  fftSize: number;
  smoothingTimeConstant: number;
  minDecibels: number;
  maxDecibels: number;
  visualizerType: 'waveform' | 'frequency' | 'circular';
  colorScheme: 'default' | 'purple' | 'blue' | 'green';
}

// API Response types
export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  metadata?: {
    timestamp: number;
    requestId: string;
    version: string;
  };
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: DeepPartial<T[P]>;
};

export type OptionalKeys<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredKeys<T, K extends keyof T> = T & Required<Pick<T, K>>;