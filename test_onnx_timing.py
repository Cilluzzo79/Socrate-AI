"""
Focused timing test for ONNX reranker overhead diagnosis
"""

import time
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_timing():
    print("ONNX Reranker Timing Diagnosis")
    print("=" * 60)

    # Test 1: Module import time
    t1 = time.time()
    from core.reranker_onnx import rerank_chunks_onnx, get_onnx_reranker
    t2 = time.time()
    print(f"Module import time: {(t2-t1)*1000:.1f}ms")

    # Test 2: First singleton call (model loading)
    print("\nFirst call - should load model:")
    t1 = time.time()
    reranker = get_onnx_reranker()
    t2 = time.time()
    print(f"First get_onnx_reranker(): {(t2-t1)*1000:.1f}ms")

    # Test 3: Second singleton call (should be instant)
    print("\nSecond call - should return cached instance:")
    t1 = time.time()
    reranker2 = get_onnx_reranker()
    t2 = time.time()
    print(f"Second get_onnx_reranker(): {(t2-t1)*1000:.1f}ms")
    print(f"Same instance? {reranker is reranker2}")

    # Test 4: Small rerank operation
    print("\nSmall rerank (8 chunks):")
    chunks = [
        {'text': f'Test chunk {i} with some content about pasta and cooking', 'chunk_id': i}
        for i in range(8)
    ]

    t1 = time.time()
    result = reranker.rerank("How to cook pasta?", chunks, top_k=5)
    t2 = time.time()
    print(f"Rerank 8 chunks: {(t2-t1)*1000:.1f}ms")

    # Test 5: Larger rerank operation
    print("\nLarge rerank (30 chunks):")
    chunks = [
        {'text': f'Test chunk {i} with some content about various Italian recipes and cooking techniques', 'chunk_id': i}
        for i in range(30)
    ]

    t1 = time.time()
    result = reranker.rerank("How to make orecchiette pasta?", chunks, top_k=10)
    t2 = time.time()
    print(f"Rerank 30 chunks: {(t2-t1)*1000:.1f}ms")

    # Test 6: Multiple consecutive calls
    print("\nConsecutive calls (3x 30 chunks):")
    for i in range(3):
        t1 = time.time()
        result = reranker.rerank(f"Query {i}", chunks, top_k=10)
        t2 = time.time()
        print(f"  Call {i+1}: {(t2-t1)*1000:.1f}ms")

if __name__ == "__main__":
    test_timing()