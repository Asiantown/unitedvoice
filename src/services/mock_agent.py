"""
Mock agent for when API keys are not available
"""

from src.core.booking_flow import BookingFlow


class MockVoiceAgent:
    """Mock voice agent that works without API keys"""
    
    def __init__(self):
        self.whisper_client = None
        self.groq_client = None
        self.tts_service = None
        self.elevenlabs_client = None
        self.booking_flow = BookingFlow()
    
    def process_audio(self, audio_data):
        """Return mock response for audio input"""
        return "I'm currently in demo mode. Please configure API keys for full voice functionality."
    
    def get_response(self, text_input):
        """Return mock response for text input"""
        return "I'm currently in demo mode. Please configure API keys for full conversation functionality."
    
    def transcribe_audio(self, audio_data):
        """Mock transcription"""
        return "Mock transcription: Audio received but API keys are not configured"
    
    def close(self):
        """Cleanup"""
        pass