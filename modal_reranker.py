"""
Modal Labs GPU Reranker Service for Socrate RAG System

Deploys Cross-Encoder on serverless GPU (NVIDIA T4) for high-quality
document reranking with ~200-300ms latency.

Free Tier: 30 GPU-hours/month (~540K queries)
Cost beyond: ~$0.60/hour

Usage:
    modal deploy modal_reranker.py
    # Returns: https://your-username--socrate-reranker-rerank-api.modal.run
"""

import modal

# Define Modal app
app = modal.App("socrate-reranker")

# Define Docker image with dependencies (updated versions for Modal 2025)
image = modal.Image.debian_slim().pip_install(
    "sentence-transformers>=2.7.0",
    "torch>=2.5.0",
    "transformers>=4.40.0",
    "fastapi"  # Required for web endpoints
)


# GPU function for reranking
@app.function(
    gpu="T4",  # NVIDIA T4 - perfect for inference
    image=image,
    timeout=60,  # 60s timeout per request
    scaledown_window=300,  # Keep warm for 5min
    max_containers=10,  # Handle 10 concurrent containers
)
def rerank_batch(query: str, chunk_texts: list[str]) -> list[float]:
    """
    Rerank chunks using Cross-Encoder on GPU.

    Args:
        query: User query text
        chunk_texts: List of chunk text strings to rerank

    Returns:
        List of relevance scores (higher = more relevant)
    """
    from sentence_transformers import CrossEncoder
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load model (cached after first call)
    model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")

    # Prepare query-document pairs
    pairs = [[query, chunk_text] for chunk_text in chunk_texts]

    logger.info(f"[MODAL-RERANK] Processing {len(pairs)} pairs")

    # Compute scores
    scores = model.predict(pairs)

    # Convert numpy to list
    scores_list = scores.tolist()

    logger.info(f"[MODAL-RERANK] Computed scores, max={max(scores_list):.3f}, min={min(scores_list):.3f}")

    return scores_list


# Web API endpoint
@app.function(
    image=image,
    timeout=60
)
@modal.fastapi_endpoint(method="POST")
def rerank_api(data: dict):
    """
    HTTP API endpoint for reranking.

    Request:
        POST /
        {
            "query": "Come si prepara l'ossobuco?",
            "chunks": ["chunk1 text", "chunk2 text", ...]
        }

    Response:
        {
            "scores": [0.85, 0.23, ...],
            "num_chunks": 50,
            "latency_ms": 234
        }
    """
    import time

    start_time = time.time()

    # Validate input
    if "query" not in data or "chunks" not in data:
        return {
            "error": "Missing 'query' or 'chunks' in request body",
            "status": "error"
        }, 400

    query = data["query"]
    chunks = data["chunks"]

    if not isinstance(chunks, list):
        return {
            "error": "'chunks' must be a list of strings",
            "status": "error"
        }, 400

    if len(chunks) == 0:
        return {
            "scores": [],
            "num_chunks": 0,
            "latency_ms": 0,
            "status": "success"
        }

    if len(chunks) > 100:
        return {
            "error": "Maximum 100 chunks allowed per request",
            "status": "error"
        }, 400

    # Call GPU function
    try:
        scores = rerank_batch.remote(query, chunks)

        latency_ms = (time.time() - start_time) * 1000

        return {
            "scores": scores,
            "num_chunks": len(scores),
            "latency_ms": round(latency_ms, 2),
            "status": "success"
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }, 500


# Health check endpoint
@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "socrate-reranker",
        "gpu": "T4",
        "model": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    }


# Local testing function
@app.local_entrypoint()
def test_local():
    """
    Test the reranker locally (will use GPU if deployed).

    Usage:
        modal run modal_reranker.py
    """
    # Test data
    query = "Come si prepara l'ossobuco alla milanese?"
    chunks = [
        "L'ossobuco alla milanese è un piatto tradizionale lombardo preparato con fette di stinco di vitello.",
        "Il risotto alla milanese è un primo piatto a base di riso e zafferano.",
        "La preparazione dell'ossobuco richiede circa 2 ore di cottura lenta.",
        "Gli ingredienti principali sono: ossobuco di vitello, farina, burro, vino bianco.",
    ]

    print(f"\n[TEST] Query: {query}")
    print(f"[TEST] Reranking {len(chunks)} chunks...")

    # Call GPU function
    scores = rerank_batch.remote(query, chunks)

    # Print results
    print(f"\n[TEST] Scores:")
    for i, (chunk, score) in enumerate(sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)):
        print(f"  {i+1}. [{score:.3f}] {chunk[:80]}...")

    print(f"\n[TEST] Success! GPU reranking working correctly.")


# Deployment instructions
"""
DEPLOYMENT STEPS:

1. Authenticate Modal:
   modal token new

2. Deploy to Modal Cloud:
   modal deploy modal_reranker.py

3. Get endpoint URL:
   Output will show: https://your-username--socrate-reranker-rerank-api.modal.run

4. Test endpoint:
   curl -X POST https://your-url/rerank_api \\
     -H "Content-Type: application/json" \\
     -d '{"query": "test", "chunks": ["chunk1", "chunk2"]}'

5. Add to Railway environment variables:
   MODAL_RERANK_URL=https://your-url/rerank_api

6. Deploy Railway with updated query_engine.py

MONITORING:

- Dashboard: https://modal.com/apps
- Logs: modal app logs socrate-reranker
- Usage: Check GPU-hours in Modal dashboard

COST ESTIMATES:

- Free tier: 30 GPU-hours/month
- Beyond: ~$0.60/hour
- Typical query: ~0.2s = $0.000033 per query
- 10K queries: ~$0.33
- 100K queries: ~$3.30
"""
