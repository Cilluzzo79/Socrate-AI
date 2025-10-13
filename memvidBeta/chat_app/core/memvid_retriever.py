"""
Fixed Memvid retrieval module with improved metadata handling.
This version ensures metadata from both the index and metadata files are properly used.
"""

from pathlib import Path
import sys
import time
import os
import json
import re
import random
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import document structure analyzer or use internal implementation
try:
    from document_structure import DocumentStructureAnalyzer, format_hierarchical_context
except ImportError:
    print("Warning: document_structure module not found, using internal implementations")
    
    class DocumentStructureAnalyzer:
        """Simplified document structure analyzer."""
        def __init__(self):
            self.header_patterns = [
                r'^#{1,6}\s+(.+)$',
                r'^(\d+\.)+\s+(.+)$',
                r'^(Chapter|Section|Part)\s+\d+[:\.\s]+(.+)$'
            ]
        
        def get_hierarchical_position(self, text: str, position: int) -> Dict[str, Any]:
            return {
                'page': 1,
                'path': [],
                'title': '',
                'level': 0
            }
        
        def analyze_structure(self, text: str) -> Dict[str, Any]:
            return {
                'headers': [],
                'hierarchy': [],
                'page_numbers': {},
                'sections': []
            }

    def format_hierarchical_context(chunk: Dict[str, Any]) -> str:
        """Simplified formatter for hierarchical context."""
        metadata = chunk.get('metadata', {})
        page = metadata.get('page', None)
        page_str = f"[Pagina {page}]" if page else ""
        return page_str

# Import configuration
from config.config import DEFAULT_TOP_K
from database.operations import get_document_by_id, update_document_access


@dataclass
class RetrievalResult:
    """Class to store the result of a retrieval operation."""
    text: str
    score: float
    source: Optional[str] = None
    meta_info: Dict[str, Any] = field(default_factory=dict)
    
    def get_title(self) -> str:
        """Get the title or section title from metadata."""
        if 'section_title' in self.meta_info:
            return self.meta_info['section_title']
        if 'title' in self.meta_info:
            return self.meta_info['title']
        if 'possible_title' in self.meta_info:
            return self.meta_info['possible_title']
        return "Section"
    
    def get_position_info(self) -> str:
        """Get position information from metadata."""
        if 'section_index' in self.meta_info and 'total_sections' in self.meta_info:
            return f"Section {self.meta_info['section_index'] + 1} of {self.meta_info['total_sections']}"
        if 'chunk_index' in self.meta_info:
            return f"Chunk {self.meta_info['chunk_index'] + 1}"
        return ""
    
    def get_path(self) -> str:
        """Get hierarchical path from metadata."""
        if 'path' in self.meta_info and isinstance(self.meta_info['path'], list):
            return " > ".join(self.meta_info['path'])
        return ""
    
    def get_document_title(self) -> str:
        """Get document title from metadata."""
        if 'document_title' in self.meta_info:
            return self.meta_info['document_title']
        return ""
    
    def get_page_number(self) -> Optional[int]:
        """
        Get the page number from which this chunk originates.
        Looks for page number in metadata and text.
        """
        # Check metadata first
        if 'page' in self.meta_info:
            return self.meta_info['page']
        
        # Check for page markers in text
        page_patterns = [
            r'## Pagina (\d+)',
            r'Page\s+(\d+)',
            r'Pagina\s+(\d+)',
            r'p\.\s*(\d+)',
            r'\bp\s*(\d+)\b',
            r'-\s*(\d+)\s*-'
        ]
        
        for pattern in page_patterns:
            match = re.search(pattern, self.text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass
                
        # Check title for page numbers
        if 'title' in self.meta_info and isinstance(self.meta_info['title'], str):
            for pattern in page_patterns:
                match = re.search(pattern, self.meta_info['title'])
                if match:
                    try:
                        return int(match.group(1))
                    except (ValueError, IndexError):
                        pass
        
        return None


class MemvidRetrieverManager:
    """
    Class to manage Memvid retrievers for different documents.
    Handles caching, metadata enhancement, and retrieval operations.
    """
    
    def __init__(self):
        self.retrievers = {}
        self.retriever_stats = {}
        self.metadata_cache = {}  # Cache for structured metadata
        self.structure_analyzer = DocumentStructureAnalyzer()  # Document structure analyzer
        self.debug = True  # Enable debug logging
    
    def log_debug(self, message: str) -> None:
        """Log debug message if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def get_retriever(self, document_id: str) -> Optional['MemvidRetriever']:
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
            self.log_debug(f"Using cached retriever for document {document_id}")
            return self.retrievers[document_id]
        
        # Get document from database
        document = get_document_by_id(document_id)
        if not document:
            self.log_debug(f"Document {document_id} not found in database")
            return None
        
        # Update document access time
        update_document_access(document_id)
        
        # Create new retriever
        try:
            from memvid import MemvidRetriever
            
            self.log_debug(f"Creating new retriever for document {document_id}")
            self.log_debug(f"Video path: {document.video_path}")
            self.log_debug(f"Index path: {document.index_path}")
            
            retriever = MemvidRetriever(document.video_path, document.index_path)
            self.retrievers[document_id] = retriever
            
            # Initialize stats
            self.retriever_stats[document_id] = {
                "created_at": time.time(),
                "last_used": time.time(),
                "use_count": 1
            }
            
            # Load metadata if available
            self._load_metadata(document_id, document)
            
            return retriever
        except Exception as e:
            self.log_debug(f"Error creating retriever for document {document_id}: {str(e)}")
            return None
    
    def _load_metadata(self, document_id: str, document) -> None:
        """
        Load structured metadata for a document if available.
        
        Args:
            document_id: The document ID
            document: The document object
        """
        # Skip if already loaded
        if document_id in self.metadata_cache:
            self.log_debug(f"Metadata for document {document_id} already loaded")
            return
        
        try:
            # Get video path and directory
            video_path = document.video_path
            video_dir = os.path.dirname(video_path)
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            
            # Log paths for debugging
            self.log_debug(f"Looking for metadata files for document {document_id}")
            self.log_debug(f"Video directory: {video_dir}")
            self.log_debug(f"Base name: {base_name}")
            
            # Define possible metadata file paths
            potential_metadata_files = [
                os.path.join(video_dir, f"{base_name}_metadata.json"),
                os.path.join(video_dir, f"{base_name}_sections_metadata.json"),
                os.path.join(video_dir, f"{base_name}_structure.json"),
                os.path.join(video_dir, f"{base_name}_simple_structure.json"),
                os.path.join(video_dir, f"{base_name}_light_metadata.json"),
                os.path.join(video_dir, f"{base_name}_smart_metadata.json"),
                os.path.join(video_dir, f"{base_name}_debug_metadata.json")
            ]
            
            metadata_loaded = False
            
            # Try to load each potential metadata file
            for metadata_file in potential_metadata_files:
                if os.path.exists(metadata_file):
                    self.log_debug(f"Found metadata file: {metadata_file}")
                    
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        self.metadata_cache[document_id] = json.load(f)
                        self.log_debug(f"Loaded metadata from {metadata_file}")
                        
                        # If this is a chunks-based metadata file, analyze structure
                        if 'chunks' in self.metadata_cache[document_id]:
                            self.log_debug(f"Analyzing document structure from chunks (count: {len(self.metadata_cache[document_id]['chunks'])})")
                            self._analyze_document_structure(document_id)
                        
                        metadata_loaded = True
                        break
            
            # Try to load the index file if no metadata file was found
            if not metadata_loaded:
                index_file = os.path.join(video_dir, f"{base_name}_index.json")
                if os.path.exists(index_file):
                    self.log_debug(f"No dedicated metadata file found, trying index file: {index_file}")
                    
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                        
                        # Check if the index file has metadata
                        if 'metadata' in index_data and isinstance(index_data['metadata'], list):
                            self.log_debug(f"Found metadata in index file (count: {len(index_data['metadata'])})")
                            
                            # Create a metadata structure from the index file
                            self.metadata_cache[document_id] = {
                                'chunks': []
                            }
                            
                            # Get documents if available
                            documents = index_data.get('documents', [])
                            
                            # Create chunks from metadata and documents
                            for i, metadata_item in enumerate(index_data['metadata']):
                                text = documents[i]['text'] if i < len(documents) else ""
                                
                                chunk = {
                                    'text': text,
                                    'metadata': metadata_item
                                }
                                
                                self.metadata_cache[document_id]['chunks'].append(chunk)
                            
                            self.log_debug(f"Created metadata from index file with {len(self.metadata_cache[document_id]['chunks'])} chunks")
                            metadata_loaded = True
            
            if metadata_loaded:
                self.log_debug(f"Successfully loaded metadata for document {document_id}")
            else:
                self.log_debug(f"No metadata files found for document {document_id}")
        
        except Exception as e:
            self.log_debug(f"Error loading metadata for document {document_id}: {str(e)}")
            # Continue without metadata
    
    def _analyze_document_structure(self, document_id: str) -> None:
        """
        Analyze document structure from metadata if available.
        
        Args:
            document_id: The document ID
        """
        if document_id not in self.metadata_cache or 'chunks' not in self.metadata_cache[document_id]:
            self.log_debug(f"No chunks found for document {document_id}")
            return
        
        try:
            # Extract full text from chunks
            chunks = self.metadata_cache[document_id]['chunks']
            
            # Pre-analysis check
            self.log_debug(f"Starting structure analysis with {len(chunks)} chunks")
            
            # Check if chunks already have structural metadata
            has_page_info = False
            has_section_info = False
            
            for chunk in chunks[:20]:  # Check a sample of chunks
                if 'metadata' in chunk:
                    if 'page' in chunk['metadata']:
                        has_page_info = True
                    if 'section' in chunk['metadata'] and 'total_sections' in chunk['metadata']:
                        has_section_info = True
            
            # If chunks already have good metadata, skip full analysis
            if has_page_info and has_section_info:
                self.log_debug(f"Chunks already have good structural metadata, skipping full analysis")
                return
                
            # Sort chunks by start position if available
            if all('metadata' in chunk and 'start' in chunk['metadata'] for chunk in chunks):
                chunks = sorted(chunks, key=lambda c: c['metadata']['start'])
                self.log_debug(f"Sorted chunks by start position")
            
            # Perform page number extraction on all chunks
            page_info_count = 0
            max_page = 0
            
            for chunk in chunks:
                if 'text' in chunk:
                    text = chunk['text']
                    
                    # Check for page markers in the text
                    page_patterns = [
                        r'## Pagina (\d+)',
                        r'Page\s+(\d+)',
                        r'Pagina\s+(\d+)'
                    ]
                    
                    for pattern in page_patterns:
                        match = re.search(pattern, text)
                        if match:
                            try:
                                page_num = int(match.group(1))
                                
                                # Add page to metadata if not already present
                                if 'metadata' not in chunk:
                                    chunk['metadata'] = {}
                                if 'page' not in chunk['metadata']:
                                    chunk['metadata']['page'] = page_num
                                    page_info_count += 1
                                    max_page = max(max_page, page_num)
                                    
                                break
                            except (ValueError, IndexError):
                                pass
            
            self.log_debug(f"Found page information for {page_info_count} chunks, max page: {max_page}")
            
            # Only do full structure analysis if really needed
            full_text = ""
            
            # Concatenate all chunk texts
            for chunk in chunks:
                if 'text' in chunk:
                    full_text += chunk['text'] + "\n\n"
            
            # Analyze structure if needed
            if full_text and not has_section_info:
                self.log_debug(f"Analyzing full document structure")
                structure = self.structure_analyzer.analyze_structure(full_text)
                self.metadata_cache[document_id]['structure'] = structure
                self.log_debug(f"Document structure analysis complete: {len(structure.get('hierarchy', []))} structural elements found")
        
        except Exception as e:
            self.log_debug(f"Error analyzing document structure: {str(e)}")
    
    def _enhance_results_with_metadata(self, document_id: str, results: List[Any]) -> List[RetrievalResult]:
        """
        Enhance search results with structured metadata.
        
        Args:
            document_id: The document ID
            results: Original search results
            
        Returns:
            List[RetrievalResult]: Enhanced retrieval results
        """
        enhanced_results = []
        
        # Get metadata if available
        metadata = self.metadata_cache.get(document_id)
        if not metadata:
            self.log_debug(f"No metadata available for document {document_id}")
        else:
            self.log_debug(f"Enhancing results with metadata for document {document_id}")
        
        # Function to find matching chunk in metadata
        def find_matching_chunk(text: str):
            if not metadata or 'chunks' not in metadata:
                return None
            
            # Try exact match first
            for chunk in metadata['chunks']:
                if 'text' in chunk and chunk['text'] == text:
                    return chunk
            
            # If no exact match, try to find the most similar chunk
            max_similarity = 0
            best_match = None
            
            # Function to compute simple similarity
            def simple_similarity(text1, text2, min_length=50):
                if len(text1) < min_length or len(text2) < min_length:
                    # For short texts, use character set overlap
                    return len(set(text1) & set(text2)) / max(len(set(text1)), len(set(text2)))
                else:
                    # For longer texts, check if one contains the other
                    if text1 in text2 or text2 in text1:
                        return 0.9  # High similarity for containment
                    
                    # Check for word overlap
                    words1 = set(text1.lower().split())
                    words2 = set(text2.lower().split())
                    
                    if len(words1) == 0 or len(words2) == 0:
                        return 0
                    
                    return len(words1 & words2) / max(len(words1), len(words2))
            
            # First try exact beginning match (often chunks differ only at the end)
            for chunk in metadata['chunks']:
                if 'text' not in chunk:
                    continue
                
                chunk_text = chunk['text']
                
                # Check if one is the beginning of the other (with 10% margin)
                min_length = min(len(text), len(chunk_text))
                check_length = int(min_length * 0.9)
                
                if check_length > 50:
                    if text[:check_length] == chunk_text[:check_length]:
                        self.log_debug(f"Found chunk with matching beginning")
                        return chunk
            
            # If no beginning match, try similarity
            for chunk in metadata['chunks']:
                if 'text' not in chunk:
                    continue
                
                chunk_text = chunk['text']
                similarity = simple_similarity(text, chunk_text)
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = chunk
            
            # Only return if similarity is high enough
            threshold = 0.5  # Lower threshold for better matching
            if max_similarity > threshold:
                self.log_debug(f"Found similar chunk with similarity {max_similarity:.2f}")
                return best_match
            
            self.log_debug(f"No matching chunk found, best similarity: {max_similarity:.2f}")
            return None
        
        # Process each result
        for result in results:
            # Handle different types of results
            if isinstance(result, str):
                # If result is a string, use it directly as text with a default score
                text = result
                score = 1.0
                meta_info = {}
                
                # Try to find matching chunk in metadata
                if metadata:
                    matching_chunk = find_matching_chunk(text)
                    if matching_chunk and 'metadata' in matching_chunk:
                        meta_info = matching_chunk['metadata']
                        self.log_debug(f"Found metadata for string result")
                
                retrieval_result = RetrievalResult(
                    text=text,
                    score=score,
                    meta_info=meta_info
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
                    
                    # Start with metadata from result if available
                    meta_info = {}
                    
                    # Check for metadata directly on the result object
                    if hasattr(result, "metadata"):
                        self.log_debug(f"Result object has metadata attribute")
                        meta_info = result.metadata
                    
                    # Try to enhance with structured metadata from our cache
                    if metadata and (not meta_info or len(meta_info) == 0):
                        matching_chunk = find_matching_chunk(text)
                        if matching_chunk and 'metadata' in matching_chunk:
                            self.log_debug(f"Enhanced result with metadata from matching chunk")
                            meta_info = matching_chunk['metadata']
                    
                    # Check if we have structure info to enhance metadata
                    if metadata and 'structure' in metadata and 'page' not in meta_info:
                        # Get hierarchical position
                        if 'chunks' in metadata:
                            chunks = metadata['chunks']
                            full_text = ""
                            
                            # Concatenate all chunk texts
                            for chunk in chunks:
                                if 'text' in chunk:
                                    full_text += chunk['text'] + "\n\n"
                            
                            # Find position of the current text in the full text
                            start_pos = full_text.find(text)
                            
                            if start_pos != -1:
                                # Get hierarchical position
                                position_info = self.structure_analyzer.get_hierarchical_position(full_text, start_pos)
                                
                                # Enhance metadata
                                meta_info.update({
                                    'page': position_info.get('page', 1),
                                    'path': position_info.get('path', []),
                                    'title': position_info.get('title', ''),
                                    'level': position_info.get('level', 0),
                                    'section_title': position_info.get('title', '')
                                })
                                
                                self.log_debug(f"Added hierarchical position information to result")
                    
                    # Extract page information from text if not in metadata
                    if 'page' not in meta_info:
                        page_patterns = [
                            r'## Pagina (\d+)',
                            r'Page\s+(\d+)',
                            r'Pagina\s+(\d+)'
                        ]
                        
                        for pattern in page_patterns:
                            match = re.search(pattern, text)
                            if match:
                                try:
                                    page_num = int(match.group(1))
                                    meta_info['page'] = page_num
                                    self.log_debug(f"Extracted page {page_num} from text")
                                    break
                                except (ValueError, IndexError):
                                    pass
                    
                    # Create the retrieval result
                    retrieval_result = RetrievalResult(
                        text=text,
                        score=score,
                        meta_info=meta_info
                    )
                    
                    # Add source if available
                    if hasattr(result, "source"):
                        retrieval_result.source = result.source
                    
                except Exception as e:
                    self.log_debug(f"Error processing result: {str(e)}")
                    # Use string representation as fallback
                    retrieval_result = RetrievalResult(
                        text=str(result),
                        score=1.0
                    )
            
            enhanced_results.append(retrieval_result)
        
        # Log the enhancement results
        self.log_debug(f"Enhanced {len(enhanced_results)} results with metadata")
        for i, result in enumerate(enhanced_results):
            meta_keys = list(result.meta_info.keys())
            self.log_debug(f"Result {i+1} metadata keys: {meta_keys}")
        
        return enhanced_results
    
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
            self.log_debug(f"Retriever not found for document {document_id}")
            return []
        
        try:
            # Search using the retriever
            self.log_debug(f"Searching document {document_id} for query: '{query}' with top_k={top_k}")
            results = retriever.search(query, top_k=top_k)
            self.log_debug(f"Found {len(results)} results for query")
            
            # Enhance results with metadata
            retrieval_results = self._enhance_results_with_metadata(document_id, results)
            
            return retrieval_results
        except Exception as e:
            self.log_debug(f"Error searching document {document_id}: {str(e)}")
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
                self.log_debug(f"Removed retriever for document {document_id} from cache")
            
            if document_id in self.retriever_stats:
                del self.retriever_stats[document_id]
            
            if document_id in self.metadata_cache:
                del self.metadata_cache[document_id]


# Singleton instance of the retriever manager
_retriever_manager = None

def get_retriever_manager() -> MemvidRetrieverManager:
    """
    Get the singleton instance of the retriever manager.
    
    Returns:
        MemvidRetrieverManager: The retriever manager
    """
    global _retriever_manager
    if _retriever_manager is None:
        _retriever_manager = MemvidRetrieverManager()
    return _retriever_manager


def get_context_for_query(document_id: str, query: str, top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
    """
    Get context for a query from a document.
    
    Args:
        document_id: The document ID
        query: The search query
        top_k: Maximum number of results to return
        
    Returns:
        List[RetrievalResult]: List of retrieval results
    """
    manager = get_retriever_manager()
    
    # Clean up unused retrievers periodically
    if (manager.retriever_stats and 
        len(manager.retrievers) > 5 and 
        random.random() < 0.1):  # 10% chance
        manager.cleanup_unused_retrievers()
    
    return manager.search(document_id, query, top_k)


def format_context_for_llm(results: List[RetrievalResult]) -> str:
    """
    Format retrieval results into a context string for the LLM.
    
    Args:
        results: List of retrieval results
        
    Returns:
        str: Formatted context
    """
    if not results:
        return ""
    
    context_parts = []
    
    for i, result in enumerate(results):
        # Create hierarchical context header
        header_parts = []
        
        # Add page information if available
        page_num = result.get_page_number()
        if page_num:
            header_parts.append(f"Pagina {page_num}")
        
        # Add section title if available
        section_title = result.get_title()
        if section_title and section_title != "Section":
            header_parts.append(f"Sezione: {section_title}")
        
        # Add path if available
        path = result.get_path()
        if path:
            header_parts.append(f"Percorso: {path}")
        
        # Create header string
        header = ""
        if header_parts:
            header = "[" + "] [".join(header_parts) + "]"
        
        # Format text with header
        section_text = f"{header}\n\n{result.text}" if header else result.text
        context_parts.append(section_text)
    
    return "\n\n---\n\n".join(context_parts)
