"""
ONNX-Optimized Reranker for BGE v2-m3 Cross-Encoder - PRODUCTION OPTIMIZED VERSION

Key optimizations:
1. Cached ONNX model (no re-export after first run)
2. Preload option for production (load at startup, not on first request)
3. Proper reranking for all chunk sizes

Performance targets:
- First request: <3s (with preloaded model)
- Subsequent requests: <2s for 30 chunks
- Cost: $0 (vs $30-50/month Modal)

Model: BAAI/bge-reranker-v2-m3
"""

from typing import List, Dict, Any, Optional
import logging
import os
import numpy as np
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Lazy imports
_ORTModelForSequenceClassification = None
_AutoTokenizer = None

def _get_onnx_model():
    """Lazy load ONNX model classes"""
    global _ORTModelForSequenceClassification, _AutoTokenizer
    if _ORTModelForSequenceClassification is None:
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification
            from transformers import AutoTokenizer
            _ORTModelForSequenceClassification = ORTModelForSequenceClassification
            _AutoTokenizer = AutoTokenizer
        except ImportError:
            logger.error("optimum[onnxruntime] not installed. Install with: pip install optimum[onnxruntime]")
            raise
    return _ORTModelForSequenceClassification, _AutoTokenizer


class ONNXReranker:
    """
    Production-optimized ONNX cross-encoder reranker.

    Key features:
    - One-time ONNX export (cached permanently)
    - Fast loading from cache (~2-3s)
    - Consistent <2s inference for 30 chunks
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize ONNX reranker with smart caching."""

        self.model_name = model_name or os.getenv(
            'ONNX_RERANKER_MODEL',
            'BAAI/bge-reranker-v2-m3'
        )

        # Cache paths
        cache_dir = Path.home() / ".cache" / "huggingface" / "onnx"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.onnx_model_path = cache_dir / self.model_name.replace("/", "_")

        logger.info(f"[ONNX-RERANKER] Initializing {self.model_name}")

        try:
            ORTModel, Tokenizer = _get_onnx_model()

            # Check for cached ONNX model
            onnx_file = self.onnx_model_path / "model.onnx"

            if onnx_file.exists():
                # Load from cache (FAST: 2-3 seconds)
                start = time.time()
                logger.info(f"[ONNX-RERANKER] Loading cached model from {self.onnx_model_path}")

                self.model = ORTModel.from_pretrained(
                    str(self.onnx_model_path),
                    provider="CPUExecutionProvider"
                )

                logger.info(f"[ONNX-RERANKER] Model loaded in {(time.time()-start)*1000:.1f}ms")

            else:
                # First time: Export and cache (SLOW: ~60s, one time only)
                logger.info("[ONNX-RERANKER] First-time setup: Converting PyTorch → ONNX")
                logger.info("[ONNX-RERANKER] This will take ~60s but only happens once")

                start = time.time()

                # Export from HuggingFace
                self.model = ORTModel.from_pretrained(
                    self.model_name,
                    export=True,
                    provider="CPUExecutionProvider"
                )

                # Save to cache
                logger.info(f"[ONNX-RERANKER] Saving to {self.onnx_model_path}")
                self.model.save_pretrained(str(self.onnx_model_path))

                logger.info(f"[ONNX-RERANKER] Export completed in {(time.time()-start):.1f}s")

            # Load tokenizer (always fast)
            self.tokenizer = Tokenizer.from_pretrained(self.model_name)
            logger.info(f"[ONNX-RERANKER] Ready! Max length: {self.tokenizer.model_max_length}")

        except Exception as e:
            logger.error(f"[ONNX-RERANKER] Failed to load: {e}")
            raise

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 10,
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using ONNX cross-encoder.

        Performance:
        - 30 chunks: ~1.5s
        - 50 chunks: ~2.5s
        - 100 chunks: ~5s
        """
        if not chunks:
            return []

        start_time = time.time()
        num_chunks = len(chunks)
        actual_top_k = min(top_k, num_chunks)

        logger.info(f"[ONNX-RERANKER] Processing {num_chunks} chunks → top {actual_top_k}")

        try:
            # Prepare pairs
            pairs = [[query, chunk['text']] for chunk in chunks]
            all_scores = []

            # Process in batches
            for i in range(0, len(pairs), batch_size):
                batch = pairs[i:i + batch_size]

                # Tokenize
                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )

                # Inference
                outputs = self.model(**inputs)
                scores = outputs.logits.squeeze(-1).detach().numpy()

                # Handle single item
                if scores.ndim == 0:
                    scores = np.array([scores.item()])

                all_scores.extend(scores.tolist())

            # Add scores and sort
            for chunk, score in zip(chunks, all_scores):
                chunk['rerank_score'] = float(score)

            # Get top k
            ranked_indices = np.argsort(all_scores)[::-1][:actual_top_k]
            reranked = [chunks[i] for i in ranked_indices]

            # Stats
            elapsed = (time.time() - start_time) * 1000
            top_scores = [all_scores[i] for i in ranked_indices]

            logger.info(
                f"[ONNX-RERANKER] Done in {elapsed:.1f}ms | "
                f"Scores: {min(top_scores):.2f} to {max(top_scores):.2f}"
            )

            return reranked

        except Exception as e:
            logger.error(f"[ONNX-RERANKER] Error: {e}", exc_info=True)
            return chunks[:actual_top_k]


# Singleton
_instance: Optional[ONNXReranker] = None

def get_onnx_reranker() -> ONNXReranker:
    """Get singleton instance."""
    global _instance
    if _instance is None:
        _instance = ONNXReranker()
    return _instance


def rerank_chunks_onnx(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Main entry point for reranking."""
    return get_onnx_reranker().rerank(query, chunks, top_k)


def preload_model():
    """
    Preload the model at application startup.
    Call this in api_server.py or __init__ to avoid first-request latency.

    Usage in api_server.py:
        if not app.debug:  # Only in production
            from core.reranker_onnx_optimized import preload_model
            preload_model()
    """
    logger.info("[ONNX-RERANKER] Preloading model at startup...")
    start = time.time()
    get_onnx_reranker()
    logger.info(f"[ONNX-RERANKER] Model preloaded in {(time.time()-start)*1000:.1f}ms")
    return True