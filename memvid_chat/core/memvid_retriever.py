"""
Memvid retrieval module for the Memvid Chat system.
Handles interaction with Memvid documents for context retrieval.
"""

from pathlib import Path
import sys
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import Memvid
try:
    from memvid import MemvidRetriever
except ImportError:
    raise ImportError("Memvid library not found. Please install it using 'pip install memvid'")

# Import configuration
from config.config import DEFAULT_TOP_K
from database.operations import get_document_by_id, update_document_access


@dataclass
class RetrievalResult:
    """Class to store the result of a retrieval operation."""
    text: str
    score: float
    source: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None


class MemvidRetrieverManager:
    """
    Class to manage Memvid retrievers for different documents.
    Handles caching and retrieval operations.
    """
    
    def __init__(self):
        self.retrievers = {}
        self.retriever_stats = {}
    
    def get_retriever(self, document_id: str) -> Optional[MemvidRetriever]:
        """
        Get a Memvid retriever for a document.
        Creates a new retriever if none exists for the document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Optional[MemvidRetriever]: The retriever, or None if document not found
        """
        # Check if retriever already exists and is cached
        if document_id in self.retrievers:
            # Update stats
            self.retriever_stats[document_id]["last_used"] = time.time()
            self.retriever_stats[document_id]["use_count"] += 1
            return self.retrievers[document_id]
        
        # Get document from database
        document = get_document_by_id(document_id)
        if not document:
            return None
        
        # Update document access time
        update_document_access(document_id)
        
        # Create new retriever
        try:
            retriever = MemvidRetriever(document.video_path, document.index_path)
            self.retrievers[document_id] = retriever
            
            # Initialize stats
            self.retriever_stats[document_id] = {
                "created_at": time.time(),
                "last_used": time.time(),
                "use_count": 1
            }
            
            return retriever
        except Exception as e:
            print(f"Error creating retriever for document {document_id}: {e}")
            return None
    
    def search(self, document_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
        """
        Search a document for relevant context.
        
        Args:
            document_id: The document ID
            query: The search query
            top_k: Maximum number of results to return
            
        Returns:
            List[RetrievalResult]: List of retrieval results
        """
        retriever = self.get_retriever(document_id)
        if not retriever:
            return []
        
        try:
            # Search using the retriever
            results = retriever.search(query, top_k=top_k)
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for result in results:
                # Handle different types of results
                if isinstance(result, str):
                    # If result is a string, use it directly as text with a default score
                    retrieval_result = RetrievalResult(
                        text=result,
                        score=1.0  # Default score
                    )
                else:
                    # Try to get text and score from result object
                    try:
                        if hasattr(result, 'text'):
                            text = result.text
                        else:
                            # If result has no text attribute but can be converted to string
                            text = str(result)
                        
                        # Try to get score, default to 1.0 if not available
                        score = float(getattr(result, 'score', 1.0))
                        
                        retrieval_result = RetrievalResult(
                            text=text,
                            score=score
                        )
                        
                        # Add source if available
                        if hasattr(result, "source"):
                            retrieval_result.source = result.source
                        
                        # Add metadata if available
                        if hasattr(result, "metadata"):
                            retrieval_result.meta_info = result.metadata
                    except Exception as e:
                        print(f"Error processing result: {e}")
                        # Use string representation as fallback
                        retrieval_result = RetrievalResult(
                            text=str(result),
                            score=1.0
                        )
                
                retrieval_results.append(retrieval_result)
            
            return retrieval_results
        except Exception as e:
            print(f"Error searching document {document_id}: {e}")
            return []
    
    def cleanup_unused_retrievers(self, max_age: int = 3600, max_count: int = 10):
        """
        Clean up retrievers that haven't been used in a while.
        
        Args:
            max_age: Maximum age in seconds before a retriever is considered unused
            max_count: Maximum number of retrievers to keep in cache
        """
        current_time = time.time()
        
        # Get retrievers sorted by last used time (oldest first)
        sorted_retrievers = sorted(
            self.retriever_stats.items(),
            key=lambda x: x[1]["last_used"]
        )
        
        # Remove old retrievers
        for document_id, stats in sorted_retrievers:
            # Keep if within max count and not too old
            if (len(self.retrievers) <= max_count and 
                current_time - stats["last_used"] < max_age):
                continue
            
            # Remove from cache
            if document_id in self.retrievers:
                del self.retrievers[document_id]
                print(f"Removed unused retriever for document {document_id}")
    
    def clear_cache(self):
        """Clear the retriever cache."""
        self.retrievers = {}
        self.retriever_stats = {}


# Create a global retriever manager
retriever_manager = MemvidRetrieverManager()


# Helper functions
def get_context_for_query(document_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
    """
    Get context from a document for a query.
    
    Args:
        document_id: The document ID
        query: The search query
        top_k: Maximum number of results to return
        
    Returns:
        List[RetrievalResult]: List of retrieval results
    """
    return retriever_manager.search(document_id, query, top_k)


def format_context_for_llm(results: List[RetrievalResult]) -> str:
    """
    Format retrieval results as context for the LLM.
    
    Args:
        results: List of retrieval results
        
    Returns:
        str: Formatted context
    """
    if not results:
        return "No relevant context found."
    
    formatted_context = ""
    for i, result in enumerate(results):
        formatted_context += f"[DOCUMENT {i+1}]\n{result.text}\n\n"
    
    return formatted_context.strip()
