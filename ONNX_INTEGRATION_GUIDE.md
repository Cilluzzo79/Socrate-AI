# ONNX Reranker Integration Guide - DEPRECATED

> **⚠️ DEPRECATION NOTICE (November 2025)**
> This ONNX integration was removed from production due to Railway's ephemeral filesystem preventing cache persistence.
> The system now uses **Modal GPU Cross-Encoder** as the primary reranker with excellent results.
> This document is kept for historical reference and lessons learned.

## Problem Diagnosis & Solution (Historical)

### Original Issue
- **Symptom**: 56 seconds total time for 30 chunks, but only 2.6s actual ONNX inference
- **Root Cause**: Model was re-exporting from PyTorch to ONNX on **every process start** due to `export=True` parameter

### Solution Implemented
Fixed implementation with proper caching and preloading:

1. **One-time ONNX export** - Cached permanently in `~/.cache/huggingface/onnx/`
2. **Fast cached loading** - ~2-3 seconds to load cached ONNX model
3. **Preload at startup** - Load model when Flask starts, not on first request
4. **Fixed reranking logic** - Always reranks (no early return bug)

## Performance Metrics

### Before Fix
- First request: 56-130 seconds (re-export on every process)
- Subsequent requests: 1.5 seconds

### After Fix
- First process ever: ~60s (one-time ONNX export)
- Process restart with cache: 2-3s model load + 1.5s inference = **~4.5s first request**
- Process restart with preload: **~1.5s first request**
- Subsequent requests: **~1.5s consistently**

## Integration Steps

### 1. Replace the Reranker Module

```bash
# Backup original
mv core/reranker_onnx.py core/reranker_onnx_old.py

# Use optimized version
mv core/reranker_onnx_optimized.py core/reranker_onnx.py
```

### 2. Add Preloading to Flask App

Edit `api_server.py`:

```python
# Add after Flask app initialization
app = Flask(__name__)

# ... existing config ...

# Preload ONNX model for production (avoid first-request latency)
if not app.debug and os.getenv('RAILWAY_ENVIRONMENT'):
    try:
        from core.reranker_onnx import preload_model
        app.logger.info("Preloading ONNX reranker model...")
        preload_model()
        app.logger.info("ONNX model preloaded successfully")
    except Exception as e:
        app.logger.warning(f"Could not preload ONNX model: {e}")
```

### 3. Update RAG Wrapper

In `core/rag_wrapper.py`, ensure it uses ONNX reranker:

```python
# In generate_answer() or wherever reranking happens
from core.reranker_onnx import rerank_chunks_onnx

# Replace Modal reranking with ONNX
reranked_chunks = rerank_chunks_onnx(
    query=query,
    chunks=retrieved_chunks,
    top_k=10
)
```

### 4. Environment Variables

Add to `.env` for Railway:

```env
# Disable Modal GPU reranking (optional, for safety)
MODAL_RERANK_URL=

# Force ONNX usage (optional)
USE_ONNX_RERANKER=true
```

### 5. First Deployment

The first deployment will:
1. Take ~60s on first request to export ONNX model
2. Cache the model permanently
3. All future deployments will use cached model

### 6. Verification

Test the deployment:

```python
# test_production_reranker.py
import requests
import time

# Your Railway URL
base_url = "https://your-app.up.railway.app"

# Test document query
payload = {
    "query": "Come si preparano le orecchiette?",
    "document_id": "your-doc-id"
}

# Measure first request (should be <5s with preload)
start = time.time()
response = requests.post(f"{base_url}/api/query", json=payload)
first_time = time.time() - start

print(f"First request: {first_time:.1f}s")

# Measure second request (should be <2s)
start = time.time()
response = requests.post(f"{base_url}/api/query", json=payload)
second_time = time.time() - start

print(f"Second request: {second_time:.1f}s")
```

## Cost Savings

### Modal GPU Costs (eliminated)
- **Monthly**: $30-50
- **Yearly**: $360-600

### ONNX Local Costs
- **Monthly**: $0
- **Yearly**: $0
- **Savings**: **$360-600/year**

## Quality Comparison

### Retrieval Quality (7 orecchiette chunks test)
- **Modal GPU Cross-Encoder**: 7/7 in top 10
- **ONNX BGE Cross-Encoder**: 7/7 in top 10
- **Quality**: ✅ **Identical**

### Latency Comparison (30 chunks)
| Scenario | Modal GPU | ONNX (Fixed) | Improvement |
|----------|-----------|--------------|-------------|
| Cold start | 15-25s | 1.5s* | **93% faster** |
| Warm request | 800-1500ms | 1500ms | Similar |
| Network latency | 200-500ms | 0ms | Eliminated |

*With preloading at app startup

## Troubleshooting

### Issue: Still slow on first request
**Solution**: Ensure preloading is active in `api_server.py`

### Issue: Model not caching
**Check**: `~/.cache/huggingface/onnx/BAAI_bge-reranker-v2-m3/model.onnx` exists

### Issue: Out of memory
**Solution**: Reduce batch_size in rerank() from 32 to 16 or 8

### Issue: Import errors
**Install**: `pip install optimum[onnxruntime] transformers`

## Architecture Notes

### Why the 53-second overhead occurred
1. Original code had `export=True` always enabled
2. This forced PyTorch → ONNX conversion on every process start
3. The conversion involves:
   - Loading 568M parameter PyTorch model
   - Tracing computation graph
   - Optimizing for ONNX Runtime
   - Writing 1.1GB ONNX file

### How the fix works
1. **First run ever**: Export once, cache permanently
2. **Subsequent runs**: Load cached ONNX file (2-3s)
3. **Preloading**: Move the 2-3s load to app startup, not first request
4. **Singleton pattern**: Keep model in memory for all requests

## Final Recommendation

Deploy the optimized version immediately to:
1. **Save $30-50/month** (no Modal costs)
2. **Improve latency by 93%** on cold starts
3. **Maintain identical quality** (same BGE model)
4. **Eliminate network dependencies** (no external API calls)

The solution is production-ready and will significantly improve both cost efficiency and user experience.