"""
Test that the ONNX model is properly cached and loads fast on second run
"""

import time
import sys
import os
from pathlib import Path

# Set logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_cached_loading():
    print("\n" + "="*80)
    print("TEST: Loading from CACHED ONNX Model (second process start)")
    print("="*80)
    print("\nThis simulates what happens when Railway container restarts")
    print("The ONNX model should already be cached from previous run\n")

    # Test loading speed
    t1 = time.time()
    from core.reranker_onnx_fixed import rerank_chunks_onnx
    t2 = time.time()
    print(f"1. Module import: {(t2-t1)*1000:.1f}ms")

    # First rerank call (should load cached ONNX model)
    chunks = [
        {'text': f'Test chunk {i}: Content about recipes', 'chunk_id': i}
        for i in range(30)
    ]

    t1 = time.time()
    result = rerank_chunks_onnx("Test query", chunks, top_k=10)
    t2 = time.time()
    first_time = (t2-t1)*1000
    print(f"2. First rerank (loads cached model): {first_time:.1f}ms")

    # Second call
    t1 = time.time()
    result = rerank_chunks_onnx("Another query", chunks, top_k=10)
    t2 = time.time()
    second_time = (t2-t1)*1000
    print(f"3. Second rerank: {second_time:.1f}ms")

    print("\n" + "="*80)
    print("RESULTS:")
    print("-"*80)

    if first_time < 5000:  # Should load in under 5 seconds from cache
        print(f"SUCCESS: Cached model loaded in {first_time:.1f}ms (<5s)")
        print("The fix is working! Model is properly cached.")
    else:
        print(f"PROBLEM: First call took {first_time:.1f}ms (>5s)")
        print("Model may be re-exporting instead of using cache")

    print("="*80)

if __name__ == "__main__":
    test_cached_loading()