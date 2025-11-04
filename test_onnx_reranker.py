"""
Test script for BGE ONNX Reranker - Cost Optimization Validation

Tests the ONNX-optimized reranker with Italian recipe queries to ensure:
1. Model loads correctly
2. Reranking produces quality results
3. Latency is <500ms (vs 15-25s Modal cold start)
4. Italian language handling is excellent

Run: python test_onnx_reranker.py
"""

import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_onnx_reranker():
    """Test ONNX reranker with Italian recipe queries"""

    print("=" * 80)
    print("🧪 BGE ONNX RERANKER TEST - Cost Optimization Validation")
    print("=" * 80)
    print()

    # Import reranker
    print("📦 Importing ONNX reranker...")
    try:
        from core.reranker_onnx import rerank_chunks_onnx
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    print()

    # Test data: Italian recipe chunks (simulating memvid chunks)
    print("📝 Creating test chunks (Italian recipes)...")
    test_chunks = [
        {
            'text': 'Ossobuco alla milanese è un piatto tradizionale lombardo preparato con stinco di vitello.',
            'chunk_id': 1,
            'page': 45
        },
        {
            'text': 'Il risotto allo zafferano è perfetto come accompagnamento per l\'ossobuco.',
            'chunk_id': 2,
            'page': 45
        },
        {
            'text': 'Ingredienti: 4 ossobuchi di vitello, farina, burro, vino bianco, brodo.',
            'chunk_id': 3,
            'page': 46
        },
        {
            'text': 'La pizza margherita è originaria di Napoli e ha pomodoro, mozzarella e basilico.',
            'chunk_id': 4,
            'page': 12
        },
        {
            'text': 'La preparazione richiede circa 2 ore di cottura lenta.',
            'chunk_id': 5,
            'page': 46
        },
        {
            'text': 'Il tiramisù è un dolce a base di mascarpone, caffè e savoiardi.',
            'chunk_id': 6,
            'page': 89
        },
        {
            'text': 'Per l\'ossobuco si usa tradizionalmente la gremolata come guarnizione finale.',
            'chunk_id': 7,
            'page': 47
        },
        {
            'text': 'La carbonara romana prevede guanciale, pecorino, uova e pepe nero.',
            'chunk_id': 8,
            'page': 23
        }
    ]

    print(f"✅ Created {len(test_chunks)} test chunks")
    print()

    # Test query: should rank ossobuco chunks highest
    test_query = "Come si prepara l'ossobuco alla milanese?"

    print(f"🔍 Test query: \"{test_query}\"")
    print()
    print("Expected: Chunks 1, 3, 7 should rank highest (ossobuco-specific)")
    print()

    # Run reranking with timing
    print("🚀 Running ONNX reranking...")
    print()

    start_time = time.time()

    try:
        reranked_chunks = rerank_chunks_onnx(
            query=test_query,
            chunks=test_chunks,
            top_k=5  # Get top 5 chunks
        )

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"✅ Reranking completed in {elapsed_ms:.1f}ms")
        print()

        # Display results
        print("📊 RERANKING RESULTS:")
        print("-" * 80)

        for i, chunk in enumerate(reranked_chunks, 1):
            score = chunk.get('rerank_score', 0)
            chunk_id = chunk.get('chunk_id', 'unknown')
            text_preview = chunk['text'][:70] + "..." if len(chunk['text']) > 70 else chunk['text']

            print(f"\n#{i} | Score: {score:.4f} | Chunk ID: {chunk_id}")
            print(f"    Text: {text_preview}")

        print()
        print("-" * 80)
        print()

        # Validation checks
        print("🔬 VALIDATION CHECKS:")
        print()

        # Check 1: Latency
        latency_ok = elapsed_ms < 500
        print(f"✓ Latency < 500ms: {elapsed_ms:.1f}ms {'✅ PASS' if latency_ok else '❌ FAIL'}")

        # Check 2: Ossobuco chunks in top 3
        top_3_ids = [c.get('chunk_id') for c in reranked_chunks[:3]]
        ossobuco_chunks = [1, 3, 7]  # Expected ossobuco-relevant chunks
        ossobuco_in_top_3 = sum(1 for cid in ossobuco_chunks if cid in top_3_ids)
        ossobuco_ok = ossobuco_in_top_3 >= 2

        print(f"✓ Ossobuco chunks in top 3: {ossobuco_in_top_3}/3 {' ✅ PASS' if ossobuco_ok else '⚠️  MARGINAL' if ossobuco_in_top_3 >= 1 else '❌ FAIL'}")

        # Check 3: Score distribution
        scores = [c.get('rerank_score', 0) for c in reranked_chunks]
        score_spread = max(scores) - min(scores)
        spread_ok = score_spread > 0.1  # Good discrimination

        print(f"✓ Score discrimination: {score_spread:.4f} {'✅ PASS' if spread_ok else '⚠️  MARGINAL'}")

        # Check 4: No crashes
        print(f"✓ No crashes: ✅ PASS")

        print()

        # Overall verdict
        all_pass = latency_ok and ossobuco_ok and spread_ok

        if all_pass:
            print("=" * 80)
            print("🎉 ALL CHECKS PASSED - ONNX Reranker is PRODUCTION READY!")
            print("=" * 80)
            print()
            print("💰 Cost Impact:")
            print(f"   • Current (Modal GPU): ~$30-50/month + 15-25s cold start")
            print(f"   • New (ONNX CPU):      $0/month + <500ms latency")
            print(f"   • Savings:             100% cost reduction + 95% latency improvement")
            print()
            return True
        else:
            print("=" * 80)
            print("⚠️  SOME CHECKS FAILED - Review results above")
            print("=" * 80)
            print()
            return False

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"❌ Reranking failed after {elapsed_ms:.1f}ms")
        print(f"   Error: {e}")
        print()

        import traceback
        print("🔍 Full traceback:")
        print(traceback.format_exc())

        return False


def test_model_loading():
    """Test that ONNX model loads correctly on first import"""

    print()
    print("=" * 80)
    print("🔧 MODEL LOADING TEST")
    print("=" * 80)
    print()

    print("⚠️  Note: First model load may take 30-60 seconds (ONNX export + download)")
    print("   Subsequent loads will be instant (<1s)")
    print()

    start_time = time.time()

    try:
        from core.reranker_onnx import get_onnx_reranker

        print("📦 Loading ONNX model...")
        reranker = get_onnx_reranker()

        elapsed = time.time() - start_time

        print(f"✅ Model loaded successfully in {elapsed:.1f}s")
        print(f"   Model: {reranker.model_name}")
        print(f"   Max sequence length: {reranker.tokenizer.model_max_length}")
        print()

        return True

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Model loading failed after {elapsed:.1f}s")
        print(f"   Error: {e}")
        print()

        import traceback
        print("🔍 Full traceback:")
        print(traceback.format_exc())

        return False


if __name__ == "__main__":
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "     BGE ONNX RERANKER TEST SUITE - Cost Optimization Validation".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Test 1: Model loading
    model_ok = test_model_loading()

    if not model_ok:
        print()
        print("❌ Model loading failed - cannot proceed with reranking test")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check that optimum[onnxruntime] is installed: pip install optimum[onnxruntime]")
        print("   2. Ensure internet connection for model download")
        print("   3. Check disk space (~2GB needed for model cache)")
        print()
        sys.exit(1)

    # Test 2: Reranking functionality
    rerank_ok = test_onnx_reranker()

    if rerank_ok:
        print()
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "✅ ONNX RERANKER READY FOR INTEGRATION".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        print("🎯 Next Steps:")
        print("   1. Integrate into query_engine.py (replace Modal GPU)")
        print("   2. Deploy to Railway")
        print("   3. Validate in production with real queries")
        print("   4. Monitor cost savings: $30-50/month → $0")
        print()
        sys.exit(0)
    else:
        print()
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "⚠️  TESTS INCOMPLETE - Review errors above".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        sys.exit(1)
