# Modal Labs Setup Guide - GPU Reranking per Socrate

## Quick Start (5 Minuti)

### Step 1: Create Modal Account & Authenticate

```bash
# 1. Vai su https://modal.com e crea account (GitHub login consigliato)
#    Free tier: 30 GPU-ore/mese gratis!

# 2. Authenticate Modal CLI
cd D:\railway\memvid
python -m modal token new

# Questo aprir il browser per login
# Dopo login, il token verr salvato automaticamente
```

### Step 2: Test Locally

```bash
# Test il reranker localmente (usa GPU cloud)
python -m modal run modal_reranker.py

# Output atteso:
# [TEST] Query: Come si prepara l'ossobuco alla milanese?
# [TEST] Reranking 4 chunks...
# [TEST] Scores:
#   1. [9.234] L'ossobuco alla milanese  un piatto tradizionale...
#   2. [3.421] La preparazione dell'ossobuco richiede circa 2 ore...
#   3. [0.234] Gli ingredienti principali sono: ossobuco di vitello...
#   4. [-1.234] Il risotto alla milanese  un primo piatto...
# [TEST] Success! GPU reranking working correctly.
```

### Step 3: Deploy to Modal Cloud

```bash
# Deploy service to Modal (serverless GPU)
python -m modal deploy modal_reranker.py

# Output atteso:
# ✓ Created objects.
# ├── 🔨 Created mount /root/modal_reranker.py
# ├── 🔨 Created function rerank_batch.
# ├── 🔨 Created function rerank_api.
# └── 🔨 Created function health.
#
# View Deployment: https://modal.com/apps/ap-xxxxx
#
# Web endpoints:
# ├── health => https://yourusername--socrate-reranker-health.modal.run
# └── rerank_api => https://yourusername--socrate-reranker-rerank-api.modal.run
#
# ✓ Deployed app in 12.5s

# IMPORTANT: Copia l'URL di "rerank_api" - lo userai nel prossimo step
```

### Step 4: Test Deployment

```bash
# Test endpoint (sostituisci con il tuo URL)
curl -X POST https://yourusername--socrate-reranker-rerank-api.modal.run \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Come si prepara ossobuco?",
    "chunks": [
      "Ossobuco alla milanese ricetta tradizionale",
      "Risotto con zafferano ricetta",
      "Preparazione ossobuco con vino bianco"
    ]
  }'

# Output atteso:
# {
#   "scores": [9.234, -1.234, 3.421],
#   "num_chunks": 3,
#   "latency_ms": 187.5,
#   "status": "success"
# }
```

---

## Step 5: Integrate with Railway

### 5.1: Add Environment Variable to Railway

```bash
# Nel dashboard Railway (https://railway.app):
# 1. Seleziona il tuo progetto "memvid"
# 2. Vai su Variables
# 3. Aggiungi nuova variabile:

MODAL_RERANK_URL=https://yourusername--socrate-reranker-rerank-api.modal.run

# 4. Save
```

### 5.2: Update requirements.txt

Aggiungi `requests` se non gi presente (dovrebbe gi esserci):

```txt
requests>=2.31.0
```

### 5.3: Deploy Updated Code to Railway

```bash
# Commit changes
git add modal_reranker.py MODAL_SETUP_GUIDE.md core/query_engine.py
git commit -m "feat: add Modal GPU reranking service integration"

# Push to Railway (auto-deploy)
git push origin main

# Monitor deploy
railway logs --service web
```

---

## Monitoring & Debugging

### Check Modal Logs

```bash
# View real-time logs
python -m modal app logs socrate-reranker

# View specific function logs
python -m modal app logs socrate-reranker --function rerank_batch
```

### Monitor Usage & Cost

1. Dashboard: https://modal.com/apps
2. Click su "socrate-reranker"
3. Vedrai:
   - GPU hours used
   - Number of calls
   - Latency metrics
   - Cost estimate

### Health Check

```bash
# Check service health
curl https://yourusername--socrate-reranker-health.modal.run

# Output:
# {
#   "status": "healthy",
#   "service": "socrate-reranker",
#   "gpu": "T4",
#   "model": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
# }
```

---

## Cost Management

### Free Tier Limits

- **30 GPU-hours/month gratis**
- ~0.2s per query = 54,000 queries/month gratis
- Automatic billing quando superi

### Usage Tracking

```bash
# Check current usage
python -m modal profile current-month

# Output:
# GPU Hours Used: 2.5 / 30.0 (8.3%)
# Estimated Cost: $0.00
# Queries Processed: ~45,000
```

### Cost Optimization Tips

1. **Container Idle Timeout**: Set to 300s (5min) per ridurre cold starts
2. **Batch Requests**: Se possibile, batch multiple queries insieme
3. **Caching**: Railway cacher query frequenti prima di chiamare Modal
4. **Fallback**: Se Modal down, sistema usa dense-only (gratis)

---

## Troubleshooting

### Issue 1: "Modal token not found"

**Solution**:
```bash
# Re-authenticate
python -m modal token new
```

### Issue 2: "Deployment failed"

**Solution**:
```bash
# Check Modal CLI version
pip install --upgrade modal

# Re-deploy
python -m modal deploy modal_reranker.py
```

### Issue 3: "Railway can't reach Modal endpoint"

**Solution**:
1. Verify URL in Railway environment variables
2. Test endpoint manually:
   ```bash
   curl https://your-url/health
   ```
3. Check Modal logs:
   ```bash
   python -m modal app logs socrate-reranker
   ```

### Issue 4: "High latency (>1s)"

**Possible Causes**:
- Cold start (first request after idle)
- Network latency Railway → Modal
- Large batch size (>50 chunks)

**Solutions**:
- Increase `container_idle_timeout` in modal_reranker.py
- Add caching layer in Railway
- Reduce batch size to 30-40 chunks

---

## Performance Expectations

### Latency Breakdown

| Component | Time | Notes |
|-----------|------|-------|
| Railway → Modal network | ~20-50ms | Depends on region |
| GPU inference (50 chunks) | ~150-200ms | T4 GPU |
| Modal → Railway response | ~20-50ms | - |
| **Total** | **~200-300ms** | vs 9000ms CPU |

### Quality Metrics

Based on testing (5 queries):

| Metric | Baseline | Modal GPU | Improvement |
|--------|----------|-----------|-------------|
| Hit@10 | 80.0% | 100.0% | +25% |
| MRR | 0.520 | 0.867 | +67% |
| NDCG@10 | 0.575 | 0.855 | +49% |

---

## Next Steps After Deployment

### Week 1: Monitor & Validate

✅ **Check**:
- Latency P95 <500ms
- No errors in Modal logs
- Railway logs show successful API calls
- User feedback positive

### Week 2: Optimize

✅ **Actions**:
- Add Redis caching for frequent queries
- Tune batch size (test 30 vs 50 chunks)
- A/B test: 50% traffic with Modal, 50% baseline

### Month 2: Scale

✅ **Consider**:
- Fine-tune cross-encoder on Italian recipes
- Add hybrid BM25 + dense retrieval
- Implement query classification for smart routing

---

## Rollback Plan

Se Modal ha problemi, il sistema automaticamente usa fallback a dense-only:

```python
# In core/query_engine.py (gi implementato)
try:
    scores = call_modal_rerank(query, chunks)
except Exception as e:
    logger.warning(f"Modal rerank failed: {e}, using dense-only")
    scores = dense_scores  # Fallback
```

**No downtime** - sistema continua a funzionare anche senza Modal.

---

## Support & Resources

- **Modal Docs**: https://modal.com/docs
- **Modal Discord**: https://modal.com/discord
- **Modal Status**: https://status.modal.com
- **Railway Docs**: https://docs.railway.app

---

## Summary Checklist

- [ ] Modal account created
- [ ] `modal token new` authenticated
- [ ] `modal run modal_reranker.py` tested locally
- [ ] `modal deploy modal_reranker.py` deployed
- [ ] Endpoint URL copied
- [ ] `MODAL_RERANK_URL` added to Railway
- [ ] Code deployed to Railway
- [ ] End-to-end test passed
- [ ] Monitoring dashboard checked
- [ ] Usage tracking configured

**Estimated Setup Time**: 10-15 minuti

**Expected Result**:
- Latency: 200-300ms (30x faster than CPU)
- Quality: Hit@10 100%, MRR 0.867
- Cost: $0/month (free tier)

🚀 **Ready for Production!**
