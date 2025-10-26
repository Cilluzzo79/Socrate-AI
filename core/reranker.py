"""
Reranker module for improving retrieval precision in RAG pipeline.

Uses cross-encoder models to re-score chunks based on query relevance.
Implements two-stage retrieval: vector search (high recall) + reranking (high precision).

Architecture:
    Stage 1: Vector search retrieves top_k candidates (broad net, ~50-100 chunks)
    Stage 2: Reranker scores each candidate vs query (select best ~10 chunks)

Benefits:
    - Higher recall (retrieve more candidates initially)
    - Higher precision (filter to most relevant chunks)
    - Lower LLM costs (fewer chunks passed to LLM)
    - Better answer quality (cleanest context)
"""

from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

# Lazy import to avoid loading sentence_transformers at module import time
_CrossEncoder = None

def _get_cross_encoder():
    """Lazy load CrossEncoder to avoid import overhead"""
    global _CrossEncoder
    if _CrossEncoder is None:
        try:
            from sentence_transformers import CrossEncoder as CE
            _CrossEncoder = CE
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
    return _CrossEncoder


class DocumentReranker:
    """
    Two-stage retrieval with cross-encoder reranking.

    The reranker uses a cross-encoder model that reads both query and document together
    to produce a relevance score. This is more accurate than comparing embeddings alone.

    Default model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
    - Multilingual (supports Italian)
    - 384 dimensions
    - ~500 MB download size
    - Good balance of speed/accuracy
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize reranker with cross-encoder model.

        Args:
            model_name: HuggingFace model ID for cross-encoder.
                       If None, uses env var RERANKER_MODEL or default.
        """
        # Get model name from env or use default
        self.model_name = model_name or os.getenv(
            'RERANKER_MODEL',
            'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1'
        )

        logger.info(f"[RERANKER] Initializing with model: {self.model_name}")

        try:
            CrossEncoder = _get_cross_encoder()
            self.model = CrossEncoder(self.model_name)
            logger.info("[RERANKER] Model loaded successfully")
        except Exception as e:
            logger.error(f"[RERANKER] Failed to load model: {e}")
            raise

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 10,
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks based on relevance to query.

        Args:
            query: User query string
            chunks: List of chunk dictionaries (must have 'text' key)
            top_k: Number of top chunks to return after reranking
            batch_size: Batch size for reranker inference (larger = faster but more RAM)

        Returns:
            List of top_k chunks, sorted by relevance score (highest first)
            Each chunk dict gets an additional 'rerank_score' key
        """
        if not chunks:
            logger.warning("[RERANKER] No chunks provided, returning empty list")
            return []

        # If fewer chunks than top_k, return all without reranking
        if len(chunks) <= top_k:
            logger.info(f"[RERANKER] {len(chunks)} chunks <= top_k={top_k}, returning all")
            return chunks

        logger.info(f"[RERANKER] Reranking {len(chunks)} chunks → selecting top {top_k}")

        try:
            # Prepare pairs: [query, chunk_text]
            pairs = [[query, chunk['text']] for chunk in chunks]

            # Get relevance scores from cross-encoder
            # Returns numpy array of scores
            scores = self.model.predict(
                pairs,
                batch_size=batch_size,
                show_progress_bar=False  # Disable progress bar for production
            )

            # Add scores to chunks for debugging
            for i, chunk in enumerate(chunks):
                chunk['rerank_score'] = float(scores[i])

            # Sort chunks by score (descending)
            import numpy as np
            ranked_indices = np.argsort(scores)[::-1]

            # Select top_k
            reranked_chunks = [chunks[i] for i in ranked_indices[:top_k]]

            # Log scores for debugging
            top_scores = [float(scores[i]) for i in ranked_indices[:top_k]]
            min_score = min(top_scores)
            max_score = max(top_scores)
            avg_score = sum(top_scores) / len(top_scores)

            logger.info(
                f"[RERANKER] Top {top_k} scores: "
                f"min={min_score:.3f}, max={max_score:.3f}, avg={avg_score:.3f}"
            )
            logger.debug(f"[RERANKER] All top scores: {[f'{s:.3f}' for s in top_scores]}")

            return reranked_chunks

        except Exception as e:
            logger.error(f"[RERANKER] Error during reranking: {e}", exc_info=True)
            # Fallback: return original top_k chunks without reranking
            logger.warning(f"[RERANKER] Fallback: returning first {top_k} chunks")
            return chunks[:top_k]


# Global singleton instance (lazy loading)
_reranker_instance: Optional[DocumentReranker] = None

def get_reranker() -> DocumentReranker:
    """
    Get singleton reranker instance.

    Uses lazy loading to avoid loading model at import time.
    The model is only loaded when first needed.

    Returns:
        DocumentReranker instance
    """
    global _reranker_instance
    if _reranker_instance is None:
        logger.info("[RERANKER] Creating singleton instance")
        _reranker_instance = DocumentReranker()
    return _reranker_instance


def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Convenience function for reranking chunks.

    Args:
        query: User query
        chunks: List of candidate chunks
        top_k: Number of chunks to return

    Returns:
        Reranked chunks (top_k best)
    """
    reranker = get_reranker()
    return reranker.rerank(query, chunks, top_k)
