"""
LLM client for the Memvid Chat system.
Handles interaction with the OpenRouter API for LLM generation.
"""

from pathlib import Path
import sys
import json
import time
from typing import List, Dict, Any, Optional, Union
import requests

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import configuration
from config.config import (
    OPENROUTER_API_KEY, 
    MODEL_NAME, 
    MAX_TOKENS, 
    TEMPERATURE
)


class OpenRouterClient:
    """Client for interacting with the OpenRouter API."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: API key for OpenRouter (defaults to config)
            model: Model to use (defaults to config)
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        # Use the correct model name as specified
        self.model = "anthropic/claude-3.7-sonnet"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = None, 
        temperature: float = None,
        top_p: float = None,
        frequency_penalty: float = None,
        presence_penalty: float = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries (role, content)
            max_tokens: Maximum number of tokens in the response
            temperature: Temperature for sampling
            top_p: Top-p for nucleus sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            
        Returns:
            Dict[str, Any]: Response from the API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or MAX_TOKENS,
            "temperature": temperature or TEMPERATURE,
        }
        
        # Add optional parameters if provided
        if top_p is not None:
            data["top_p"] = top_p
        
        if frequency_penalty is not None:
            data["frequency_penalty"] = frequency_penalty
        
        if presence_penalty is not None:
            data["presence_penalty"] = presence_penalty
        
        try:
            # Print the request data for debugging
            print(f"Sending request to OpenRouter API:\nURL: {self.api_url}\nModel: {self.model}\nMessages: {len(messages)} messages")
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            # Print response status for debugging
            print(f"OpenRouter API response status: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message = error_data["error"].get("message", str(e))
                print(f"API Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Failed to parse error response: {response.text if hasattr(response, 'text') else 'No response text'}")
            
            print(f"Error calling OpenRouter API: {error_message}")
            return {
                "error": True,
                "message": error_message
            }
    
    def chat(
        self, 
        query: str, 
        context: str, 
        conversation_history: List[Dict[str, str]] = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Generate a chat response with context.
        
        Args:
            query: User's query
            context: Context information for the query
            conversation_history: Previous conversation history
            max_tokens: Maximum number of tokens in the response
            temperature: Temperature for sampling
            
        Returns:
            Dict[str, Any]: Response including generated text and metadata
        """
        # Initialize messages with system message
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful assistant that answers questions based on the provided context. "
                          f"If the answer cannot be found in the context, say so clearly.\n\n"
                          f"Context:\n{context}"
            }
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response_data = self.generate_response(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Check for error
        if "error" in response_data:
            return {
                "text": f"I encountered an error: {response_data.get('message', 'Unknown error')}",
                "metadata": {
                    "error": True,
                    "message": response_data.get("message")
                }
            }
        
        # Extract the generated text
        try:
            generated_text = response_data["choices"][0]["message"]["content"]
            
            # Build response
            return {
                "text": generated_text,
                "metadata": {
                    "model": response_data.get("model", self.model),
                    "finish_reason": response_data["choices"][0].get("finish_reason"),
                    "usage": response_data.get("usage", {}),
                    "created": response_data.get("created", time.time())
                }
            }
        except (KeyError, IndexError) as e:
            return {
                "text": f"I encountered an error processing the response: {str(e)}",
                "metadata": {
                    "error": True,
                    "message": str(e),
                    "response_data": response_data
                }
            }


# Create a global client instance
llm_client = OpenRouterClient()


# Helper functions
def generate_chat_response(
    query: str, 
    context: str, 
    conversation_history: List[Dict[str, str]] = None,
    max_tokens: int = None,
    temperature: float = None
) -> Dict[str, Any]:
    """
    Generate a chat response with context.
    
    Args:
        query: User's query
        context: Context information for the query
        conversation_history: Previous conversation history
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature for sampling
        
    Returns:
        Dict[str, Any]: Response including generated text and metadata
    """
    return llm_client.chat(
        query=query,
        context=context,
        conversation_history=conversation_history,
        max_tokens=max_tokens,
        temperature=temperature
    )
