"""
LLM client for the Memvid Chat system.
Handles interaction with the OpenRouter API for LLM generation.
Implements the Socrates personality for document analysis.
"""

from pathlib import Path
import sys
import json
import time
import os
from typing import List, Dict, Any, Optional, Union
import requests
import logging

# Configuration from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'anthropic/claude-haiku-4.5')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2048'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))

logger = logging.getLogger(__name__)

# Socrates system prompt with enhanced structural awareness
SOCRATES_SYSTEM_PROMPT = """
You are Socrate, an AI assistant specializing in deep textual analysis and thoughtful exploration of ideas. 
Your approach is modeled after the historical Socrates, who used methodical questioning to help others 
reach deeper understanding.

# Your Core Characteristics:
- You are thoughtful, insightful, and patient
- You ask probing questions that guide users toward their own discoveries
- You help users examine texts from multiple perspectives
- You are skilled at synthesizing complex information into clear structures
- You avoid giving simplistic answers, preferring to explore nuances and complexity

# Your Capabilities:
1. ANALYSIS: You can perform in-depth analysis of texts, examining themes, arguments, evidence, assumptions, and implications.

2. SUMMARIZATION: You can create comprehensive summaries at different levels of detail:
   - Brief overviews (1-2 paragraphs)
   - Extended summaries (multiple paragraphs with key points)
   - Chapter-by-chapter or section-by-section breakdowns

3. STRUCTURAL MAPPING: You can organize content into:
   - Hierarchical outlines
   - Concept maps showing relationships between ideas
   - Argument structures with premises and conclusions
   - Comparison frameworks highlighting similarities and differences

4. KNOWLEDGE ASSESSMENT: You can create:
   - Discussion questions at different levels of complexity
   - Quiz questions (multiple choice, true/false, short answer)
   - Thought experiments to test understanding
   - Scenarios for applying concepts

# Your Approach:
- When asked about a text, first ensure you understand what specific aspect the user wants to explore
- Respond to vague questions by offering several possible interpretations or asking clarifying questions
- Present information in organized, structured formats using markdown for clarity
- Use examples from the text to support your analysis
- When appropriate, connect ideas to broader contexts or universal principles
- Acknowledge limitations in the provided context if relevant information is missing

# Understanding Document Structure:
- Pay close attention to the hierarchical structure information provided with each text fragment
- Use this structure to understand how different sections relate to each other
- When responding, maintain awareness of where information comes from in the document structure
- Reference specific chapters, sections, and pages when answering to provide clear citations
- If asked about structure-related queries (e.g., "What's in Chapter 3?"), use the hierarchical path information

# Responding to Structural Queries:
- For questions about document organization, refer to the hierarchical paths provided
- When summarizing content, acknowledge the section or chapter being summarized
- If providing page references, mention them explicitly (e.g., "On page 45, the author states...")
- Use structural awareness to connect related concepts from different parts of the document

Remember that your purpose is to deepen understanding through thoughtful dialogue. Guide users to 
discover insights rather than simply delivering information.

For the content below, you'll receive chunks of text from different parts of a document, with 
hierarchical path and page information when available. Use this structural context to provide
more coherent and precisely cited responses.

Context:
"""


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
        # Changed to Claude Haiku 4.5 for better reliability and speed
        # Claude Haiku: fast, reliable, good balance of cost/performance
        # Input: ~$0.80/1M, Output: ~$4.00/1M
        self.model = model or "anthropic/claude-haiku-4.5"
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
            payload_preview = {
                "model": self.model,
                "messages": len(messages),
                "max_tokens": data["max_tokens"],
                "temperature": data.get("temperature")
            }
            logger.info("Calling OpenRouter API", extra={"payload_preview": payload_preview})
            response = requests.post(self.api_url, headers=headers, json=data)
            logger.info("OpenRouter API response", extra={"status_code": response.status_code})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_payload = None
            try:
                error_data = response.json()
                error_payload = error_data
                if "error" in error_data:
                    error_message = error_data["error"].get("message", str(e))
            except Exception:
                error_payload = getattr(response, "text", "")
            logger.error("Error calling OpenRouter API", extra={"message": error_message, "response": error_payload})
            return {
                "error": True,
                "message": error_message
            }
        except Exception as e:
            logger.exception("Unexpected error calling OpenRouter API")
            return {
                "error": True,
                "message": str(e)
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
        # Initialize messages with Socrates system message
        messages = [
            {
                "role": "system",
                "content": SOCRATES_SYSTEM_PROMPT + context
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
                "text": f"Mi dispiace, ho incontrato un errore: {response_data.get('message', 'Errore sconosciuto')}",
                "metadata": {
                    "error": True,
                    "message": response_data.get("message")
                }
            }
        
        # Extract the generated text
        try:
            generated_text = response_data["choices"][0]["message"].get("content", "")
            metadata = {
                "model": response_data.get("model", self.model),
                "finish_reason": response_data["choices"][0].get("finish_reason"),
                "usage": response_data.get("usage", {}),
                "created": response_data.get("created", time.time())
            }

            logger.debug("LLM raw response", extra={
                "finish_reason": metadata["finish_reason"],
                "usage": metadata["usage"],
                "text_length": len(generated_text or "")
            })

            normalized_text = (generated_text or "").strip()
            if not normalized_text:
                normalized_text = "Non è stato possibile generare una risposta. Riprova con una domanda più specifica."

            return {
                "text": normalized_text,
                "metadata": metadata
            }
        except (KeyError, IndexError) as e:
            return {
                "text": f"Mi dispiace, ho incontrato un errore durante l'elaborazione della risposta: {str(e)}",
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
    temperature: float = None,
    document_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate a chat response with context.
    
    Args:
        query: User's query
        context: Context information for the query
        conversation_history: Previous conversation history
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature for sampling
        document_metadata: Additional metadata about the document
        
    Returns:
        Dict[str, Any]: Response including generated text and metadata
    """
    # Add document metadata to query if available
    enhanced_query = query
    if document_metadata:
        # Create a metadata prefix
        metadata_prefix = ""
        if 'title' in document_metadata:
            metadata_prefix += f"[Documento: {document_metadata['title']}]\n"
        if 'structure' in document_metadata and isinstance(document_metadata['structure'], dict):
            if 'sections' in document_metadata['structure']:
                sections_count = len(document_metadata['structure']['sections'])
                metadata_prefix += f"[Il documento contiene {sections_count} sezioni principali]\n"
        
        if metadata_prefix:
            enhanced_query = f"{metadata_prefix}\n{query}"
    
    return llm_client.chat(
        query=enhanced_query,
        context=context,
        conversation_history=conversation_history,
        max_tokens=max_tokens,
        temperature=temperature
    )
