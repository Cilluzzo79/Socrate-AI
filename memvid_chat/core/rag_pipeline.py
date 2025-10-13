"""
Main RAG pipeline for the Memvid Chat system.
Integrates Memvid retrieval and LLM generation for document-based question answering.
"""

from pathlib import Path
import sys
from typing import List, Dict, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import local modules
from core.memvid_retriever import get_context_for_query, format_context_for_llm
from core.llm_client import generate_chat_response
from database.operations import (
    ensure_user_exists,
    get_or_create_conversation,
    add_message,
    get_conversation_messages,
    get_document_by_id
)
from config.config import user_settings_manager, DEFAULT_TOP_K, TEMPERATURE, MAX_TOKENS


def process_query(
    user_id: int,
    user_first_name: str,
    user_last_name: Optional[str],
    user_username: Optional[str],
    query: str,
    document_id: Optional[str] = None,
    include_history: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Process a user query using the RAG pipeline.
    
    Args:
        user_id: Telegram user ID
        user_first_name: User's first name
        user_last_name: User's last name
        user_username: User's username
        query: The user's query
        document_id: Document ID to search, or None to use user's current document
        include_history: Whether to include conversation history
        
    Returns:
        Tuple[str, Dict[str, Any]]: Response text and metadata
    """
    # Ensure user exists
    user_db = ensure_user_exists(
        telegram_id=user_id,
        first_name=user_first_name,
        last_name=user_last_name,
        username=user_username
    )
    
    # Get user settings
    user_settings = user_settings_manager.get_user_settings(user_id)
    
    # If no document ID provided, use the one from user settings
    if not document_id:
        document_id = user_settings.get("current_document")
    
    # If still no document ID, return error
    if not document_id:
        return (
            "No document selected. Please select a document using /select command.",
            {"error": "no_document"}
        )
    
    # Update user's current document
    user_settings_manager.update_user_setting(user_id, "current_document", document_id)
    
    # Get the document
    document = get_document_by_id(document_id)
    if not document:
        return (
            f"Document with ID '{document_id}' not found. Please select another document.",
            {"error": "document_not_found"}
        )
    
    # Get or create a conversation
    conversation, is_new = get_or_create_conversation(user_id, document_id)
    
    # Add user message to conversation
    add_message(
        conversation_id=conversation.id,
        role="user",
        content=query
    )
    
    # Get retrieval parameters
    top_k = user_settings.get("top_k", DEFAULT_TOP_K)
    temperature = user_settings.get("temperature", TEMPERATURE)
    max_tokens = user_settings.get("max_tokens", MAX_TOKENS)
    
    # Retrieve context from the document
    retrieval_results = get_context_for_query(document_id, query, top_k=top_k)
    
    # Format context for the LLM
    context = format_context_for_llm(retrieval_results)
    
    # Get conversation history if needed
    history = []
    if include_history:
        messages = get_conversation_messages(conversation.id)
        
        # Skip the current user message (we just added it)
        for message in messages[:-1]:
            history.append({
                "role": message.role,
                "content": message.content
            })
    
    # Generate response
    response_data = generate_chat_response(
        query=query,
        context=context,
        conversation_history=history,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # Add assistant message to conversation
    add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_data["text"],
        metadata=response_data["metadata"]
    )
    
    return response_data["text"], response_data["metadata"]
