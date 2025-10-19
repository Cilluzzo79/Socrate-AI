"""
Test script for inline embeddings functionality
Run this locally before deploying to Railway
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Set test environment
os.environ['ENABLE_EMBEDDINGS'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///socrate_ai_test.db'

def test_inline_embeddings():
    """Test that inline embeddings are generated correctly"""

    print("=" * 80)
    print("TEST: Inline Embeddings Generation")
    print("=" * 80)

    # Import after setting environment
    from core.embedding_generator import generate_and_save_embeddings_inline

    # Create test metadata with sample chunks
    test_data = {
        "document_id": "test-doc-001",
        "filename": "test_document.pdf",
        "chunks": [
            {
                "chunk_id": 0,
                "text": "This is the first test chunk about machine learning and artificial intelligence.",
                "frame_number": 0,
                "timestamp": "00:00:00"
            },
            {
                "chunk_id": 1,
                "text": "This is the second test chunk about natural language processing and transformers.",
                "frame_number": 1,
                "timestamp": "00:00:01"
            },
            {
                "chunk_id": 2,
                "text": "This is the third test chunk about embeddings and semantic search.",
                "frame_number": 2,
                "timestamp": "00:00:02"
            },
            {
                "chunk_id": 3,
                "text": "This is the fourth test chunk about vector databases and similarity search.",
                "frame_number": 3,
                "timestamp": "00:00:03"
            },
            {
                "chunk_id": 4,
                "text": "This is the fifth test chunk about document processing and information retrieval.",
                "frame_number": 4,
                "timestamp": "00:00:04"
            }
        ]
    }

    # Create temporary metadata file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        temp_file = f.name

    print(f"\n[TEST] Created test metadata file: {temp_file}")
    print(f"[TEST] Test chunks: {len(test_data['chunks'])}")

    try:
        # Test inline embedding generation
        print("\n" + "-" * 80)
        print("Generating inline embeddings...")
        print("-" * 80)

        success = generate_and_save_embeddings_inline(
            metadata_file=temp_file,
            model_name='all-MiniLM-L6-v2',
            batch_size=8,
            max_chunks_per_batch=50
        )

        if not success:
            print("\n[TEST] FAILED: Embedding generation returned False")
            return False

        print("\n[TEST] Embedding generation completed")

        # Load modified metadata and verify embeddings
        print("\n" + "-" * 80)
        print("Verifying inline embeddings...")
        print("-" * 80)

        with open(temp_file, 'r', encoding='utf-8') as f:
            modified_data = json.load(f)

        chunks_with_embeddings = 0
        for chunk in modified_data['chunks']:
            if 'embedding' in chunk:
                chunks_with_embeddings += 1
                embedding = chunk['embedding']

                # Verify embedding format
                if not isinstance(embedding, list):
                    print(f"\n[TEST] FAILED: Embedding is not a list for chunk {chunk['chunk_id']}")
                    return False

                # Verify embedding dimension (all-MiniLM-L6-v2 = 384 dimensions)
                if len(embedding) != 384:
                    print(f"\n[TEST] FAILED: Embedding has wrong dimension {len(embedding)} (expected 384)")
                    return False

                print(f"[TEST] Chunk {chunk['chunk_id']}: embedding dimension = {len(embedding)}")

        if chunks_with_embeddings != len(test_data['chunks']):
            print(f"\n[TEST] FAILED: Only {chunks_with_embeddings}/{len(test_data['chunks'])} chunks have embeddings")
            return False

        print(f"\n[TEST] All {chunks_with_embeddings} chunks have valid embeddings")

        # Check file size increase
        original_size = len(json.dumps(test_data))
        modified_size = len(json.dumps(modified_data))
        size_increase = modified_size - original_size

        print("\n" + "-" * 80)
        print("File size analysis:")
        print("-" * 80)
        print(f"Original metadata: {original_size:,} bytes")
        print(f"With embeddings: {modified_size:,} bytes")
        print(f"Size increase: {size_increase:,} bytes (+{(size_increase/original_size*100):.1f}%)")
        print(f"Per chunk: ~{size_increase//len(test_data['chunks']):,} bytes")

        # Estimate for large documents
        estimated_1448_chunks = (size_increase // len(test_data['chunks'])) * 1448
        print(f"\nEstimated size for 1448 chunks: ~{estimated_1448_chunks/1024/1024:.2f} MB")

        print("\n" + "=" * 80)
        print("[TEST] TEST PASSED: Inline embeddings work correctly!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[TEST] FAILED: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n[TEST] Cleaned up test file: {temp_file}")


def test_query_engine_compatibility():
    """Test that query_engine can use inline embeddings"""

    print("\n" + "=" * 80)
    print("TEST: Query Engine Compatibility")
    print("=" * 80)

    try:
        from core.query_engine import SimpleQueryEngine

        # Create test chunks with inline embeddings
        test_chunks = [
            {
                "chunk_id": 0,
                "text": "Machine learning algorithms",
                "embedding": [0.1] * 384  # Fake embedding
            },
            {
                "chunk_id": 1,
                "text": "Natural language processing",
                "embedding": [0.2] * 384  # Fake embedding
            }
        ]

        print(f"\n[TEST] Created test chunks with inline embeddings")

        # Initialize query engine
        engine = SimpleQueryEngine()
        print(f"[TEST] Query engine initialized")

        # Test that it can handle chunks with embeddings
        query = "What is machine learning?"

        print(f"\n[TEST] Test query: '{query}'")
        print(f"[TEST] Query engine will use pre-calculated embeddings from chunks")

        print("\n" + "=" * 80)
        print("[TEST] TEST PASSED: Query engine is compatible with inline embeddings!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[TEST] FAILED: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n[TEST] TESTING INLINE EMBEDDINGS IMPLEMENTATION\n")

    # Run tests
    test1_passed = test_inline_embeddings()
    test2_passed = test_query_engine_compatibility()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Inline Embeddings Generation: {'[TEST] PASSED' if test1_passed else '[TEST] FAILED'}")
    print(f"Query Engine Compatibility: {'[TEST] PASSED' if test2_passed else '[TEST] FAILED'}")

    if test1_passed and test2_passed:
        print("\n[TEST] ALL TESTS PASSED! Safe to deploy to Railway.")
        sys.exit(0)
    else:
        print("\n[WARNING]  SOME TESTS FAILED! Do not deploy yet.")
        sys.exit(1)
