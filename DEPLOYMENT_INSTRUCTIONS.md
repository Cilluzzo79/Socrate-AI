# Modal + Railway Deployment - Step by Step Instructions

## Overview

Hai tutti i file pronti. Ora devi:
1. Autenticare Modal (richiede browser)
2. Deploy Modal service (1 comando)
3. Configurare Railway
4. Deploy codice aggiornato

**Tempo stimato**: 10 minuti

---

## STEP 1: Autentica Modal (Richiede Browser)

```bash
# Da terminale Windows
cd D:\railway\memvid

# Authenticate Modal - questo aprir il browser
python -m modal token new
```

**Cosa succede**:
1. Si apre browser su https://modal.com
2. Login con GitHub/Google (crea account se necessario)
3. Autorizza CLI
4. Token salvato automaticamente in `~/.modal.toml`

**Output atteso**:
```
Token created successfully!
```

---

## STEP 2: Test Modal Locally

```bash
# Test che tutto funziona (usa GPU cloud)
python -m modal run modal_reranker.py
```

**Output atteso**:
```
[TEST] Query: Come si prepara l'ossobuco alla milanese?
[TEST] Reranking 4 chunks...
[TEST] Scores:
  1. [9.234] L'ossobuco alla milanese...
  2. [3.421] La preparazione dell'ossobuco...
[TEST] Success! GPU reranking working correctly.
```

**Se fallisce**: Ri-autentica con `python -m modal token new`

---

## STEP 3: Deploy Modal Service

```bash
# Deploy to Modal cloud
python -m modal deploy modal_reranker.py
```

**Output atteso**:
```
✓ Created objects.
├── 🔨 Created function rerank_batch.
├── 🔨 Created function rerank_api.
└── 🔨 Created function health.

View Deployment: https://modal.com/apps/ap-xxxxx

Web endpoints:
├── health => https://yourusername--socrate-reranker-health.modal.run
└── rerank_api => https://yourusername--socrate-reranker-rerank-api.modal.run

✓ Deployed app in 12.5s
```

**IMPORTANTE**: **Copia l'URL di `rerank_api`** - esempio:
```
https://mau

ro--socrate-reranker-rerank-api.modal.run
```

---

## STEP 4: Test Modal Endpoint

```bash
# Test con curl (sostituisci URL con il tuo)
curl -X POST https://YOUR-URL-HERE/rerank_api ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"ossobuco\",\"chunks\":[\"ossobuco ricetta\",\"risotto ricetta\"]}"
```

**Output atteso**:
```json
{
  "scores": [9.234, -1.234],
  "num_chunks": 2,
  "latency_ms": 187.5,
  "status": "success"
}
```

---

## STEP 5: Configura Railway

### 5.1: Aggiungi Environment Variable

1. Vai su https://railway.app
2. Seleziona progetto "memvid"
3. Vai su **Variables**
4. Click **New Variable**
5. Aggiungi:
   ```
   Name: MODAL_RERANK_URL
   Value: https://YOUR-MODAL-URL-HERE/rerank_api
   ```
6. Click **Add**

**Verifica**: L'environment variable deve apparire nella lista

---

## STEP 6: Deploy Codice Aggiornato a Railway

### Opzione A: Git Push (Recommended)

```bash
cd D:\railway\memvid

# Stage files
git add modal_reranker.py
git add core/modal_rerank_client.py
git add MODAL_SETUP_GUIDE.md
git add DEPLOYMENT_INSTRUCTIONS.md

# Commit
git commit -m "feat: add Modal GPU reranking integration

- Add modal_reranker.py for serverless GPU inference
- Add modal_rerank_client.py for Railway integration
- Add fallback to dense-only if Modal unavailable
- Expected improvement: Hit@10 100%, MRR 0.867, latency 200-300ms"

# Push (triggers auto-deploy)
git push origin main
```

### Opzione B: Railway CLI

```bash
railway up
```

---

## STEP 7: Verifica Deployment

### 7.1: Check Railway Logs

```bash
# Monitor deploy logs
railway logs --service web | grep -i "modal\|rerank"
```

**Cosa cercare**:
```
[INFO] Modal rerank URL configured: https://...
[INFO] Modal GPU reranking enabled
```

### 7.2: Test End-to-End

Fai una query di test via Telegram o API:

**Query di test**: "Come si prepara l'ossobuco alla milanese?"

**Nel log Railway dovresti vedere**:
```
[MODAL-RERANK] Calling Modal API with 50 chunks
[MODAL-RERANK] Received scores in 234ms
[RERANKING SUCCESS] Selected 10 diverse chunks
```

---

## STEP 8: Monitor Performance

### Modal Dashboard

1. Vai su https://modal.com/apps
2. Click su "socrate-reranker"
3. Vedrai:
   - Numero di chiamate
   - Latency media
   - GPU hours utilizzate
   - Cost estimate

### Railway Dashboard

1. Vai su https://railway.app
2. Seleziona "memvid"
3. Click su "Metrics"
4. Verifica:
   - CPU usage stabile
   - Memory usage normale
   - No errors

---

## Troubleshooting

### Issue: "Modal token not found"

**Fix**:
```bash
python -m modal token new
```

### Issue: "Railway can't reach Modal"

**Check**:
1. Verifica URL in Railway Variables
2. Test endpoint manualmente:
   ```bash
   curl https://your-modal-url/health
   ```
3. Check Modal logs:
   ```bash
   python -m modal app logs socrate-reranker
   ```

### Issue: "High latency (>1s)"

**Possibili cause**:
- Cold start (prima richiesta dopo idle)
- Batch size troppo grande (>50 chunks)

**Fix**:
- Aspetta 30s (warm-up)
- Riduci batch size a 40 chunks

### Issue: "Modal deployment failed"

**Fix**:
```bash
# Upgrade Modal CLI
pip install --upgrade modal

# Re-deploy
python -m modal deploy modal_reranker.py
```

---

## Success Checklist

- [ ] Modal token autenticato
- [ ] `modal run` test passed
- [ ] `modal deploy` completato
- [ ] Modal endpoint URL copiato
- [ ] Railway environment variable aggiunta
- [ ] Codice committed e pushed
- [ ] Railway deployment completato
- [ ] Logs Railway mostrano "Modal enabled"
- [ ] Test end-to-end query passed
- [ ] Modal dashboard mostra chiamate

---

## Performance Targets

Dopo deployment, verifica metrics:

| Metric | Target | Come Verificare |
|--------|--------|-----------------|
| Latency P95 | <500ms | Railway logs |
| Hit@10 | >95% | User feedback |
| Modal GPU hours | <5 hours/week | Modal dashboard |
| Railway CPU | <80% | Railway metrics |
| Errors | 0% | Railway logs |

---

## Cost Tracking

### Week 1
- **Modal**: $0 (free tier)
- **Railway**: $5/month (existing)
- **Total**: $5/month

### Monitor
- Check Modal usage: https://modal.com/settings/billing
- Se superi 30 GPU-hours/month, costo aggiuntivo: ~$0.60/hour

---

## Rollback Plan

Se qualcosa va male:

### Disable Modal (Quick Fix)

```bash
# Railway dashboard → Variables → Remove MODAL_RERANK_URL
# Sistema usar automaticamente dense-only fallback
```

### Full Rollback

```bash
git revert HEAD
git push origin main
```

---

## Next Steps After Deployment

### Day 1-3: Monitor
- Check logs ogni ora
- Verify latency <500ms
- Check Modal usage
- User feedback

### Week 1: Optimize
- Tune batch size (30 vs 50)
- Add caching for frequent queries
- A/B test quality improvement

### Week 2: Expand
- Increase test set to 50 queries
- Evaluate Hybrid BM25 strategy
- Consider fine-tuning embeddings

---

## Support

- **Modal Docs**: https://modal.com/docs
- **Modal Discord**: https://modal.com/discord
- **Railway Docs**: https://docs.railway.app

---

**Estimated Total Time**: 10-15 minuti

**Expected Result**:
- ✅ Hit@10: 100% (+25%)
- ✅ MRR: 0.867 (+67%)
- ✅ Latency: 200-300ms (30x faster)
- ✅ Cost: $0/month (free tier)

🚀 **Ready to Deploy!**
