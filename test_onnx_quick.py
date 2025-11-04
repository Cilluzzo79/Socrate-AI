"""
Quick test to verify the fix works - simulates your production scenario
"""

import time
import sys
import os
from pathlib import Path

# Set logging to INFO to see progress
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def simulate_production_scenario():
    """Simulate exactly what happens in production:
    1. Fresh process starts (like Railway container)
    2. First request comes in
    3. Model needs to load
    """

    print("\n" + "="*80)
    print("PRODUCTION SCENARIO SIMULATION - Fresh Process")
    print("="*80)

    # Measure TOTAL time from cold start
    t_total_start = time.time()

    print("\n1. Importing module...")
    t1 = time.time()
    from core.reranker_onnx_fixed import rerank_chunks_onnx
    t2 = time.time()
    print(f"   Import time: {(t2-t1)*1000:.1f}ms")

    print("\n2. First RAG query (cold start - will load model)...")
    chunks = [
        {'text': f'Chunk {i}: Italian recipe content about pasta, cooking, ingredients', 'chunk_id': i}
        for i in range(30)
    ]

    t1 = time.time()
    result = rerank_chunks_onnx(
        "Come si preparano le orecchiette?",
        chunks,
        top_k=10
    )
    t2 = time.time()
    first_call_time = (t2-t1)*1000
    print(f"   First rerank (30 chunks): {first_call_time:.1f}ms")

    print("\n3. Second RAG query (warm - model already loaded)...")
    t1 = time.time()
    result = rerank_chunks_onnx(
        "Ricetta della carbonara",
        chunks,
        top_k=10
    )
    t2 = time.time()
    second_call_time = (t2-t1)*1000
    print(f"   Second rerank (30 chunks): {second_call_time:.1f}ms")

    print("\n4. Third query (should be consistently fast)...")
    t1 = time.time()
    result = rerank_chunks_onnx(
        "Come fare il tiramisu",
        chunks,
        top_k=10
    )
    t2 = time.time()
    third_call_time = (t2-t1)*1000
    print(f"   Third rerank (30 chunks): {third_call_time:.1f}ms")

    total_time = (time.time() - t_total_start) * 1000

    print("\n" + "="*80)
    print("RESULTS SUMMARY:")
    print("-"*80)
    print(f"Total time from cold start: {total_time:.1f}ms")
    print(f"First query (includes model load): {first_call_time:.1f}ms")
    print(f"Subsequent queries avg: {(second_call_time + third_call_time)/2:.1f}ms")

    print("\n" + "="*80)

    # Success criteria
    if first_call_time < 10000:  # First call under 10 seconds
        print("✓ PASS: First call under 10 seconds")
    else:
        print("✗ FAIL: First call took too long")

    if second_call_time < 3000 and third_call_time < 3000:  # Subsequent under 3 seconds
        print("✓ PASS: Subsequent calls under 3 seconds")
    else:
        print("✗ FAIL: Subsequent calls too slow")

    print("="*80)

if __name__ == "__main__":
    # Clear any existing singleton to simulate fresh process
    if 'core.reranker_onnx_fixed' in sys.modules:
        del sys.modules['core.reranker_onnx_fixed']

    simulate_production_scenario()