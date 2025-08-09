"""
Mock agent for when API keys are not available
"""

class MockVoiceAgent:
    """Mock voice agent that works without API keys"""
    
    def __init__(self):
        self.whisper_client = None
        self.groq_client = None
        self.tts_service = None
    
    def process_audio(self, audio_data):
        """Return mock response"""
        return "I'm a mock agent. Please configure API keys for full functionality."
    
    def close(self):
        """Cleanup"""
        pass