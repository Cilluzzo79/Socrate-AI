"""
Test the FIXED ONNX reranker implementation
"""

import time
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_fixed_version():
    print("Testing FIXED ONNX Reranker")
    print("=" * 60)

    # Import the FIXED version
    from core.reranker_onnx_fixed import rerank_chunks_onnx, get_onnx_reranker

    # Create 30 test chunks
    chunks = [
        {'text': f'Test chunk {i}: Content about Italian recipes, pasta, cooking techniques and ingredients', 'chunk_id': i}
        for i in range(30)
    ]

    print("Test 1: First call (may need to export ONNX on first run)")
    print("-" * 60)
    t1 = time.time()
    reranker = get_onnx_reranker()
    t2 = time.time()
    print(f"Model loading: {(t2-t1)*1000:.1f}ms")

    print("\nTest 2: Rerank 30 chunks")
    print("-" * 60)
    t1 = time.time()
    result = rerank_chunks_onnx(
        "How to make pasta?",
        chunks,
        top_k=10
    )
    t2 = time.time()
    print(f"Rerank time: {(t2-t1)*1000:.1f}ms")
    print(f"Returned {len(result)} chunks")

    print("\nTest 3: Second rerank call (should be fast)")
    print("-" * 60)
    t1 = time.time()
    result = rerank_chunks_onnx(
        "Recipe for orecchiette",
        chunks,
        top_k=10
    )
    t2 = time.time()
    print(f"Rerank time: {(t2-t1)*1000:.1f}ms")

    print("\nTest 4: Small chunk test (8 chunks - should still rerank)")
    print("-" * 60)
    small_chunks = chunks[:8]
    t1 = time.time()
    result = rerank_chunks_onnx(
        "Italian cooking",
        small_chunks,
        top_k=10  # top_k > chunks
    )
    t2 = time.time()
    print(f"Rerank time: {(t2-t1)*1000:.1f}ms")
    print(f"Returned {len(result)} chunks (should be 8 with scores)")

    # Check if scores were added
    if result and 'rerank_score' in result[0]:
        print(f"Scores added: YES (top score: {result[0]['rerank_score']:.3f})")
    else:
        print("WARNING: No scores added!")

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("If first load was <5s and rerankings are <2s, the fix worked!")
    print("=" * 60)

if __name__ == "__main__":
    test_fixed_version()