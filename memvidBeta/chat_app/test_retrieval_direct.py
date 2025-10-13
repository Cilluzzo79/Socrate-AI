"""
Direct testing script for retrieval and LLM generation without Telegram.
This script allows testing the retrieval and generation components directly.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(script_dir)
sys.path.append(project_root)

# Import the debug interceptor first to patch the function
try:
    import core.llm_debug
except ImportError:
    print("Warning: llm_debug module not found, debugging features will be disabled")

# Import necessary components
from core.memvid_retriever import get_retriever_manager, RetrievalResult, format_context_for_llm
from core.llm_client import generate_chat_response
from database.operations import get_document_by_id, sync_documents
from database.models import get_session, Document
from config.config import DEFAULT_TOP_K


def get_all_documents():
    """Get all documents from the database."""
    session = get_session()
    documents = session.query(Document).all()
    session.close()
    return documents


def perform_hybrid_search(document_id: str, query: str, top_k: int = DEFAULT_TOP_K):
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
    import re
    
    print(f"[HYBRID SEARCH] Starting for query: '{query}'")
    
    # First, check if this is a direct article or page query
    article_match = re.search(r'articolo\s+(\d+)', query.lower())
    page_match = re.search(r'pagina\s+(\d+)', query.lower())
    last_page_query = "ultima pagina" in query.lower()
    
    # Get the retriever manager
    manager = get_retriever_manager()
    
    # Get a retriever for the document
    retriever = manager.get_retriever(document_id)
    if not retriever:
        print(f"Retriever not found for document {document_id}")
        return []
    
    # If this is a specific article/page query, try direct search first
    if article_match or page_match or last_page_query:
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
                            print(f"[HYBRID SEARCH] Found direct match for article {article_num} in chunk {i}")
                            print(f"[HYBRID SEARCH] Text preview: {text[:100]}...")
                            
                            # Create a result
                            result = RetrievalResult(
                                text=chunk['text'],
                                score=0.99,  # High score for direct match
                                meta_info=chunk.get('metadata', {})
                            )
                            direct_matches.append(result)
                
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
                        print(f"[HYBRID SEARCH] Found page {page_num} in metadata of chunk {i}")
                        
                        result = RetrievalResult(
                            text=chunk['text'],
                            score=0.99,
                            meta_info=chunk['metadata']
                        )
                        direct_matches.append(result)
                    
                    # Check text for page markers
                    elif 'text' in chunk and isinstance(chunk['text'], str):
                        text = chunk['text']
                        if f"## Pagina {page_num}" in text or f"Page {page_num}" in text:
                            print(f"[HYBRID SEARCH] Found page {page_num} marker in text of chunk {i}")
                            
                            meta_info = chunk.get('metadata', {})
                            if 'page' not in meta_info:
                                meta_info['page'] = int(page_num)
                            
                            result = RetrievalResult(
                                text=chunk['text'],
                                score=0.99,
                                meta_info=meta_info
                            )
                            direct_matches.append(result)
                
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
                
                if highest_page > 0:
                    print(f"[HYBRID SEARCH] Found highest page: {highest_page}")
                    
                    for i, chunk in enumerate(highest_chunks):
                        result = RetrievalResult(
                            text=chunk['text'],
                            score=0.99,
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
    try:
        results = retriever.search(query, top_k=top_k)
        print(f"[HYBRID SEARCH] Semantic search returned {len(results)} results")
        
        # Convert to RetrievalResult objects
        retrieval_results = []
        for result in results:
            if isinstance(result, str):
                # Simple string result
                retrieval_results.append(RetrievalResult(
                    text=result,
                    score=1.0
                ))
            else:
                # Object with text and score
                try:
                    text = result.text if hasattr(result, 'text') else str(result)
                    score = float(getattr(result, 'score', 1.0))
                    
                    retrieval_result = RetrievalResult(
                        text=text,
                        score=score
                    )
                    
                    # Add metadata if available
                    if hasattr(result, "metadata"):
                        retrieval_result.meta_info = result.metadata
                    
                    retrieval_results.append(retrieval_result)
                except Exception as e:
                    print(f"[HYBRID SEARCH] Error processing result: {e}")
        
        # Enhance results with metadata
        retrieval_results = manager._enhance_results_with_metadata(document_id, results)
        
        return retrieval_results
    except Exception as e:
        print(f"[HYBRID SEARCH] Error in semantic search: {e}")
        return []


def main():
    # Sync documents to ensure all are in database
    print("Synchronizing documents...")
    sync_documents()
    
    # Get all documents
    documents = get_all_documents()
    
    if not documents:
        print("No documents found! Please make sure documents are available.")
        return
    
    print("\nAvailable documents:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc.document_id} ({os.path.basename(doc.video_path)})")
    
    # Select document
    while True:
        doc_idx_input = input("\nSelect document (number): ")
        try:
            doc_idx = int(doc_idx_input) - 1
            if 0 <= doc_idx < len(documents):
                document = documents[doc_idx]
                document_id = document.document_id
                break
            else:
                print(f"Please enter a number between 1 and {len(documents)}")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"\nSelected document: {document_id}")
    
    # Testing loop
    while True:
        # Get query
        query = input("\nEnter query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        
        # Get top_k
        top_k_input = input("Enter top_k (default: 5): ")
        top_k = int(top_k_input) if top_k_input.strip() else 5
        
        # Perform retrieval
        print(f"\nRetrieving context for: {query}")
        retrieval_results = perform_hybrid_search(document_id, query, top_k=top_k)
        
        if not retrieval_results:
            print("No results found for this query.")
            continue
        
        # Format context
        context = format_context_for_llm(retrieval_results)
        
        print(f"\nFormatted {len(retrieval_results)} chunks into context of length {len(context)}")
        
        # Preview context
        preview_len = min(500, len(context))
        print(f"\nContext preview:\n{context[:preview_len]}...")
        
        # Ask if user wants to see full context
        if input("\nShow full context? (y/n): ").lower() == 'y':
            print(f"\nFull context:\n{context}")
        
        # Ask if user wants to generate response
        if input("\nGenerate response? (y/n): ").lower() == 'y':
            print("\nGenerating response...")
            
            # Get document metadata
            manager = get_retriever_manager()
            document_metadata = {}
            if document_id in manager.metadata_cache:
                metadata = manager.metadata_cache[document_id]
                document_metadata = {
                    "title": os.path.basename(document.video_path),
                    "path": document.video_path
                }
                
                # Add structure if available
                if 'structure' in metadata:
                    document_metadata['structure'] = metadata['structure']
            
            # Generate response
            response = generate_chat_response(
                query=query,
                context=context,
                conversation_history=[],
                document_metadata=document_metadata
            )
            
            print(f"\nResponse:\n{response['text']}")
        
        # Ask whether to continue
        if input("\nContinue? (y/n): ").lower() != 'y':
            break


if __name__ == "__main__":
    print("Starting direct testing script...")
    main()
