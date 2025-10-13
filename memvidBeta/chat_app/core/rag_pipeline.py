"""
Enhanced RAG pipeline for the Memvid Chat system.
Improved to prioritize direct keyword matches for specific queries.
"""

from pathlib import Path
import sys
import os
import re
import random
from typing import List, Dict, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import local modules
from core.memvid_retriever import get_context_for_query, format_context_for_llm, get_retriever_manager, RetrievalResult
from core.llm_client import generate_chat_response
from database.operations import (
    ensure_user_exists,
    get_or_create_conversation,
    add_message,
    get_conversation_messages,
    get_document_by_id
)
from database.models import get_session
from config.config import user_settings_manager, DEFAULT_TOP_K, TEMPERATURE, MAX_TOKENS


def perform_hybrid_search(document_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
    """
    Perform a hybrid search that combines semantic search and keyword matching.
    
    This is especially useful for finding specific articles or page numbers that
    might not be well-represented in the semantic space.
    
    Args:
        document_id: The document ID
        query: The search query
        top_k: Maximum number of results to return
        
    Returns:
        List[RetrievalResult]: Combined and deduplicated results
    """
    print(f"[HYBRID SEARCH] Starting for query: '{query}'")
    
    # First, check if this is a direct article or page query
    article_match = re.search(r'articolo\s+(\d+)', query.lower())
    page_match = re.search(r'pagina\s+(\d+)', query.lower())
    last_page_query = "ultima pagina" in query.lower()
    
    # If this is a specific article/page query, try direct search first
    if article_match or page_match or last_page_query:
        # Get the retriever manager for direct access to metadata
        manager = get_retriever_manager()
        
        # Only proceed if we have metadata
        if document_id in manager.metadata_cache and 'chunks' in manager.metadata_cache[document_id]:
            metadata = manager.metadata_cache[document_id]
            chunks = metadata['chunks']
            direct_matches = []
            
            # Search for specific article
            if article_match:
                article_num = article_match.group(1)
                article_pattern = f"articolo\\s+{article_num}|art\\.\\s+{article_num}|art\\s+{article_num}"
                
                print(f"[HYBRID SEARCH] Looking for article {article_num} in {len(chunks)} chunks")
                
                # Find chunks that directly mention the article
                for i, chunk in enumerate(chunks):
                    if 'text' in chunk and isinstance(chunk['text'], str):
                        text = chunk['text'].lower()
                        if re.search(article_pattern, text):
                            # Create a retrieval result with high score
                            result = RetrievalResult(
                                text=chunk['text'],
                                score=0.99,  # High score for direct match
                                meta_info=chunk.get('metadata', {})
                            )
                            direct_matches.append(result)
                            print(f"[HYBRID SEARCH] Found direct match for article {article_num} in chunk {i}")
                
                # If we found direct matches, use them directly
                if direct_matches:
                    print(f"[HYBRID SEARCH] Found {len(direct_matches)} direct matches for article {article_num}")
                    
                    # Return the top direct matches
                    direct_matches = direct_matches[:top_k]
                    return direct_matches
            
            # Search for specific page
            if page_match:
                page_num = page_match.group(1)
                print(f"[HYBRID SEARCH] Looking for page {page_num} in chunks")
                
                # Find chunks with that page number
                for i, chunk in enumerate(chunks):
                    # Check metadata
                    if 'metadata' in chunk and 'page' in chunk['metadata'] and str(chunk['metadata']['page']) == page_num:
                        result = RetrievalResult(
                            text=chunk['text'],
                            score=0.99,  # High score for direct match
                            meta_info=chunk['metadata']
                        )
                        direct_matches.append(result)
                        print(f"[HYBRID SEARCH] Found page {page_num} in metadata of chunk {i}")
                    
                    # Check for explicit page markers in text
                    elif 'text' in chunk and isinstance(chunk['text'], str):
                        text = chunk['text']
                        if f"## Pagina {page_num}" in text or f"Page {page_num}" in text:
                            meta_info = chunk.get('metadata', {})
                            # Add page info if not already present
                            if 'page' not in meta_info:
                                meta_info['page'] = int(page_num)
                            
                            result = RetrievalResult(
                                text=chunk['text'],
                                score=0.99,  # High score for direct match
                                meta_info=meta_info
                            )
                            direct_matches.append(result)
                            print(f"[HYBRID SEARCH] Found page {page_num} in text of chunk {i}")
                
                # If we found direct matches, use them directly
                if direct_matches:
                    print(f"[HYBRID SEARCH] Found {len(direct_matches)} direct matches for page {page_num}")
                    
                    # Return the top direct matches
                    direct_matches = direct_matches[:top_k]
                    return direct_matches
            
            # Search for "ultima pagina"
            if last_page_query:
                print(f"[HYBRID SEARCH] Looking for highest page number")
                
                # Find highest page
                highest_page = 0
                highest_chunks = []
                
                for chunk in chunks:
                    if 'metadata' in chunk and 'page' in chunk['metadata']:
                        page = chunk['metadata']['page']
                        if isinstance(page, int) and page > highest_page:
                            highest_page = page
                            highest_chunks = [chunk]
                        elif page == highest_page:
                            highest_chunks.append(chunk)
                
                if highest_page > 0 and highest_chunks:
                    print(f"[HYBRID SEARCH] Found highest page: {highest_page}")
                    
                    # Create results for these chunks
                    for chunk in highest_chunks:
                        # Create retrieval result
                        result = RetrievalResult(
                            text=chunk['text'],
                            score=0.99,  # High score
                            meta_info=chunk['metadata']
                        )
                        direct_matches.append(result)
                    
                    # If we found direct matches, use them directly
                    if direct_matches:
                        print(f"[HYBRID SEARCH] Found {len(direct_matches)} chunks from highest page {highest_page}")
                        
                        # Return the top direct matches
                        direct_matches = direct_matches[:top_k]
                        return direct_matches
    
    # If we didn't find specific matches or this isn't a specific article/page query,
    # fall back to semantic search
    print(f"[HYBRID SEARCH] Performing semantic search as fallback")
    
    # First, perform normal semantic search
    semantic_results = get_context_for_query(document_id, query, top_k=top_k)
    print(f"[HYBRID SEARCH] Semantic search returned {len(semantic_results)} results")
    
    return semantic_results


def extract_document_structure_info(document_id: str) -> Dict[str, Any]:
    """
    Extract structure information from a document.
    
    Args:
        document_id: The document ID
        
    Returns:
        Dict[str, Any]: Document structure information
    """
    try:
        retriever_manager = get_retriever_manager()
        
        # Get document from database
        document = get_document_by_id(document_id)
        if not document:
            return {}
        
        # Get metadata from retriever manager
        metadata = {}
        if document_id in retriever_manager.metadata_cache:
            metadata = retriever_manager.metadata_cache[document_id]
        
        # Extract document title - safely get attributes
        document_name = getattr(document, 'name', None)
        document_title = document_name if document_name else os.path.basename(document.video_path)
        
        # Create structure information
        structure_info = {
            "title": document_title,
            "path": document.video_path,
        }
        
        # Add structure if available
        if 'structure' in metadata:
            structure_info['structure'] = metadata['structure']
        
        # Add other metadata if available
        if 'chunks_count' in metadata:
            structure_info['chunks_count'] = metadata['chunks_count']
        
        if 'total_text_length' in metadata:
            structure_info['total_text_length'] = metadata['total_text_length']
            
        # Get information about articles in the document
        articles_found = set()
        max_page = 0
        
        if 'chunks' in metadata:
            for chunk in metadata['chunks']:
                # Check for articles
                if 'text' in chunk:
                    text = chunk['text'].lower()
                    
                    # Extract article numbers
                    article_matches = re.finditer(r'articolo\s+(\d+)|art\.\s+(\d+)|art\s+(\d+)', text)
                    for match in article_matches:
                        article_num = match.group(1) or match.group(2) or match.group(3)
                        if article_num:
                            articles_found.add(article_num)
                
                # Check for pages
                if 'metadata' in chunk and 'page' in chunk['metadata']:
                    page_num = chunk['metadata']['page']
                    if isinstance(page_num, int) and page_num > max_page:
                        max_page = page_num
        
        # Add article and page information
        structure_info['articles_found'] = sorted(list(articles_found), key=lambda x: int(x))
        structure_info['max_page'] = max_page
        
        return structure_info
    except Exception as e:
        print(f"Error extracting document structure: {e}")
        return {}


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
    # Get a fresh session for this operation
    session = get_session()
    
    try:
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
        
        # Make sure conversation is attached to the current session
        conversation = session.merge(conversation)
        
        # Get conversation ID (we need this later)
        conversation_id = conversation.id
        
        # Add user message to conversation
        add_message(
            conversation_id=conversation_id,
            role="user",
            content=query
        )
        
        # Get retrieval parameters
        top_k = user_settings.get("top_k", DEFAULT_TOP_K)
        temperature = user_settings.get("temperature", TEMPERATURE)
        max_tokens = user_settings.get("max_tokens", MAX_TOKENS)
        
        # Analyze query to determine if it's a structure-related question
        structure_terms = ['struttura', 'capitoli', 'sezioni', 'indice', 'sommario', 
                          'organizzato', 'suddiviso', 'strutturato', 'paragrafi',
                          'structure', 'chapters', 'sections', 'index', 'summary',
                          'organized', 'divided', 'structured', 'paragraphs']
        
        article_terms = ['articolo', 'art.', 'art ', 
                         'article']
                         
        page_terms = ['pagina', 'pag.', 'pag ', 
                     'page']
        
        is_structure_query = any(term in query.lower() for term in structure_terms)
        is_article_query = any(term in query.lower() for term in article_terms)
        is_page_query = any(term in query.lower() for term in page_terms)
        
        # Adjust top_k for specific queries
        if is_article_query or is_page_query or "ultima pagina" in query.lower():
            top_k = max(top_k, 8)  # Use more context for specific queries
            print(f"Using increased top_k={top_k} for specific query")
        
        if is_structure_query:
            top_k = max(top_k, 10)  # Use even more context for structure questions
        
        # Use enhanced search for all queries
        print(f"Using hybrid search for query: '{query}'")
        retrieval_results = perform_hybrid_search(document_id, query, top_k=top_k)
        
        # Format context for the LLM
        context = format_context_for_llm(retrieval_results)
        
        # Get conversation history if needed
        history = []
        if include_history:
            messages = get_conversation_messages(conversation_id)
            
            # Skip the current user message (we just added it)
            for message in messages[:-1]:
                history.append({
                    "role": message.role,
                    "content": message.content
                })
        
        # Extract document structure information for LLM context
        try:
            document_structure = extract_document_structure_info(document_id)
        except Exception as e:
            print(f"Error extracting document structure: {e}")
            document_structure = {}
        
        # Generate response
        response_data = generate_chat_response(
            query=query,
            context=context,
            conversation_history=history,
            temperature=temperature,
            max_tokens=max_tokens,
            document_metadata=document_structure
        )
        
        # Add assistant message to conversation
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_data["text"],
            metadata=response_data["metadata"]
        )
        
        # Commit changes
        session.commit()
        
        return response_data["text"], response_data["metadata"]
    
    except Exception as e:
        import logging
        logging.error(f"Error in process_query: {str(e)}", exc_info=True)
        return (
            f"I'm sorry, an error occurred while processing your question: {str(e)}",
            {"error": str(e)}
        )
    
    finally:
        # Always close the session
        session.close()
