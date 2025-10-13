"""
Rewrite of the core retrieval pipeline to ensure consistent and correct data handling.
This file addresses the fundamental issues with retrieval, text encoding, and context formatting.
"""

import sys
import os
from pathlib import Path
import json
import re
import unicodedata
import time
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retrieval.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import necessary modules
from core.memvid_retriever import RetrievalResult
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


def normalize_text(text: str) -> str:
    """
    Normalize text to handle Unicode and encoding issues.
    
    Args:
        text: The text to normalize
        
    Returns:
        str: The normalized text
    """
    # Replace common problematic character sequences
    replacements = {
        'Ã²': 'ò',
        'Ã¹': 'ù',
        'Ã¨': 'è',
        'Ã©': 'é',
        'Ã ': 'à',
        'Ã¬': 'ì',
        'ï¬': 'fi',
        'â€™': "'",
        'â€"': '-',
        'â€œ': '"',
        'â€': '"',
        'Â': ' '
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFC', text)
    
    return text


def direct_metadata_search(document_id: str, query: str, metadata_only: bool = False) -> List[Dict[str, Any]]:
    """
    Perform a direct search in the metadata files, bypassing the Memvid retriever.
    This ensures we find relevant content even if the semantic search is not working.
    
    Args:
        document_id: The document ID
        query: The search query
        metadata_only: Whether to return only metadata without the text
        
    Returns:
        List[Dict[str, Any]]: The search results
    """
    try:
        # Get document from database
        document = get_document_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return []
        
        # Get base name and directory
        video_path = document.video_path
        video_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Find metadata file
        metadata_file = os.path.join(video_dir, f"{base_name}_metadata.json")
        if not os.path.exists(metadata_file):
            # Try alternative names
            for alt_name in [f"{base_name}_sections_metadata.json", f"{base_name}_simple_metadata.json"]:
                alt_file = os.path.join(video_dir, alt_name)
                if os.path.exists(alt_file):
                    metadata_file = alt_file
                    break
        
        if not os.path.exists(metadata_file):
            logger.error(f"Metadata file not found for document {document_id}")
            return []
        
        logger.info(f"Loading metadata from {metadata_file}")
        
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Extract chunks
        chunks = metadata.get('chunks', [])
        if not chunks:
            logger.error(f"No chunks found in metadata file for document {document_id}")
            return []
        
        logger.info(f"Loaded {len(chunks)} chunks from metadata file")
        
        # Process the query
        query_lower = query.lower()
        
        # Check if this is an article query
        article_match = re.search(r'articolo\s+(\d+)', query_lower)
        page_match = re.search(r'pagina\s+(\d+)', query_lower)
        last_page_query = "ultima pagina" in query_lower
        
        results = []
        
        # Handle article queries
        if article_match:
            article_num = article_match.group(1)
            article_pattern = fr"art(?:\.|icolo)?\s*{article_num}\b|articolo\s+{article_num}\b"
            
            logger.info(f"Looking for article {article_num} in chunks")
            
            article_chunks = []
            for i, chunk in enumerate(chunks):
                if 'text' not in chunk:
                    continue
                    
                text = chunk['text'].lower()
                if re.search(article_pattern, text):
                    article_chunks.append((i, chunk))
                    logger.info(f"Found article {article_num} reference in chunk {i}")
            
            # Process article chunks
            if article_chunks:
                # Look for chunks that contain the article header
                header_chunks = []
                for i, chunk in article_chunks:
                    text = chunk['text'].lower()
                    if f"art. {article_num}." in text or f"articolo {article_num}." in text:
                        header_chunks.append((i, chunk))
                
                # If we found header chunks, prioritize them
                if header_chunks:
                    logger.info(f"Found {len(header_chunks)} header chunks for article {article_num}")
                    # Sort by position if metadata available
                    if all('metadata' in c and 'start' in c['metadata'] for _, c in header_chunks):
                        header_chunks.sort(key=lambda x: x[1]['metadata'].get('start', 0))
                    
                    # Add all header chunks to results
                    for i, chunk in header_chunks:
                        if metadata_only:
                            results.append({'metadata': chunk.get('metadata', {})})
                        else:
                            result = {
                                'text': normalize_text(chunk['text']),
                                'metadata': chunk.get('metadata', {})
                            }
                            results.append(result)
                
                # If no header chunks or not enough results, add other article chunks
                if len(results) < 5:
                    remaining_chunks = [c for c in article_chunks if c not in header_chunks]
                    if remaining_chunks:
                        # Sort by position if metadata available
                        if all('metadata' in c[1] and 'start' in c[1]['metadata'] for c in remaining_chunks):
                            remaining_chunks.sort(key=lambda x: x[1]['metadata'].get('start', 0))
                        
                        # Add remaining chunks to results
                        for i, chunk in remaining_chunks[:5 - len(results)]:
                            if metadata_only:
                                results.append({'metadata': chunk.get('metadata', {})})
                            else:
                                result = {
                                    'text': normalize_text(chunk['text']),
                                    'metadata': chunk.get('metadata', {})
                                }
                                results.append(result)
        
        # Handle page queries
        elif page_match or last_page_query:
            if page_match:
                page_num = page_match.group(1)
                logger.info(f"Looking for page {page_num} in chunks")
                
                page_chunks = []
                for i, chunk in enumerate(chunks):
                    # Check metadata for page number
                    if 'metadata' in chunk and 'page' in chunk['metadata'] and str(chunk['metadata']['page']) == page_num:
                        page_chunks.append((i, chunk))
                        logger.info(f"Found page {page_num} in metadata of chunk {i}")
                    
                    # Check text for page markers
                    elif 'text' in chunk:
                        text = chunk['text']
                        if f"## Pagina {page_num}" in text or f"Page {page_num}" in text:
                            page_chunks.append((i, chunk))
                            logger.info(f"Found page {page_num} marker in text of chunk {i}")
                
                # Add page chunks to results
                if page_chunks:
                    for i, chunk in page_chunks:
                        if metadata_only:
                            results.append({'metadata': chunk.get('metadata', {})})
                        else:
                            result = {
                                'text': normalize_text(chunk['text']),
                                'metadata': chunk.get('metadata', {})
                            }
                            results.append(result)
            
            # Handle "ultima pagina" query
            elif last_page_query:
                logger.info(f"Looking for highest page number")
                
                # Find highest page number
                highest_page = 0
                highest_chunks = []
                
                for i, chunk in enumerate(chunks):
                    if 'metadata' in chunk and 'page' in chunk['metadata']:
                        page = chunk['metadata']['page']
                        if isinstance(page, (int, float)) and page > highest_page:
                            highest_page = page
                            highest_chunks = [(i, chunk)]
                        elif page == highest_page:
                            highest_chunks.append((i, chunk))
                
                if highest_page > 0:
                    logger.info(f"Found highest page: {highest_page}")
                    
                    # Add highest page chunks to results
                    for i, chunk in highest_chunks:
                        if metadata_only:
                            results.append({'metadata': chunk.get('metadata', {})})
                        else:
                            result = {
                                'text': normalize_text(chunk['text']),
                                'metadata': chunk.get('metadata', {})
                            }
                            results.append(result)
        
        # Handle other queries with simple keyword matching
        else:
            # Define a score function based on keyword matching
            def score_chunk(chunk):
                if 'text' not in chunk:
                    return 0
                
                text = chunk['text'].lower()
                # Count occurrences of query terms
                score = 0
                for term in query_lower.split():
                    if len(term) > 3:  # Only consider terms with more than 3 characters
                        score += text.count(term)
                
                return score
            
            # Score and sort chunks
            scored_chunks = [(i, chunk, score_chunk(chunk)) for i, chunk in enumerate(chunks)]
            scored_chunks.sort(key=lambda x: x[2], reverse=True)
            
            # Add top-scoring chunks to results
            for i, chunk, score in scored_chunks[:10]:
                if score > 0:
                    if metadata_only:
                        results.append({'metadata': chunk.get('metadata', {})})
                    else:
                        result = {
                            'text': normalize_text(chunk['text']),
                            'metadata': chunk.get('metadata', {}),
                            'score': score
                        }
                        results.append(result)
        
        logger.info(f"Found {len(results)} results for query: {query}")
        return results
    
    except Exception as e:
        logger.error(f"Error in direct_metadata_search: {str(e)}", exc_info=True)
        return []


def convert_to_retrieval_results(search_results: List[Dict[str, Any]]) -> List[RetrievalResult]:
    """
    Convert direct search results to RetrievalResult objects.
    
    Args:
        search_results: The direct search results
        
    Returns:
        List[RetrievalResult]: The search results as RetrievalResult objects
    """
    retrieval_results = []
    
    for i, result in enumerate(search_results):
        text = result.get('text', '')
        metadata = result.get('metadata', {})
        score = result.get('score', 1.0)
        
        retrieval_result = RetrievalResult(
            text=text,
            score=score,
            meta_info=metadata
        )
        
        retrieval_results.append(retrieval_result)
    
    return retrieval_results


def format_context_for_llm_robust(results: List[RetrievalResult]) -> str:
    """
    Improved version of format_context_for_llm that ensures text is normalized
    and properly formatted for the LLM.
    
    Args:
        results: List of retrieval results
        
    Returns:
        str: Formatted context
    """
    if not results:
        return ""
    
    context_parts = []
    
    # Check if we have occurrence count metadata
    count_info = ""
    if results and hasattr(results[0], 'meta_info') and results[0].meta_info:
        total = results[0].meta_info.get('total_occurrences', 0)
        shown = results[0].meta_info.get('shown_occurrences', 0)
        term = results[0].meta_info.get('search_term', '')
        
        if total > 0 and term:
            if total > shown:
                count_info = f"\n**NOTA IMPORTANTE**: Ho trovato {total} occorrenze totali del termine '{term}' nel documento. Per motivi di spazio, ne mostro le prime {shown} più rilevanti.\n"
            else:
                count_info = f"\n**NOTA**: Ho trovato {total} occorrenze del termine '{term}' nel documento. Ecco tutte le occorrenze trovate:\n"
            context_parts.append(count_info)
    
    for i, result in enumerate(results):
        # Normalize text to handle encoding issues
        text = normalize_text(result.text)
        
        # Create hierarchical context header
        header_parts = []
        
        # Add page information if available
        page_num = None
        if 'page' in result.meta_info:
            page_num = result.meta_info['page']
            header_parts.append(f"Pagina {page_num}")
        
        # Check for page marker in text if not in metadata
        if not page_num:
            page_match = re.search(r'## Pagina (\d+)', text)
            if page_match:
                page_num = page_match.group(1)
                header_parts.append(f"Pagina {page_num}")
        
        # Add section title if available
        section_title = None
        if 'title' in result.meta_info:
            section_title = result.meta_info['title']
            header_parts.append(f"Sezione: {section_title}")
        
        # Check for article title in text
        if not section_title:
            article_match = re.search(r'(Art(?:\.|icolo)?\s*\d+\.\s*[^\n.]+)', text)
            if article_match:
                section_title = article_match.group(1).strip()
                header_parts.append(f"Sezione: {section_title}")
        
        # Add section number if available
        if 'section' in result.meta_info and 'total_sections' in result.meta_info:
            section_num = result.meta_info['section']
            total_sections = result.meta_info['total_sections']
            header_parts.append(f"Sezione {section_num} di {total_sections}")
        
        # Create header string
        header = ""
        if header_parts:
            header = "[" + "] [".join(header_parts) + "]"
        
        # Format text with header
        section_text = f"{header}\n\n{text}" if header else text
        context_parts.append(section_text)
    
    # Join all parts with clear separators
    formatted_context = "\n\n---\n\n".join(context_parts)
    
    # If we added count info, make sure it's at the beginning
    if count_info:
        # Remove count_info from parts and add it at the start
        context_parts = [p for p in context_parts if p != count_info]
        formatted_context = count_info + "\n\n---\n\n".join(context_parts)
    
    return formatted_context


def perform_hybrid_search_robust(document_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
    """
    Robust hybrid search that combines direct metadata search with semantic search.
    
    Args:
        document_id: The document ID
        query: The search query
        top_k: Maximum number of results to return
        
    Returns:
        List[RetrievalResult]: Combined search results
    """
    logger.info(f"Starting hybrid search for query: '{query}'")
    
    # Check for specific query types
    query_lower = query.lower()
    article_match = re.search(r'articolo\s+(\d+)', query_lower)
    page_match = re.search(r'pagina\s+(\d+)', query_lower)
    last_page_query = "ultima pagina" in query_lower
    
    # NEW: Check for "find all" or "occurrences" queries
    find_all_query = any(phrase in query_lower for phrase in [
        'trova tutte', 'trova tutti', 'tutte le occorrenze', 'tutti i riferimenti',
        'cerca tutte', 'elenca tutte', 'mostra tutte', 'quante volte',
        'cerca parola', 'cerca termine', 'cerca il termine', 'cerca la parola',
        'nel documento', 'nel testo', 'dove appare', 'dove compare',
        'in che pagine', 'in quali pagine', 'dammi tutte', 'lista completa',
        'ogni menzione', 'ogni riferimento', 'tutte le volte'
    ])
    
    # Extract search term for "find all" queries
    search_term = None
    if find_all_query:
        # Try to extract term in quotes - split into separate line
        quote_pattern = r'["\']([^"\'\n]+)["\']'
        quote_match = re.search(quote_pattern, query)
        if quote_match:
            search_term = quote_match.group(1)
        # Or extract term after "parola", "termine", etc.
        elif 'parola' in query_lower:
            term_match = re.search(r'parola\s+["\']?([\w]+)["\']?', query_lower)
            if term_match:
                search_term = term_match.group(1)
        elif 'termine' in query_lower:
            term_match = re.search(r'termine\s+["\']?([\w]+)["\']?', query_lower)
            if term_match:
                search_term = term_match.group(1)
        
        # If still no term, try to find a quoted or capitalized word
        if not search_term:
            words = query.split()
            for word in words:
                if len(word) > 3 and word[0].isupper() and word.lower() not in [
                    'trova', 'tutte', 'occorrenze', 'riferimenti', 'cerca', 'elenca', 'mostra'
                ]:
                    search_term = word.lower()
                    break
        
        if search_term:
            logger.info(f"Detected 'find all' query for term: {search_term}")
            # Use direct search with expanded top_k
            direct_results = direct_metadata_search(document_id, search_term)
            if direct_results:
                total_count = len(direct_results)
                max_results = 30  # Increased from 20 to 30
                logger.info(f"Found {total_count} results for find-all query, returning up to {max_results}")
                
                # Create results with count info
                results_to_return = direct_results[:min(max_results, total_count)]
                retrieval_results = convert_to_retrieval_results(results_to_return)
                
                # Add count information to the first result's metadata
                if retrieval_results and total_count > 0:
                    # Store total count for the LLM to use
                    if not hasattr(retrieval_results[0], 'meta_info'):
                        retrieval_results[0].meta_info = {}
                    retrieval_results[0].meta_info['total_occurrences'] = total_count
                    retrieval_results[0].meta_info['shown_occurrences'] = len(results_to_return)
                    retrieval_results[0].meta_info['search_term'] = search_term
                    logger.info(f"Added count metadata: {total_count} total, showing {len(results_to_return)}")
                
                return retrieval_results
    
    # For specific query types, use direct metadata search first
    if article_match or page_match or last_page_query:
        logger.info(f"Using direct metadata search for specific query type")
        direct_results = direct_metadata_search(document_id, query)
        
        if direct_results:
            logger.info(f"Found {len(direct_results)} results with direct metadata search")
            return convert_to_retrieval_results(direct_results)
    
    # Fall back to normal retrieval
    try:
        # Import here to avoid circular dependencies
        from core.memvid_retriever import get_context_for_query
        
        logger.info(f"Falling back to semantic search")
        retrieval_results = get_context_for_query(document_id, query, top_k=top_k)
        
        if retrieval_results:
            logger.info(f"Found {len(retrieval_results)} results with semantic search")
            return retrieval_results
        else:
            # If semantic search fails, try direct search as a last resort
            logger.info(f"Semantic search returned no results, trying direct metadata search")
            direct_results = direct_metadata_search(document_id, query)
            
            if direct_results:
                logger.info(f"Found {len(direct_results)} results with direct metadata search")
                return convert_to_retrieval_results(direct_results)
    
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
        
        # Try direct search as a fallback
        logger.info(f"Semantic search failed, trying direct metadata search")
        direct_results = direct_metadata_search(document_id, query)
        
        if direct_results:
            logger.info(f"Found {len(direct_results)} results with direct metadata search")
            return convert_to_retrieval_results(direct_results)
    
    logger.warning(f"No results found for query: {query}")
    return []


def process_query_robust(
    user_id: int,
    user_first_name: str,
    user_last_name: Optional[str],
    user_username: Optional[str],
    query: str,
    document_id: Optional[str] = None,
    include_history: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Robust process_query implementation that handles text encoding issues
    and ensures reliable retrieval.
    
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
        
        # Adjust top_k for specific queries
        query_lower = query.lower()
        is_article_query = "articolo" in query_lower or "art." in query_lower
        is_page_query = "pagina" in query_lower or "pag." in query_lower
        
        if is_article_query or is_page_query or "ultima pagina" in query_lower:
            top_k = max(top_k, 8)  # Use more context for specific queries
            logger.info(f"Using increased top_k={top_k} for specific query")
        
        # Use robust hybrid search
        logger.info(f"Using robust hybrid search for query: '{query}'")
        retrieval_results = perform_hybrid_search_robust(document_id, query, top_k=top_k)
        
        # Log retrieval results
        for i, result in enumerate(retrieval_results):
            logger.info(f"Result {i+1}: {result.text[:100]}...")
        
        # Format context with robust formatting
        context = format_context_for_llm_robust(retrieval_results)
        
        # Log the formatted context
        logger.info(f"Formatted context ({len(context)} characters):\n{context[:500]}...")
        
        # Save the full context to a debug file
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_logs")
        os.makedirs(debug_dir, exist_ok=True)
        with open(os.path.join(debug_dir, f"context_{int(time.time())}.txt"), "w", encoding="utf-8") as f:
            f.write(context)
        
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
        
        # Generate response
        response_data = generate_chat_response(
            query=query,
            context=context,
            conversation_history=history,
            temperature=temperature,
            max_tokens=max_tokens,
            document_metadata={
                "title": document.name,
                "path": document.video_path
            }
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
        import traceback
        logging.error(f"Error in process_query: {str(e)}", exc_info=True)
        return (
            f"I'm sorry, an error occurred while processing your question: {str(e)}\n\n{traceback.format_exc()}",
            {"error": str(e)}
        )
    
    finally:
        # Always close the session
        session.close()
