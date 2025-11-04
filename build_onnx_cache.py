#!/usr/bin/env python3
"""
Pre-build ONNX cache during Railway deployment build phase.

This script exports the BGE reranker model to ONNX format and caches it
in the Docker image, avoiding the 60-90s export time on first query.

Usage:
    python build_onnx_cache.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_onnx_cache():
    """Build ONNX model cache during Docker build."""

    logger.info("=" * 80)
    logger.info("ONNX CACHE BUILD - Pre-building reranker model")
    logger.info("=" * 80)

    try:
        # Import ONNX reranker (this will trigger model export if not cached)
        logger.info("Importing ONNX reranker module...")
        from core.reranker_onnx import get_onnx_reranker

        # Get or create the ONNX reranker instance
        logger.info("Initializing ONNX reranker (will export if needed)...")
        reranker = get_onnx_reranker()

        # Verify cache was created
        cache_dir = Path.home() / ".cache" / "huggingface" / "onnx"
        model_path = cache_dir / "BAAI_bge-reranker-v2-m3" / "model.onnx"

        if model_path.exists():
            logger.info(f"✅ ONNX cache built successfully: {model_path}")
            logger.info(f"   Cache size: {model_path.stat().st_size / 1024 / 1024:.1f} MB")
            logger.info("=" * 80)
            logger.info("✅ ONNX CACHE BUILD COMPLETE")
            logger.info("=" * 80)
            return True
        else:
            logger.error(f"❌ ONNX cache not found after build: {model_path}")
            return False

    except Exception as e:
        logger.error(f"❌ ONNX cache build failed: {e}", exc_info=True)
        logger.warning("Deployment will continue, but ONNX will fallback to Modal GPU")
        # Don't fail the build - fallback to Modal is acceptable
        return False

if __name__ == "__main__":
    success = build_onnx_cache()
    # Exit 0 even if failed - we don't want to block deployment
    # Modal fallback will handle queries
    sys.exit(0)
