# Come Riprendere il Lavoro su Socrate AI
**Guida Rapida per Recuperare il Contesto**

---

## 🚀 CHECKLIST INIZIO SESSIONE

### 1. Aprire i File di Stato (2 minuti)
```
📂 D:\railway\memvid\STATO DEL PROGETTO SOCRATE\
   ├── ✅ STATO_PROGETTO.md          # Dove siamo, cosa fare ora
   ├── ✅ PIANO_AZIONE.md             # Roadmap completa
   └── ✅ COME_RIPRENDERE_LAVORO.md   # Questa guida
```

**Leggi nell'ordine:**
1. `STATO_PROGETTO.md` → sezione "DOVE SIAMO ADESSO"
2. `STATO_PROGETTO.md` → sezione "PROSSIMI PASSI IMMEDIATI"
3. `PIANO_AZIONE.md` → sezione del giorno corrente

---

### 2. Verificare Stato Servizi (3 minuti)

#### A) Railway Services
1. Vai su: https://railway.app
2. Apri progetto "Socrate AI"
3. Verifica che siano "Active":
   - ✅ Web Service
   - ✅ Worker Service
   - ✅ PostgreSQL
   - ✅ Redis

#### B) Test Rapido Sito
1. Apri: https://web-production-38b1c.up.railway.app/
2. Verifica che carichi (anche solo landing page)
3. Se errore 500 → guarda logs Railway

#### C) Link Railway CLI (se necessario)
```bash
cd /d/railway/memvid
railway link
# Seleziona: Socrate AI project
```

---

### 3. Controllare Cosa è Cambiato (2 minuti)

#### Git Status
```bash
cd /d/railway/memvid
git status
git log --oneline -5  # Ultimi 5 commit
```

#### Railway Logs (ultimi 10 minuti)
```bash
railway logs --service web --since 10m
railway logs --service worker --since 10m
```

---

## 📋 SCENARI COMUNI

### Scenario A: "Ho appena riavviato il PC"
**Problema**: Railway non linkato, contesto perso

**Soluzione**:
```bash
# 1. Vai nella cartella progetto
cd /d/railway/memvid

# 2. Link Railway
railway link

# 3. Apri file stato
code "STATO DEL PROGETTO SOCRATE/STATO_PROGETTO.md"

# 4. Continua da ultimo task
```

---

### Scenario B: "Sono passati giorni dall'ultima sessione"
**Problema**: Non ricordo cosa stavo facendo

**Soluzione**:
1. **Leggi** `STATO_PROGETTO.md` → "Ultima sessione"
2. **Controlla** `PIANO_AZIONE.md` → Settimana corrente
3. **Verifica** Railway → Se deploy è ancora online
4. **Testa** sito web → Se funziona ancora
5. **Guarda** logs → Se ci sono errori recenti

---

### Scenario C: "Ho fatto modifiche e non ricordo se ho fatto deploy"
**Problema**: Codice locale ≠ codice produzione?

**Soluzione**:
```bash
# 1. Verifica git
git status
git diff origin/main

# 2. Se ci sono modifiche non committate
git add .
git commit -m "Descrizione modifiche"

# 3. Push su GitHub (trigger auto-deploy Railway)
git push origin main

# 4. Monitora deploy su Railway
railway logs --service web
```

---

### Scenario D: "Il sito è down / errore 500"
**Problema**: Servizio non risponde

**Soluzione**:
```bash
# 1. Controlla logs
railway logs --service web --since 30m

# 2. Cerca errori tipo:
#    - "ModuleNotFoundError"
#    - "Connection refused"
#    - "Environment variable ... not set"

# 3. Se database error
railway logs --service postgres

# 4. Se worker error
railway logs --service worker

# 5. Riavvia servizio da Railway dashboard se necessario
```

---

### Scenario E: "Upload file non funziona"
**Problema**: Errore durante upload documento

**Soluzione**:
```bash
# 1. Test connessione R2
cd /d/railway/memvid
python test_r2_connection.py

# 2. Se fallisce, verifica variabili Railway
railway variables | grep R2

# 3. Controlla Cloudflare R2 dashboard
# https://dash.cloudflare.com/
# Verifica bucket "socrate-ai-storage" esiste

# 4. Guarda logs upload
railway logs --service web | grep -i "upload\|r2\|error"
```

---

## 🎯 WORKFLOW TIPO SESSIONE DI LAVORO

### 1. Setup Iniziale (5 minuti)
```bash
# Vai nella cartella
cd /d/railway/memvid

# Aggiorna da GitHub
git pull origin main

# Verifica Railway linkato
railway link

# Apri editor
code .
```

### 2. Rivedi Contesto (5 minuti)
- Leggi `STATO_PROGETTO.md`
- Identifica task da fare oggi
- Controlla se ci sono bug aperti

### 3. Lavora sul Task (60-120 minuti)
- Sviluppa feature/fix
- Testa in locale (se possibile)
- Committa spesso con messaggi chiari

### 4. Deploy e Test (10 minuti)
```bash
# Commit
git add .
git commit -m "Descrizione chiara"
git push origin main

# Monitora deploy
railway logs --service web

# Test su produzione
# Apri https://web-production-38b1c.up.railway.app/
```

### 5. Aggiorna Documentazione (5 minuti)
```bash
# Aggiorna STATO_PROGETTO.md
# - Spunta task completati
# - Aggiungi problemi risolti
# - Aggiorna "Ultima sessione"

# Commit modifiche
git add "STATO DEL PROGETTO SOCRATE/"
git commit -m "docs: aggiorna stato progetto"
git push origin main
```

---

## 🔧 COMANDI RAPIDI DA SALVARE

### Railway
```bash
# Link progetto
railway link

# Logs real-time
railway logs --service web -f
railway logs --service worker -f

# Variabili
railway variables

# Riavvia servizio (da dashboard)
# https://railway.app → Services → Restart
```

### Git
```bash
# Status veloce
git status -s

# Commit veloce
git add . && git commit -m "msg" && git push

# Vedi differenze
git diff
git diff HEAD~1  # Ultimo commit

# Torna indietro (ATTENZIONE!)
git reset --hard HEAD~1
```

### Test Locali
```bash
# Test connessione R2
python test_r2_connection.py

# Test encoder memvid (locale)
python process_test.py

# Run Flask locale
python api_server.py
# Apri http://localhost:5000
```

---

## 📞 RIFERIMENTI VELOCI

### URLs Importanti
- **Sito produzione**: https://web-production-38b1c.up.railway.app/
- **Railway dashboard**: https://railway.app
- **GitHub repo**: https://github.com/Cilluzzo79/Socrate-AI
- **Cloudflare R2**: https://dash.cloudflare.com/

### File Chiave
- **Stato progetto**: `STATO DEL PROGETTO SOCRATE/STATO_PROGETTO.md`
- **Piano azione**: `STATO DEL PROGETTO SOCRATE/PIANO_AZIONE.md`
- **Guida completa**: `GUIDA_COMPLETA_SISTEMA.MD`
- **API server**: `api_server.py`
- **Celery tasks**: `tasks.py`
- **Storage R2**: `core/s3_storage.py`

---

## 💡 TIPS & TRICKS

### Tip 1: Usa TODO Comments nel Codice
```python
# TODO(15-ott): Implementare retry logic per R2 upload
# FIXME(14-ott): Worker non processa se file > 100MB
# NOTE(13-ott): Questa funzione è temporanea, da refactorare
```

### Tip 2: Committa Spesso
Non aspettare di finire tutto. Commit piccoli e frequenti:
```bash
git commit -m "feat: aggiungi upload progress"
git commit -m "fix: risolvi errore R2 NoSuchBucket"
git commit -m "docs: aggiorna stato progetto"
```

### Tip 3: Tag Git per Milestone
```bash
git tag -a v0.2.0 -m "Fase 2 completata: Storage funzionante"
git push origin v0.2.0
```

### Tip 4: Usa Railway Logs per Debug
```bash
# Filtra solo errori
railway logs --service web | grep -i error

# Cerca una specifica keyword
railway logs --service worker | grep -i "document.*processing"

# Ultimi 100 log
railway logs --service web --tail 100
```

### Tip 5: Backup Database Periodico
```bash
# Ogni venerdì
railway connect postgres
# Poi in psql:
\copy documents TO '/tmp/documents_backup.csv' CSV HEADER;
```

---

## ⚠️ COSA NON FARE

❌ **NON committare**:
- File `.env` con credenziali
- `__pycache__/` directory
- File temporanei `.swp`, `.DS_Store`
- Dati sensibili utenti

❌ **NON modificare direttamente**:
- Database produzione senza backup
- Variabili Railway senza verificare impatto
- File su R2 manualmente (usa sempre API)

❌ **NON deployare senza**:
- Aver testato in locale (quando possibile)
- Aver controllato che test passino
- Aver letto i logs prima

---

## 🎯 OBIETTIVO FINALE

**Al termine di ogni sessione**:
1. ✅ Codice committato e pushato
2. ✅ Deploy completato senza errori
3. ✅ Test funzionale su produzione
4. ✅ STATO_PROGETTO.md aggiornato
5. ✅ Prossimi step identificati

---

**Versione**: 1.0
**Creato**: 15 Ottobre 2025
**Prossimo update**: Quando cambiano workflow significativi
