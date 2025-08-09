#!/usr/bin/env python3
"""
Groq client for fast LLM inference
"""

import os
from typing import List, Dict
import requests
import json


class GroqClient:
    """Client for Groq API - fast LLM inference"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key required")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Available models on Groq (fast inference)
        self.models = {
            "gemma2-9b": "gemma2-9b-it",             # Gemma 2 9B - Tool calling model
            "qwen3-32b": "qwen/qwen3-32b",           # Qwen 3 32B
            "llama3-8b": "llama3-8b-8192",           # Llama 3 8B
            "llama3-70b": "llama3-70b-8192",         # Llama 3 70B
            "mixtral": "mixtral-8x7b-32768",         # Mixtral
            "gemma": "gemma-7b-it",                  # Gemma 7B
        }
        
        # Default to Gemma 2 9B for tool calling
        self.default_model = "gemma2-9b-it"
    
    def chat(self, messages: List[Dict], model: str = None, temperature: float = 0.7) -> Dict:
        """
        Send chat completion request to Groq
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=10  # Add 10 second timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "message": {
                    "content": result["choices"][0]["message"]["content"]
                },
                "usage": result.get("usage", {}),
                "model": model
            }
            
        except Exception as e:
            print(f"Groq API error: {e}")
            # Fallback response
            return {
                "message": {
                    "content": "Sorry, I'm having trouble with that. Could you say it again?"
                }
            }
    
    def test_connection(self):
        """Test Groq API connection"""
        try:
            response = self.chat(
                messages=[{"role": "user", "content": "Say 'Hello from Groq!'"}],
                temperature=0
            )
            return True, response["message"]["content"]
        except Exception as e:
            return False, str(e)


# Test the Groq client
if __name__ == "__main__":
    print("🚀 Testing Groq Client")
    print("="*50)
    
    # Use environment API key
    client = GroqClient()
    
    # Test connection
    success, message = client.test_connection()
    print(f"Connection test: {'✅ Success' if success else '❌ Failed'}")
    print(f"Response: {message}")
    
    # Test speed
    import time
    
    test_prompts = [
        "Hi, I need to book a flight",
        "I want to fly from Boston to Miami next Friday",
        "What's the weather like today?"
    ]
    
    print("\n⚡ Speed Test:")
    for prompt in test_prompts:
        start = time.time()
        response = client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful flight booking assistant. Keep responses concise."},
                {"role": "user", "content": prompt}
            ]
        )
        elapsed = time.time() - start
        
        print(f"\nPrompt: '{prompt}'")
        print(f"Response: {response['message']['content'][:100]}...")
        print(f"Time: {elapsed:.2f}s")
    
    print("\n✅ Groq is typically 10-20x faster than local Ollama!")