# Istruzioni Test Produzione - Inline Embeddings Fix

**Data**: 17 Ottobre 2025
**Versione**: v2.1 (Inline Embeddings)

---

## STATO ATTUALE

### ✅ COMPLETATO
1. **Codice deployato su Railway**
   - Commit: `562406f fix: implement inline embeddings to solve OOM query crashes`
   - File modificati:
     - `core/embedding_generator.py` - nuova funzione `generate_and_save_embeddings_inline()`
     - `tasks.py` - usa embeddings inline invece di file separati

2. **Configurazione Railway**
   - `ENABLE_EMBEDDINGS=true` già configurato sul servizio `web`

3. **Test locali PASSATI**
   - Embedding generation: ✅ PASSED
   - Query engine compatibility: ✅ PASSED
   - File size estimate: ~11.66 MB per 1448 chunks

---

## ⚠️ AZIONE RICHIESTA: Riprocessare Documenti Esistenti

### Problema
I documenti caricati PRIMA del deploy (come `124c073e-10ea-4b39-b17e-4947b55ce6af` con 1448 chunks) hanno un `metadata.json` che **NON contiene embeddings inline**.

Quando fai una query su questi documenti vecchi:
1. Sistema scarica metadata.json da R2
2. NON trova `chunk['embedding']`
3. Ricalcola TUTTI gli embeddings on-the-fly
4. Worker timeout dopo 120 secondi → SIGKILL/OOM

### Soluzione: Eliminare e Ricaricare

#### Step 1: Identifica Documenti da Riprocessare
```bash
# Controlla quali documenti sono stati caricati prima del 17 ottobre ore 12:30
railway logs --service web 2>&1 | grep "Document uploaded"
```

Output attuale mostra:
```
2025-10-17 12:14:04 - Document uploaded: 124c073e-10ea-4b39-b17e-4947b55ce6af
```

Questo documento è stato caricato alle 12:14, PRIMA del deploy del codice (che è stato dopo), quindi va riprocessato.

#### Step 2: Elimina Documento Vecchio
1. Vai su: https://web-production-38b1c.up.railway.app/
2. Login con Telegram
3. Trova documento "Frammenti di un insegnamento sconosciuto.pdf" (4.7MB, 1448 chunks)
4. Clicca sull'icona cestino 🗑️
5. Conferma eliminazione

#### Step 3: Ricarica Documento
1. Clicca "Carica Documento"
2. Seleziona lo stesso file PDF
3. Aspetta completamento processing

**Tempo stimato**: ~12-15 minuti per 1448 chunks
- Encoding: ~5 minuti
- **Inline embeddings generation**: ~8-10 minuti (0.5s/chunk × 1448)
- Upload metadata a R2: ~30 secondi

#### Step 4: Verifica Embeddings Inline
Durante il processing, controlla i logs Railway:
```bash
railway logs --service web 2>&1 | grep -E "(Generating inline embeddings|✅ Saved.*chunks with inline embeddings)"
```

Dovresti vedere:
```
Generating INLINE embeddings for 1448 chunks...
✅ Saved 1448 chunks with inline embeddings
```

#### Step 5: Test Query Performance
1. Vai alla dashboard
2. Clicca "Strumenti" sul documento ricaricato
3. Prova una query: "Di cosa parla la legge del tre?"
4. Aspetta risposta

**Performance attesa**:
- Query OLD (senza embeddings inline): TIMEOUT dopo 120s → CRASH ❌
- Query NEW (con embeddings inline): **<5 secondi** ✅

---

## VERIFICA TECNICA

### Come Verificare che il Metadata Contiene Embeddings Inline

1. **Download metadata da R2**:
   ```bash
   # Dopo aver ricaricato il documento, scarica il metadata
   # (sostituisci con l'ID documento reale)
   railway logs --service web 2>&1 | grep "File uploaded to R2.*metadata.json"
   ```

2. **Controlla dimensione metadata**:
   - Senza embeddings: ~1.9 MB (come ora)
   - **Con embeddings inline**: ~13-14 MB (+11.66 MB di embeddings)

3. **Log key da cercare**:
   ```
   ✅ Saved 1448 chunks with inline embeddings
   File uploaded to R2: users/.../metadata.json (13000000+ bytes)
   ```

---

## TIMELINE COMPLETA

### Fino ad Ora
- ✅ Identificato root cause: query engine ricalcola embeddings
- ✅ Implementato inline embeddings in `embedding_generator.py`
- ✅ Aggiornato `tasks.py` per usare nuova funzione
- ✅ Testato localmente: ALL TESTS PASSED
- ✅ Deployato su Railway
- ✅ Configurato `ENABLE_EMBEDDINGS=true`

### Prossimi Step (IN ATTESA DI ESECUZIONE)
- ⏳ Eliminare documento vecchio 124c073e
- ⏳ Ricaricare stesso PDF
- ⏳ Verificare processing con embeddings inline
- ⏳ Testare query performance (<5s)

---

## TROUBLESHOOTING

### Se il Processing Fallisce
Controlla logs Railway per errori:
```bash
railway logs --service web 2>&1 | tail -100
```

Possibili problemi:
1. **OOM durante embedding generation**: ridurre `max_chunks_per_batch` da 50 a 25 in `embedding_generator.py:219`
2. **Timeout worker**: aumentare timeout Gunicorn (attuale: 120s)
3. **R2 upload failed**: verificare credenziali R2

### Se la Query è Ancora Lenta
Verifica che il metadata scaricato contenga embeddings:
```python
# In Railway logs cerca:
"Loaded metadata: 1448 chunks"
```

Poi controlla se query engine ricalcola embeddings:
- Se vedi `Batches: 0%|  | 0/46` → embeddings NON inline ❌
- Se query completa in <5s → embeddings inline funzionano ✅

---

## RISULTATI ATTESI

### Prima (Situazione Attuale)
```
Query: "Di cosa parla la legge del tre?"
Status: processing...
Progress: 28% (batch 13/46)
Time elapsed: 1m 56s
Result: WORKER TIMEOUT → SIGKILL ❌
```

### Dopo Fix
```
Query: "Di cosa parla la legge del tre?"
Status: processing...
Progress: Searching chunks... (instant)
Time elapsed: 2-4s
Result: [Risposta completa dal LLM] ✅
```

---

## METRICHE DI SUCCESSO

- ✅ Query su documenti 1000+ chunks completa in <10 secondi
- ✅ Zero worker crashes/SIGKILL
- ✅ Metadata.json contiene embeddings inline (~11-12 MB per 1448 chunks)
- ✅ Processing time accettabile (~12-15 minuti per 4.7MB PDF)

---

## CONTATTI E SUPPORTO

**Report creato da**: Claude Code
**File correlati**:
- `REPORT_17_OTT_2025_EMBEDDINGS_FIX.md` - analisi tecnica completa
- `test_inline_embeddings.py` - script di test locale
- `CLAUDE.md` - guida al progetto

**Per problemi**: Controllare Railway logs e confrontare con metriche attese sopra.
