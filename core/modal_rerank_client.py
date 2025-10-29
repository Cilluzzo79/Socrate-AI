"""
Modal Labs GPU Reranker Client

HTTP client for calling Modal GPU reranking service from Railway.
Provides robust error handling, timeouts, and fallback logic.

Usage:
    from core.modal_rerank_client import rerank_with_modal

    reranked_chunks = rerank_with_modal(query, chunks, top_k=10)
    if reranked_chunks is None:
        # Fallback to dense-only or local reranker
        pass
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional, Tuple
import time

logger = logging.getLogger(__name__)

# Modal endpoint URL from environment
MODAL_RERANK_URL = os.getenv("MODAL_RERANK_URL")

# Configuration
DEFAULT_TIMEOUT = 30.0  # 30 seconds timeout (allow cold starts for GPU model loading)
MAX_CHUNKS_PER_REQUEST = 100  # Modal service limit
DEFAULT_TOP_K = 10

# Log timeout at module load for debugging deployments
import logging
_logger = logging.getLogger(__name__)
_logger.info(f"[MODAL-CLIENT-INIT] DEFAULT_TIMEOUT = {DEFAULT_TIMEOUT}s (commit d0655f6+)")


def is_modal_enabled() -> bool:
    """Check if Modal GPU reranking is enabled."""
    return bool(MODAL_RERANK_URL)


def rerank_with_modal(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
    timeout: float = DEFAULT_TIMEOUT
) -> Optional[List[Dict[str, Any]]]:
    """
    Rerank chunks using Modal GPU service.

    Args:
        query: User query text
        chunks: List of chunk dictionaries with 'text' field
        top_k: Number of top chunks to return after reranking
        timeout: Request timeout in seconds (default 2.0s)

    Returns:
        Reranked chunks (top_k) or None if failed

    Example:
        >>> chunks = [{"text": "chunk1", "chunk_id": 1}, ...]
        >>> reranked = rerank_with_modal("query", chunks, top_k=10)
        >>> if reranked is None:
        ...     # Use fallback strategy
        ...     reranked = chunks[:10]
    """
    if not MODAL_RERANK_URL:
        logger.debug("[MODAL] No MODAL_RERANK_URL configured, skipping GPU reranking")
        return None

    if not chunks:
        logger.warning("[MODAL] No chunks provided, skipping reranking")
        return []

    if len(chunks) > MAX_CHUNKS_PER_REQUEST:
        logger.warning(f"[MODAL] Too many chunks ({len(chunks)}), truncating to {MAX_CHUNKS_PER_REQUEST}")
        chunks = chunks[:MAX_CHUNKS_PER_REQUEST]

    try:
        start_time = time.time()

        # Extract chunk texts
        chunk_texts = [chunk.get("text", "") for chunk in chunks]

        logger.info(f"[MODAL] Calling Modal API with {len(chunk_texts)} chunks")

        # Call Modal API
        response = requests.post(
            MODAL_RERANK_URL,
            json={"query": query, "chunks": chunk_texts},
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

        # Check HTTP status
        response.raise_for_status()

        # Parse response
        result = response.json()

        if result.get("status") != "success":
            logger.error(f"[MODAL] API returned error status: {result.get('error', 'unknown')}")
            return None

        scores = result.get("scores", [])

        if len(scores) != len(chunks):
            logger.error(f"[MODAL] Score count mismatch: {len(scores)} scores for {len(chunks)} chunks")
            return None

        # Sort chunks by scores (descending)
        scored_chunks = list(zip(chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Return top-K
        reranked = [chunk for chunk, score in scored_chunks[:top_k]]

        elapsed_ms = (time.time() - start_time) * 1000
        modal_latency = result.get("latency_ms", 0)

        logger.info(
            f"[MODAL-RERANK] Received scores in {modal_latency:.0f}ms "
            f"(total {elapsed_ms:.0f}ms including network)"
        )
        logger.debug(f"[MODAL] Top-3 scores: {[scores[i] for i in range(min(3, len(scores)))]}")

        return reranked

    except requests.exceptions.Timeout:
        logger.warning(f"[MODAL] Request timeout after {timeout}s, using fallback")
        return None

    except requests.exceptions.ConnectionError as e:
        logger.warning(f"[MODAL] Connection error: {e}, using fallback")
        return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"[MODAL] HTTP error: {e.response.status_code} - {e.response.text}")
        return None

    except Exception as e:
        logger.error(f"[MODAL] Unexpected error: {e}", exc_info=True)
        return None


def rerank_with_modal_batch(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
    batch_size: int = 50,
    timeout: float = DEFAULT_TIMEOUT
) -> Optional[List[Dict[str, Any]]]:
    """
    Rerank chunks in batches (for very large candidate sets).

    Useful when you have >100 chunks and want to rerank in multiple batches.

    Args:
        query: User query text
        chunks: List of chunk dictionaries
        top_k: Final number of chunks to return
        batch_size: Number of chunks per batch (default 50)
        timeout: Request timeout per batch

    Returns:
        Top-K reranked chunks or None if failed
    """
    if not MODAL_RERANK_URL:
        return None

    if len(chunks) <= batch_size:
        # Single batch, use regular rerank
        return rerank_with_modal(query, chunks, top_k=top_k, timeout=timeout)

    logger.info(f"[MODAL-BATCH] Processing {len(chunks)} chunks in batches of {batch_size}")

    all_scored = []

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        try:
            chunk_texts = [c.get("text", "") for c in batch]

            response = requests.post(
                MODAL_RERANK_URL,
                json={"query": query, "chunks": chunk_texts},
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            scores = result.get("scores", [])

            # Collect scored chunks
            for chunk, score in zip(batch, scores):
                all_scored.append((chunk, score))

        except Exception as e:
            logger.warning(f"[MODAL-BATCH] Batch {i//batch_size + 1} failed: {e}")
            # Continue with remaining batches
            continue

    if not all_scored:
        logger.error("[MODAL-BATCH] All batches failed")
        return None

    # Sort all scored chunks globally
    all_scored.sort(key=lambda x: x[1], reverse=True)

    # Return top-K
    reranked = [chunk for chunk, score in all_scored[:top_k]]

    logger.info(f"[MODAL-BATCH] Reranked {len(chunks)} chunks → top-{len(reranked)} returned")

    return reranked


def check_modal_health(timeout: float = 5.0) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if Modal service is healthy and reachable.

    Args:
        timeout: Request timeout in seconds

    Returns:
        (is_healthy, health_info) tuple

    Example:
        >>> is_healthy, info = check_modal_health()
        >>> if is_healthy:
        ...     print(f"Modal service running: {info['model']}")
    """
    if not MODAL_RERANK_URL:
        return False, {"error": "MODAL_RERANK_URL not configured"}

    try:
        # Derive health endpoint URL
        health_url = MODAL_RERANK_URL.replace("/rerank_api", "/health")

        response = requests.get(health_url, timeout=timeout)
        response.raise_for_status()

        health_info = response.json()

        is_healthy = health_info.get("status") == "healthy"

        return is_healthy, health_info

    except Exception as e:
        logger.error(f"[MODAL] Health check failed: {e}")
        return False, {"error": str(e)}


# Logging helper for debugging
def log_modal_config():
    """Log Modal configuration for debugging."""
    if MODAL_RERANK_URL:
        logger.info(f"[MODAL] Modal rerank URL configured: {MODAL_RERANK_URL}")
        logger.info("[MODAL] GPU reranking enabled")
    else:
        logger.info("[MODAL] Modal rerank URL not configured, using dense-only fallback")
