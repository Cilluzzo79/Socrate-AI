"""
Query Engine for Document Q&A
Uses metadata JSON from memvid processing + sentence-transformers for retrieval
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ sentence-transformers available")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not available - using simple keyword matching")

# Import LLM client and content generators
from core.llm_client import generate_chat_response
from core.content_generators import (
    generate_quiz_prompt,
    generate_outline_prompt,
    generate_mindmap_prompt,
    generate_summary_prompt,
    generate_analysis_prompt
)


class SimpleQueryEngine:
    """
    Simple query engine using metadata JSON and embeddings
    """

    def __init__(self):
        """Initialize query engine (lazy load embedding model)"""
        self._model = None  # Lazy loaded
        self.model_name = 'all-MiniLM-L6-v2'

    @property
    def model(self):
        """Lazy load embedding model only when needed"""
        if not EMBEDDINGS_AVAILABLE:
            return None

        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")

        return self._model

    def load_document_metadata(self, metadata_source: str, is_r2_key: bool = False) -> Optional[Dict[str, Any]]:
        """
        Load document metadata from JSON file or R2

        Args:
            metadata_source: Path to metadata JSON file or R2 key
            is_r2_key: True if metadata_source is an R2 key, False if local path

        Returns:
            Metadata dict or None if error
        """
        try:
            if is_r2_key:
                # Download from R2
                from core.s3_storage import download_file
                logger.info(f"Downloading metadata from R2: {metadata_source}")

                metadata_bytes = download_file(metadata_source)
                if not metadata_bytes:
                    logger.error(f"Failed to download metadata from R2: {metadata_source}")
                    return None

                metadata = json.loads(metadata_bytes.decode('utf-8'))
            else:
                # Load from local file
                with open(metadata_source, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            logger.info(f"Loaded metadata: {metadata.get('chunks_count', 0)} chunks")
            return metadata

        except Exception as e:
            logger.error(f"Error loading metadata from {metadata_source}: {e}")
            return None

    def find_relevant_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find most relevant chunks using HYBRID SEARCH (semantic + keyword matching)

        Args:
            query: User query
            chunks: List of chunk dictionaries (may contain precomputed embeddings)
            top_k: Number of chunks to return

        Returns:
            List of most relevant chunks with scores (hybrid ranking)
        """

        if not chunks:
            return []

        # If embeddings not available, use pure keyword matching
        if not EMBEDDINGS_AVAILABLE or self.model is None:
            return self._keyword_matching(query, chunks, top_k)

        try:
            # STEP 1: Semantic search (embeddings)
            query_embedding = self.model.encode(query, convert_to_tensor=False)

            # Check if chunks have precomputed embeddings inline
            has_inline_embeddings = all('embedding' in chunk for chunk in chunks)

            if has_inline_embeddings:
                logger.info(f"Using precomputed inline embeddings for {len(chunks)} chunks")
                chunk_embeddings = np.array([chunk['embedding'] for chunk in chunks])
            else:
                logger.warning(f"No inline embeddings found, computing on-demand for {len(chunks)} chunks")
                chunk_texts = [chunk['text'] for chunk in chunks]
                chunk_embeddings = self.model.encode(chunk_texts, convert_to_tensor=False, show_progress_bar=True)

            # Calculate cosine similarity
            semantic_scores = np.dot(chunk_embeddings, query_embedding) / (
                np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )

            # STEP 2: Keyword matching (term frequency)
            keyword_scores = self._calculate_keyword_scores(query, chunks)

            # STEP 3: Hybrid combination (weighted average)
            # Normalize scores to [0, 1] range
            semantic_norm = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min() + 1e-10)
            keyword_norm = (keyword_scores - keyword_scores.min()) / (keyword_scores.max() - keyword_scores.min() + 1e-10)

            # Combine: 70% semantic, 30% keyword (prioritize semantic understanding)
            # BUT if keyword score is high (>0.8), boost it to catch exact matches
            hybrid_scores = np.zeros(len(chunks))
            for i in range(len(chunks)):
                if keyword_norm[i] > 0.8:
                    # Strong keyword match → boost keyword weight to 50%
                    hybrid_scores[i] = 0.5 * semantic_norm[i] + 0.5 * keyword_norm[i]
                else:
                    # Normal: 70% semantic, 30% keyword
                    hybrid_scores[i] = 0.7 * semantic_norm[i] + 0.3 * keyword_norm[i]

            # Get top-k indices
            top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]

            # Build results
            results = []
            for idx in top_indices:
                chunk = chunks[idx].copy()
                chunk['similarity_score'] = float(hybrid_scores[idx])
                chunk['semantic_score'] = float(semantic_scores[idx])
                chunk['keyword_score'] = float(keyword_scores[idx])
                results.append(chunk)

            logger.info(f"Hybrid search: {len(results)} chunks (semantic avg: {semantic_scores[top_indices].mean():.3f}, keyword avg: {keyword_scores[top_indices].mean():.3f})")
            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to keyword matching
            return self._keyword_matching(query, chunks, top_k)

    def _calculate_keyword_scores(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Calculate keyword-based scores for all chunks (TF-IDF-like)

        Args:
            query: User query
            chunks: List of chunks

        Returns:
            Array of keyword scores (one per chunk)
        """
        query_lower = query.lower()
        query_terms = [term for term in query_lower.split() if len(term) > 2]  # Filter stopwords

        scores = np.zeros(len(chunks))

        for i, chunk in enumerate(chunks):
            if 'text' not in chunk:
                continue

            text_lower = chunk['text'].lower()

            # Count term frequency for each query term
            score = 0
            for term in query_terms:
                # Exact term matches
                term_count = text_lower.count(term)
                score += term_count * 2  # Weight exact matches higher

                # Partial matches (term as substring)
                words = text_lower.split()
                for word in words:
                    if term in word and term != word:  # Substring but not exact
                        score += 0.5

            scores[i] = score

        return scores

    def _keyword_matching(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword-based chunk matching (fallback when embeddings unavailable)

        Args:
            query: User query
            chunks: List of chunks
            top_k: Number to return

        Returns:
            Top matching chunks
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score each chunk by keyword overlap
        scored_chunks = []
        for chunk in chunks:
            text_lower = chunk['text'].lower()
            chunk_words = set(text_lower.split())

            # Simple overlap score
            overlap = len(query_words & chunk_words)

            chunk_copy = chunk.copy()
            chunk_copy['similarity_score'] = overlap
            scored_chunks.append(chunk_copy)

        # Sort by score and return top-k
        scored_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)

        return scored_chunks[:top_k]

    def query_document(
        self,
        query: str,
        metadata_file: str = None,
        metadata_r2_key: str = None,
        embeddings_r2_key: str = None,
        faiss_r2_key: str = None,
        top_k: int = 3,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        user_tier: str = 'free',
        query_type: str = 'query',
        command_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query a document using RAG pipeline with support for specialized commands

        Args:
            query: User's question or command
            metadata_file: Path to document metadata JSON (local)
            metadata_r2_key: R2 key for metadata JSON (cloud)
            top_k: Number of chunks to retrieve
            max_tokens: Max tokens in LLM response
            temperature: LLM temperature
            user_tier: User subscription tier (affects limits)
            query_type: Type of query (query, quiz, summary, outline, mindmap, analyze)
            command_params: Additional parameters for specialized commands

        Returns:
            Dict with answer, sources, and metadata
        """
        command_params = command_params or {}

        # Adjust top_k and max_tokens based on tier AND query type
        tier_limits = {
            'free': {'query': 5, 'summary': 20, 'quiz': 30, 'outline': 30, 'mindmap': 20, 'analyze': 30},
            'pro': {'query': 10, 'summary': 50, 'quiz': 50, 'outline': 50, 'mindmap': 30, 'analyze': 100},
            'enterprise': {'query': 20, 'summary': 100, 'quiz': 100, 'outline': 100, 'mindmap': 50, 'analyze': 200}
        }

        tier_config = tier_limits.get(user_tier, tier_limits['free'])
        max_chunks = tier_config.get(query_type, tier_config['query'])
        top_k = min(top_k, max_chunks)

        # Increase max_tokens for structured outputs based on complexity
        if query_type in ['outline', 'mindmap']:
            # Outline and mindmap need more tokens for hierarchical structures
            max_tokens = 8192  # Premium: comprehensive structured outputs
        elif query_type in ['quiz', 'summary', 'analyze']:
            # Other tools need moderate token budget
            max_tokens = 6144  # Premium: detailed but not as complex as outlines

        logger.info(f"Processing {query_type} (tier: {user_tier}, top_k: {top_k}): {query[:100]}")

        # Load document metadata (prefer R2, fallback to local)
        if metadata_r2_key:
            metadata = self.load_document_metadata(metadata_r2_key, is_r2_key=True)
        elif metadata_file:
            metadata = self.load_document_metadata(metadata_file, is_r2_key=False)
        else:
            logger.error("No metadata source provided (neither R2 key nor local file)")
            return {
                'success': False,
                'answer': 'Configurazione documento non valida',
                'sources': [],
                'metadata': {'error': 'no_metadata_source'}
            }
        if not metadata:
            return {
                'success': False,
                'answer': 'Impossibile caricare i metadati del documento',
                'sources': [],
                'metadata': {'error': 'metadata_load_failed'}
            }

        # Get chunks
        chunks = metadata.get('chunks', [])
        if not chunks:
            return {
                'success': False,
                'answer': 'Documento senza contenuto processato',
                'sources': [],
                'metadata': {'error': 'no_chunks'}
            }

        # Find relevant chunks
        relevant_chunks = self.find_relevant_chunks(query, chunks, top_k)

        if not relevant_chunks:
            return {
                'success': False,
                'answer': 'Nessun contenuto rilevante trovato nel documento',
                'sources': [],
                'metadata': {'error': 'no_relevant_chunks'}
            }

        # Build context from relevant chunks
        context_parts = []
        sources = []

        for i, chunk in enumerate(relevant_chunks):
            chunk_metadata = chunk.get('metadata', {})
            page = chunk_metadata.get('page', '?')
            section = chunk_metadata.get('section', '?')

            context_parts.append(
                f"[Chunk {i+1} - Pagina {page}, Sezione {section}]\n{chunk['text']}\n"
            )

            sources.append({
                'chunk_index': chunk_metadata.get('index', i),
                'page': page,
                'section': section,
                'similarity_score': chunk.get('similarity_score', 0),
                'preview': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text']
            })

        context = "\n\n".join(context_parts)

        logger.info(f"Built context from {len(relevant_chunks)} chunks ({len(context)} chars)")

        # Generate specialized prompt based on command type
        final_query = query
        if query_type == 'quiz':
            final_query = generate_quiz_prompt(
                quiz_type=command_params.get('quiz_type', 'multiple_choice'),
                num_questions=command_params.get('num_questions', 10),
                difficulty=command_params.get('difficulty', 'medium'),
                focus_area=command_params.get('focus_area')
            )
        elif query_type == 'outline':
            final_query = generate_outline_prompt(
                outline_type=command_params.get('outline_type', 'hierarchical'),
                detail_level=command_params.get('detail_level', 'medium'),
                focus_area=command_params.get('focus_area')
            )
        elif query_type == 'mindmap':
            final_query = generate_mindmap_prompt(
                central_concept=command_params.get('central_concept'),
                depth_level=command_params.get('depth_level', 3),
                focus_area=command_params.get('focus_area')
            )
        elif query_type == 'summary':
            final_query = generate_summary_prompt(
                summary_type=command_params.get('summary_type', 'medium'),
                length=command_params.get('length', '3-5 paragrafi'),
                focus_area=command_params.get('focus_area')
            )
        elif query_type == 'analyze':
            final_query = generate_analysis_prompt(
                analysis_type=command_params.get('analysis_type', 'thematic'),
                focus_area=command_params.get('focus_area'),
                depth=command_params.get('depth', 'profonda')
            )

        # Call LLM
        try:
            llm_response = generate_chat_response(
                query=final_query,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature,
                document_metadata={
                    'file': metadata.get('file'),
                    'chunks_count': metadata.get('chunks_count'),
                    'sections_count': metadata.get('sections_count')
                }
            )

            # Extract usage info for cost tracking
            usage = llm_response.get('metadata', {}).get('usage', {})

            return {
                'success': True,
                'answer': llm_response.get('text', 'Errore nella generazione della risposta'),
                'sources': sources,
                'metadata': {
                    'chunks_retrieved': len(relevant_chunks),
                    'context_length': len(context),
                    'model': llm_response.get('metadata', {}).get('model', 'unknown'),
                    'input_tokens': usage.get('prompt_tokens', 0),
                    'output_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0),
                    'finish_reason': llm_response.get('metadata', {}).get('finish_reason')
                }
            }

        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return {
                'success': False,
                'answer': f'Errore nella generazione della risposta: {str(e)}',
                'sources': sources,
                'metadata': {
                    'error': str(e),
                    'chunks_retrieved': len(relevant_chunks)
                }
            }


# Create global instance
query_engine = SimpleQueryEngine()


# Helper function for easy use
def query_document(
    query: str,
    metadata_file: str,
    top_k: int = 3,
    user_tier: str = 'free',
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to query a document

    Args:
        query: User question
        metadata_file: Path to metadata JSON
        top_k: Number of chunks to retrieve
        user_tier: User subscription tier
        **kwargs: Additional parameters for query_document

    Returns:
        Query result dict
    """
    return query_engine.query_document(
        query=query,
        metadata_file=metadata_file,
        top_k=top_k,
        user_tier=user_tier,
        **kwargs
    )
