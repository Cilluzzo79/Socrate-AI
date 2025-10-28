"""
Cost-Optimized Reranker with Diversity Filter
Reduces chunks to LLM by 85-90% while maintaining high recall
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import cross-encoder for advanced reranking
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("CrossEncoder not available, using lightweight reranking")


class CostOptimizedReranker:
    """
    Two-stage reranker with diversity filtering for cost optimization

    Stage 1: Semantic reranking (relevance scoring)
    Stage 2: Diversity filtering (avoid redundant chunks)

    Result: Top-k chunks that are BOTH relevant AND diverse
    """

    def __init__(self, use_cross_encoder: bool = True):
        """
        Initialize reranker

        Args:
            use_cross_encoder: Use CrossEncoder for better relevance (requires more memory)
                              If False, uses lightweight semantic similarity
        """
        self._cross_encoder = None
        self.use_cross_encoder = use_cross_encoder and CROSS_ENCODER_AVAILABLE

        if self.use_cross_encoder:
            logger.info("Initializing CrossEncoder reranker (advanced mode)")
        else:
            logger.info("Using lightweight reranker (memory efficient)")

    def _is_recipe_query(self, query: str) -> bool:
        """
        Detect if query is asking for a recipe.

        RECIPE FIX: Recipe queries need lower diversity threshold to capture both title and content.

        Args:
            query: User query string

        Returns:
            True if query appears to be asking for a recipe
        """
        recipe_keywords = [
            'ricetta', 'ricette', 'preparano', 'prepara', 'preparare', 'preparazione',
            'ingredienti', 'cucinare', 'cucina', 'cucinato', 'cucinati',
            'come si fa', 'come si prepara', 'come fare'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in recipe_keywords)

    @property
    def cross_encoder(self):
        """Lazy load cross-encoder model"""
        if self.use_cross_encoder and self._cross_encoder is None:
            try:
                # Multilingual cross-encoder for Italian content
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("CrossEncoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder: {e}, falling back to lightweight")
                self.use_cross_encoder = False
        return self._cross_encoder

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 12,
        diversity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks with diversity filtering (MAIN METHOD)

        Args:
            query: User query
            chunks: Candidate chunks from retrieval stage
            top_k: Number of final chunks to return
            diversity_threshold: Cosine similarity threshold for diversity
                               Higher = more diverse (0.85 recommended)
                               RECIPE FIX: Automatically lowered to 0.70 for recipe queries

        Returns:
            Top-k chunks that are relevant AND diverse
        """

        if not chunks:
            return []

        if len(chunks) <= top_k:
            # Not enough chunks to filter, return all
            logger.info(f"Only {len(chunks)} chunks, returning all (no reranking needed)")
            return chunks

        # RECIPE FIX: Lower diversity threshold for recipe queries
        is_recipe = self._is_recipe_query(query)
        if is_recipe:
            original_threshold = diversity_threshold
            diversity_threshold = 0.70  # Lower threshold to allow similar title+content chunks
            logger.info(f"[RECIPE MODE] Lowered diversity threshold: {original_threshold} → {diversity_threshold} (capture title + full content)")

        logger.info(f"[RERANKING] Starting: {len(chunks)} candidates → {top_k} final (diversity: {diversity_threshold})")

        # STAGE 1: Semantic reranking (relevance)
        if self.use_cross_encoder:
            reranked_chunks = self._rerank_with_cross_encoder(query, chunks)
        else:
            reranked_chunks = self._rerank_with_scores(query, chunks)

        logger.info(f"[RERANKING] Stage 1 complete: scored {len(reranked_chunks)} chunks")

        # STAGE 2: Diversity filtering
        final_chunks = self._apply_diversity_filter(
            chunks=reranked_chunks,
            top_k=top_k,
            diversity_threshold=diversity_threshold
        )

        logger.info(f"[RERANKING] Stage 2 complete: selected {len(final_chunks)} diverse chunks")

        return final_chunks

    def _rerank_with_cross_encoder(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Advanced reranking using CrossEncoder (better accuracy)
        """
        try:
            # Prepare (query, chunk_text) pairs
            pairs = [(query, chunk['text']) for chunk in chunks]

            # Score with cross-encoder
            scores = self.cross_encoder.predict(pairs)

            # Add rerank scores to chunks
            for i, chunk in enumerate(chunks):
                chunk['rerank_score'] = float(scores[i])

            # Sort by rerank score (descending)
            reranked = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)

            logger.info(f"CrossEncoder reranking: best score={reranked[0]['rerank_score']:.3f}, worst={reranked[-1]['rerank_score']:.3f}")

            return reranked

        except Exception as e:
            logger.error(f"CrossEncoder reranking failed: {e}, falling back to similarity scores")
            return self._rerank_with_scores(query, chunks)

    def _rerank_with_scores(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Lightweight reranking using existing similarity scores + keyword boost
        """

        # Use existing similarity_score (from retrieval stage)
        # Add keyword boost for proper nouns and exact matches

        query_lower = query.lower()
        query_terms = set(query_lower.split())

        for chunk in chunks:
            # Get base similarity score
            base_score = chunk.get('similarity_score', 0.5)

            # Calculate keyword boost
            text_lower = chunk['text'].lower()
            text_words = set(text_lower.split())

            # Exact query match bonus
            if query_lower in text_lower:
                keyword_boost = 0.15
            else:
                # Term overlap bonus
                overlap = len(query_terms & text_words)
                keyword_boost = min(0.10, overlap * 0.02)

            # Combined rerank score
            chunk['rerank_score'] = base_score + keyword_boost

        # Sort by rerank score
        reranked = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)

        return reranked

    def _apply_diversity_filter(
        self,
        chunks: List[Dict[str, Any]],
        top_k: int,
        diversity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity filtering to avoid redundant chunks

        Algorithm:
        1. Take top chunk (highest rerank score)
        2. For next chunks, check similarity with already selected
        3. Add chunk only if it's sufficiently different (< diversity_threshold)
        4. Continue until we have top_k chunks

        This ensures we capture:
        - Titles + full content
        - Different sections of same topic
        - Complementary information

        Without capturing:
        - Near-duplicate content
        - Repeated information
        """

        if not chunks:
            return []

        # Check if chunks have embeddings for diversity calculation
        has_embeddings = all('embedding' in chunk for chunk in chunks)

        if not has_embeddings:
            logger.warning("Chunks don't have embeddings, using text-based diversity")
            return self._text_based_diversity(chunks, top_k, diversity_threshold)

        selected = []

        for chunk in chunks:
            if len(selected) >= top_k:
                break

            if len(selected) == 0:
                # Always take the top chunk
                selected.append(chunk)
                continue

            # Check similarity with already selected chunks
            chunk_embedding = np.array(chunk['embedding'])

            max_similarity = 0.0
            for selected_chunk in selected:
                selected_embedding = np.array(selected_chunk['embedding'])

                # Cosine similarity
                similarity = np.dot(chunk_embedding, selected_embedding) / (
                    np.linalg.norm(chunk_embedding) * np.linalg.norm(selected_embedding)
                )

                max_similarity = max(max_similarity, similarity)

            # Add chunk if sufficiently diverse
            if max_similarity < diversity_threshold:
                selected.append(chunk)
                logger.debug(f"Added chunk (diversity: {1-max_similarity:.3f})")
            else:
                logger.debug(f"Skipped redundant chunk (similarity: {max_similarity:.3f} >= {diversity_threshold})")

        # If we couldn't get enough diverse chunks, fill remaining with top scored ones
        if len(selected) < top_k:
            remaining = top_k - len(selected)
            logger.warning(f"Only {len(selected)} diverse chunks found, adding {remaining} more by score")

            selected_indices = {id(c) for c in selected}
            for chunk in chunks:
                if id(chunk) not in selected_indices:
                    selected.append(chunk)
                    if len(selected) >= top_k:
                        break

        return selected

    def _text_based_diversity(
        self,
        chunks: List[Dict[str, Any]],
        top_k: int,
        diversity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Fallback diversity filter using text overlap (when embeddings unavailable)
        """
        selected = []

        for chunk in chunks:
            if len(selected) >= top_k:
                break

            if len(selected) == 0:
                selected.append(chunk)
                continue

            # Calculate word overlap with selected chunks
            chunk_words = set(chunk['text'].lower().split())

            max_overlap = 0.0
            for selected_chunk in selected:
                selected_words = set(selected_chunk['text'].lower().split())

                # Jaccard similarity
                intersection = len(chunk_words & selected_words)
                union = len(chunk_words | selected_words)
                overlap = intersection / union if union > 0 else 0

                max_overlap = max(max_overlap, overlap)

            # Add if sufficiently diverse (lower threshold for text-based)
            if max_overlap < (diversity_threshold - 0.1):  # More lenient
                selected.append(chunk)

        # Fill remaining
        if len(selected) < top_k:
            selected_ids = {id(c) for c in selected}
            for chunk in chunks:
                if id(chunk) not in selected_ids:
                    selected.append(chunk)
                    if len(selected) >= top_k:
                        break

        return selected


# Singleton instance
_reranker_instance = None


def get_reranker(use_cross_encoder: bool = True) -> CostOptimizedReranker:
    """
    Get singleton reranker instance

    Args:
        use_cross_encoder: Use CrossEncoder (better accuracy, more memory)

    Returns:
        CostOptimizedReranker instance
    """
    global _reranker_instance

    if _reranker_instance is None:
        _reranker_instance = CostOptimizedReranker(use_cross_encoder=use_cross_encoder)

    return _reranker_instance


# Convenience function for direct use
def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 12,
    diversity_threshold: float = 0.85,
    use_cross_encoder: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function for reranking chunks

    Args:
        query: User query
        chunks: Candidate chunks
        top_k: Number of final chunks
        diversity_threshold: Diversity threshold (0.85 recommended)
        use_cross_encoder: Use advanced reranking

    Returns:
        Top-k reranked and diverse chunks
    """
    reranker = get_reranker(use_cross_encoder=use_cross_encoder)
    return reranker.rerank(query, chunks, top_k, diversity_threshold)
