# 🚀 Railway Deployment - Step by Step Guide

**Progetto**: Socrate AI Multi-tenant con Async Processing
**Data**: 13 Ottobre 2025
**Tempo stimato**: 20-30 minuti

---

## ✅ Pre-requisiti Verificati

- [x] Tutti i file deployment pronti
  - [x] `Procfile` (web service)
  - [x] `Procfile.worker` (celery worker)
  - [x] `railway.json` (configurazione)
  - [x] `requirements_multitenant.txt` (dipendenze)
- [x] Codice testato localmente
  - [x] Database operations ✅
  - [x] Celery + Redis integration ✅
  - [x] Task registration ✅
- [x] Repository GitHub pronto

---

## 📋 Step 1: Verifica Repository GitHub

### 1.1 Controlla status git

```bash
git status
```

**Verifica**:
- Tutti i file sono committati?
- Nessun file importante è in `.gitignore`?

### 1.2 Files da NON committare

Assicurati che `.gitignore` contenga:
```
.env
*.db
__pycache__/
*.pyc
venv/
storage/
storage_test/
*.log
```

### 1.3 Push al repository

```bash
# Se hai modifiche non salvate:
git add .
git commit -m "Deploy: Async implementation ready for Railway"
git push origin master
```

**✅ Checkpoint**: Codice su GitHub aggiornato

---

## 🚂 Step 2: Crea Progetto Railway

### 2.1 Accedi a Railway

1. Vai su https://railway.app
2. Login con GitHub
3. Dashboard → **"New Project"**

### 2.2 Connetti Repository

1. Click **"Deploy from GitHub repo"**
2. Seleziona repository: `Datapdfimg` (o il tuo nome repo)
3. Railway inizierà automaticamente il deploy

**⚠️ IMPORTANTE**: Il primo deploy FALLIRÀ - è normale! Mancano le variabili d'ambiente.

**✅ Checkpoint**: Progetto Railway creato, servizio "web" in errore (expected)

---

## 🗄️ Step 3: Aggiungi PostgreSQL

### 3.1 Crea Database

1. Nel dashboard Railway, click **"+ New"**
2. Seleziona **"Database"**
3. Seleziona **"Add PostgreSQL"**
4. Railway crea automaticamente il database

### 3.2 Verifica DATABASE_URL

1. Click sul servizio PostgreSQL
2. Tab **"Variables"**
3. Cerca `DATABASE_URL` - dovrebbe essere auto-generato
4. Formato: `postgresql://user:password@host:5432/railway`

**✅ Checkpoint**: PostgreSQL creato con DATABASE_URL disponibile

---

## 🔴 Step 4: Aggiungi Redis

### 4.1 Crea Redis Service

1. Click **"+ New"** di nuovo
2. Seleziona **"Database"**
3. Seleziona **"Add Redis"**
4. Railway crea automaticamente Redis

### 4.2 Verifica REDIS_URL

1. Click sul servizio Redis
2. Tab **"Variables"**
3. Cerca `REDIS_URL` - dovrebbe essere auto-generato
4. Formato: `redis://default:password@host:6379`

**✅ Checkpoint**: Redis creato con REDIS_URL disponibile

---

## ⚙️ Step 5: Configura Web Service (Flask API)

### 5.1 Vai alle Variables del Web Service

1. Click sul servizio **"memvid"** o **"web"** (il primo servizio creato)
2. Tab **"Settings"** → **"Variables"**

### 5.2 Aggiungi Variabili d'Ambiente

Click **"+ New Variable"** per ognuna:

```bash
# Telegram Bot (OBBLIGATORIO)
TELEGRAM_BOT_TOKEN=<il-tuo-bot-token-da-@BotFather>
BOT_USERNAME=<il-tuo-bot-username>  # Esempio: SocrateAIBot

# AI Provider (OBBLIGATORIO - almeno uno)
OPENAI_API_KEY=sk-...
# OPPURE
ANTHROPIC_API_KEY=sk-ant-...

# Flask (OBBLIGATORIO)
SECRET_KEY=<genera-stringa-random-32-caratteri>
# Usa: python -c "import secrets; print(secrets.token_hex(32))"

FLASK_ENV=production
FLASK_DEBUG=False

# Storage
STORAGE_PATH=/app/storage

# Database e Redis (AUTO-GENERATI da Railway)
# Questi dovrebbero essere già presenti:
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Port (AUTO-GENERATO da Railway)
PORT=<lascia vuoto, Railway lo setta automaticamente>
```

### 5.3 Verifica Variabili Essenziali

**Devono essere presenti**:
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `BOT_USERNAME`
- ✅ `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`
- ✅ `SECRET_KEY`
- ✅ `DATABASE_URL` (auto-generato)
- ✅ `REDIS_URL` (auto-generato)

### 5.4 Redeploy Web Service

1. Tab **"Deployments"**
2. Click **"Deploy"** (o aspetta auto-deploy)
3. Monitora i logs

**✅ Checkpoint**: Web service deployed e running (controlla logs)

---

## 👷 Step 6: Aggiungi Celery Worker Service

### 6.1 Crea Worker Service

1. Click **"+ New"** nel progetto
2. Seleziona **"Empty Service"**
3. Nome: `worker` o `celery-worker`

### 6.2 Connetti al Repository

1. Nel worker service, vai su **"Settings"** → **"Source"**
2. Click **"Connect Repo"**
3. Seleziona lo stesso repository (`Datapdfimg`)
4. Branch: `master` (o il tuo branch)

### 6.3 Configura Start Command

1. Vai su **"Settings"** → **"Deploy"**
2. **Start Command**:
   ```bash
   celery -A celery_config worker --loglevel=info --concurrency=2
   ```
3. **Health Check**: Disabilitato (i worker non hanno HTTP endpoint)

### 6.4 Copia Variables dal Web Service

**IMPORTANTE**: Il worker ha bisogno delle STESSE variabili del web service!

1. Nel web service, vai su **"Variables"**
2. Copia TUTTE le variabili (puoi usare il bottone "Copy All")
3. Nel worker service, vai su **"Variables"**
4. Incolla tutte le variabili

**Variabili essenziali per worker**:
- ✅ `REDIS_URL` (per comunicare con Redis)
- ✅ `DATABASE_URL` (per aggiornare documenti)
- ✅ `TELEGRAM_BOT_TOKEN` (se serve)
- ✅ `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`
- ✅ `STORAGE_PATH=/app/storage`

### 6.5 Deploy Worker

1. Click **"Deploy"** nel worker service
2. Monitora i logs - dovrebbe mostrare:
   ```
   celery@worker ready.
   [tasks]
     . tasks.process_document_task
     . tasks.cleanup_old_documents
   ```

**✅ Checkpoint**: Worker service deployed e pronto

---

## 🧪 Step 7: Verifica Deployment

### 7.1 Controlla Tutti i Servizi

Nel dashboard Railway dovresti vedere:
- ✅ **memvid** (web) - Status: Running, Green
- ✅ **PostgreSQL** - Status: Running, Green
- ✅ **Redis** - Status: Running, Green
- ✅ **worker** - Status: Running, Green

### 7.2 Testa Health Endpoint

1. Nel web service, trova l'URL pubblico (es: `https://memvid-production.up.railway.app`)
2. Apri browser o usa curl:
   ```bash
   curl https://your-app.up.railway.app/api/health
   ```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "Socrate AI Multi-tenant API",
  "version": "1.0.0"
}
```

### 7.3 Controlla Logs

**Web Service Logs** (dovrebbe mostrare):
```
[INFO] Starting Socrate AI API server on port 8080
[INFO] Bot Username: YourBot
[INFO] Storage Path: /app/storage
 * Running on http://0.0.0.0:8080
```

**Worker Logs** (dovrebbe mostrare):
```
[INFO] Connected to redis://...
[INFO] celery@worker ready.
[INFO] registered tasks:
  - tasks.process_document_task
  - tasks.cleanup_old_documents
```

**✅ Checkpoint**: Tutti i servizi running, logs OK

---

## 🎯 Step 8: Test Completo End-to-End

### 8.1 Accedi alla Web UI

1. Apri l'URL pubblico del web service
2. Dovresti vedere la landing page con Telegram Login Widget

### 8.2 Configura Telegram Domain (IMPORTANTE!)

Prima del login, devi configurare il dominio su Telegram:

1. Apri Telegram → cerca @BotFather
2. Invia: `/setdomain`
3. Seleziona il tuo bot
4. Inserisci il dominio Railway (SENZA https://):
   ```
   your-app.up.railway.app
   ```
5. @BotFather confermerà: "Success!"

### 8.3 Test Login

1. Click **"Accedi con Telegram"**
2. Autorizza il bot
3. Dovresti essere reindirizzato alla dashboard

**Se fallisce**: Controlla che `TELEGRAM_BOT_TOKEN` e `BOT_USERNAME` siano corretti

### 8.4 Test Upload Documento

1. Nella dashboard, click **"Carica Documento"**
2. Seleziona un PDF di test (piccolo, 1-2 pagine)
3. Click **"Carica"**
4. Osserva la progress bar:
   - Dovrebbe mostrare "Elaborazione in corso..."
   - Progress bar dovrebbe aggiornarsi
   - Dopo 30-60 secondi: "Documento pronto!"

### 8.5 Verifica Logs Worker

Mentre il documento è in processing:

1. Vai su Railway → Worker service → Logs
2. Dovresti vedere:
   ```
   [INFO] Starting document processing: <doc-id>
   [INFO] Processing document: filename.pdf
   [INFO] Running memvid encoder...
   [INFO] Memvid encoder completed successfully
   [INFO] Document processing completed: <doc-id>
   ```

**✅ Checkpoint**: Upload funziona, processing async OK!

---

## 🐛 Troubleshooting Comune

### Problema: Web service non si avvia

**Sintomi**: Logs mostrano errori di import

**Soluzione**:
1. Verifica che `requirements_multitenant.txt` sia corretto
2. Controlla `railway.json` buildCommand
3. Redeploy

### Problema: Worker non processa task

**Sintomi**: Task rimane in "processing" per sempre

**Soluzione**:
1. Verifica worker logs - è in esecuzione?
2. Controlla che `REDIS_URL` sia corretto in entrambi i servizi
3. Verifica che worker abbia accesso al database (`DATABASE_URL`)
4. Redeploy worker

### Problema: Database connection failed

**Sintomi**: Errore "connection refused" o "authentication failed"

**Soluzione**:
1. Verifica che PostgreSQL service sia running
2. Controlla che `DATABASE_URL` sia presente nel web service
3. Format corretto: `postgresql://user:pass@host:5432/railway`

### Problema: Telegram login fallisce

**Sintomi**: "Authentication failed" o redirect non funziona

**Soluzione**:
1. Verifica `TELEGRAM_BOT_TOKEN` sia corretto (copia da @BotFather)
2. Verifica `BOT_USERNAME` sia corretto (SENZA @)
3. Configura domain su @BotFather con `/setdomain`
4. Usa dominio Railway senza `https://`

### Problema: File upload fallisce

**Sintomi**: Errore durante upload

**Soluzione**:
1. Controlla `STORAGE_PATH=/app/storage` sia settato
2. Verifica storage quota utente nel database
3. Controlla logs per errori specifici

---

## 📊 Monitoraggio Post-Deployment

### Metriche da Monitorare

**Web Service**:
- Response time: < 1s per la maggior parte delle richieste
- Error rate: < 1%
- Uptime: > 99%

**Worker Service**:
- Task completion rate: > 95%
- Average processing time: 30s - 5min
- Error rate: < 5%

**Database**:
- Connection pool: < 80% utilizzo
- Query time: < 100ms media
- Storage: Crescita controllata

**Redis**:
- Memory usage: < 100MB per pochi utenti
- Connections: < 50
- Hit rate: > 80%

### Railway Monitoring

1. Dashboard → Metrics
2. Controlla CPU, Memory, Network per ogni servizio
3. Setup alerts per errori critici

---

## ✅ Deployment Completato!

Se hai completato tutti gli step:

- ✅ Web service running
- ✅ Worker service running
- ✅ PostgreSQL connesso
- ✅ Redis connesso
- ✅ Telegram login funzionante
- ✅ Upload e processing async funzionante

**Congratulazioni! 🎉**

Il sistema è in produzione e funzionante!

---

## 📚 Risorse

- **Railway Docs**: https://docs.railway.app
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Implementation Summary**: `ASYNC_IMPLEMENTATION_SUMMARY.md`
- **Troubleshooting**: `ASYNC_DEPLOYMENT_CHECKLIST.md`

---

## 🎯 Prossimi Step (Opzionali)

1. **Custom Domain**: Configura dominio personalizzato
2. **Monitoring**: Setup Sentry o New Relic
3. **Scaling**: Aumenta worker concurrency se necessario
4. **Celery Beat**: Aggiungi scheduled tasks per cleanup
5. **Backup**: Configura backup automatici database
6. **CDN**: Setup CDN per file statici

---

**Buon Deploy! 🚀**
