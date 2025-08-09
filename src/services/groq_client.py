#!/usr/bin/env python3
"""
Groq API Client for Fast LLM Inference

This module provides a client for accessing Groq's fast language model inference API.
Groq specializes in accelerated inference for large language models.

Author: United Airlines Voice Agent Team
Version: 2.0.0
Python Version: 3.8+
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Union

try:
    import requests
except ImportError:
    raise ImportError(
        "requests package is required for GroqClient. Install with: pip install requests"
    )

# Configure module logger
logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for Groq API providing fast LLM inference.
    
    This client handles communication with Groq's API for language model
    inference with optimized speed and reliability.
    
    Attributes:
        api_key: Authentication key for Groq API
        base_url: Base URL for Groq API endpoints
        headers: HTTP headers for API requests
        models: Available model configurations
        default_model: Default model identifier
        
    Raises:
        ValueError: If API key is not provided
        requests.HTTPError: If API requests fail
    """
    
    # API Configuration
    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_TOKENS = 1024
    
    # Available Groq models with their capabilities
    AVAILABLE_MODELS = {
        "gemma2-9b": {
            "id": "gemma2-9b-it",
            "description": "Gemma 2 9B - Optimized for tool calling",
            "max_tokens": 8192
        },
        "llama3-8b": {
            "id": "llama3-8b-8192", 
            "description": "Llama 3 8B - Fast general purpose",
            "max_tokens": 8192
        },
        "llama3-70b": {
            "id": "llama3-70b-8192",
            "description": "Llama 3 70B - High quality responses", 
            "max_tokens": 8192
        },
        "mixtral": {
            "id": "mixtral-8x7b-32768",
            "description": "Mixtral 8x7B - Mixture of experts",
            "max_tokens": 32768
        }
    }
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the Groq client.
        
        Args:
            api_key: Groq API key. If None, reads from GROQ_API_KEY environment variable
            
        Raises:
            ValueError: If no API key is provided or found
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Provide via api_key parameter or GROQ_API_KEY environment variable."
            )
        
        self.base_url = self.BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "UnitedVoiceAgent/2.0.0"
        }
        
        # Use Gemma 2 9B as default for tool calling capabilities
        self.default_model = "gemma2-9b-it"
        
        logger.info(f"Groq client initialized with default model: {self.default_model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Union[Dict, str]]:
        """
        Send a chat completion request to Groq API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model identifier to use (defaults to configured default)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary containing response message, usage stats, and model info
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If input parameters are invalid
        """
        # Validate inputs
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        if not all(isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in messages):
            raise ValueError("Each message must be a dict with 'role' and 'content' keys")
        
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        # Set defaults
        model = model or self.default_model
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        start_time = time.time()
        
        try:
            logger.debug(f"Sending chat completion request to Groq (model: {model})")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            elapsed_time = time.time() - start_time
            
            logger.debug(f"Chat completion successful in {elapsed_time:.2f}s")
            
            # Extract response data
            choice = result["choices"][0]
            message_content = choice["message"]["content"]
            
            return {
                "message": {
                    "content": message_content
                },
                "usage": result.get("usage", {}),
                "model": model,
                "response_time": elapsed_time
            }
            
        except requests.Timeout:
            logger.error(f"Groq API request timed out after {timeout} seconds")
            raise
        except requests.HTTPError as e:
            logger.error(f"Groq API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Groq API response format: {e}")
            raise ValueError(f"Invalid API response format: {e}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to Groq API.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("Testing Groq API connection")
            
            response = self.chat(
                messages=[{"role": "user", "content": "Say 'Hello from Groq!'"}],
                temperature=0.0,
                timeout=10
            )
            
            success_msg = response["message"]["content"]
            logger.info("Groq API connection test successful")
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Union[str, int]]]:
        """
        Get information about a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model information dictionary or None if not found
        """
        for model_key, model_data in self.AVAILABLE_MODELS.items():
            if model_data["id"] == model_id or model_key == model_id:
                return model_data
        return None
    
    def list_available_models(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Get list of available models and their capabilities.
        
        Returns:
            Dictionary mapping model keys to model information
        """
        return self.AVAILABLE_MODELS.copy()
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count for text.
        
        Args:
            text: Input text to estimate
            
        Returns:
            Estimated token count
            
        Note:
            This is a rough approximation. Actual tokenization may vary.
        """
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)


def main() -> None:
    """
    Test the Groq client functionality.
    
    This function demonstrates basic usage and performance testing
    of the Groq client.
    """
    print("🚀 Testing Groq Client")
    print("=" * 50)
    
    try:
        # Initialize client
        client = GroqClient()
        
        # Test basic connection
        print("\n📡 Testing API Connection...")
        success, message = client.test_connection()
        print(f"Connection test: {'✅ Success' if success else '❌ Failed'}")
        print(f"Response: {message}")
        
        if not success:
            return
        
        # Show available models
        print("\n🤖 Available Models:")
        for model_key, model_info in client.list_available_models().items():
            print(f"  {model_key}: {model_info['description']} (max tokens: {model_info['max_tokens']})")
        
        # Performance test
        test_prompts = [
            "Hi, I need to book a flight",
            "I want to fly from Boston to Miami next Friday", 
            "What's the weather like today?"
        ]
        
        print("\n⚡ Performance Test:")
        total_time = 0
        
        for i, prompt in enumerate(test_prompts, 1):
            try:
                response = client.chat(
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a helpful flight booking assistant. Keep responses concise."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                response_time = response.get('response_time', 0)
                total_time += response_time
                
                print(f"\n  Test {i}: '{prompt}'")
                print(f"  Response: {response['message']['content'][:80]}...")
                print(f"  Time: {response_time:.2f}s")
                print(f"  Tokens used: {response.get('usage', {}).get('total_tokens', 'N/A')}")
                
            except Exception as e:
                print(f"  Test {i} failed: {e}")
        
        avg_time = total_time / len(test_prompts) if test_prompts else 0
        print(f"\n📊 Average response time: {avg_time:.2f}s")
        print("✅ Groq provides fast inference compared to traditional LLM hosting!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure GROQ_API_KEY environment variable is set")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Error during Groq client testing")


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    main()