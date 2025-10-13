# 🚀 Socrate AI - Guida al Deployment su Railway

## 📋 Indice
1. [Prerequisiti](#prerequisiti)
2. [Setup Locale](#setup-locale)
3. [Deployment Railway](#deployment-railway)
4. [Configurazione Bot Telegram](#configurazione-bot-telegram)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisiti

### Account Necessari
- ✅ Account [Railway](https://railway.app)
- ✅ Bot Telegram (via [@BotFather](https://t.me/botfather))
- ✅ API Key OpenAI o Anthropic
- ✅ Account GitHub (per deploy automatico)

### Software Richiesto (per sviluppo locale)
- Python 3.10+
- PostgreSQL 14+ (opzionale, per test locale)
- Git

---

## 2. Setup Locale

### Step 1: Clone Repository
```bash
git clone https://github.com/Cilluzzo79/Datapdfimg.git
cd memvid
```

### Step 2: Crea Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Installa Dipendenze
```bash
pip install -r requirements_multitenant.txt
```

### Step 4: Configura Environment Variables
Copia `.env.example` in `.env` e compila:

```bash
cp .env.example .env
```

Modifica `.env`:
```env
TELEGRAM_BOT_TOKEN=<il-tuo-bot-token>
BOT_USERNAME=<il-tuo-bot-username>
OPENAI_API_KEY=<la-tua-api-key>
SECRET_KEY=<genera-una-chiave-random>
DATABASE_URL=sqlite:///socrate_dev.db
STORAGE_PATH=./storage
```

### Step 5: Inizializza Database
```bash
python -c "from core.database import init_db; init_db()"
```

### Step 6: Test Locale
```bash
python api_server.py
```

Apri browser: `http://localhost:5000`

---

## 3. Deployment Railway

### Step 1: Crea Progetto Railway
1. Vai su [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Seleziona **"Deploy from GitHub repo"**
4. Autorizza GitHub e seleziona il repository `Datapdfimg`

### Step 2: Aggiungi Database e Redis

#### PostgreSQL
1. Nel progetto Railway, click **"+ New"**
2. Seleziona **"Database" → "PostgreSQL"**
3. Railway creerà automaticamente `DATABASE_URL`

#### Redis (per Celery)
1. Click **"+ New"** di nuovo
2. Seleziona **"Database" → "Redis"**
3. Railway creerà automaticamente `REDIS_URL`

### Step 3: Aggiungi Servizio Celery Worker

1. Click **"+ New"** → "Empty Service"
2. Nomina il servizio **"worker"**
3. Connettilo al tuo repository GitHub
4. Vai su **"Settings" → "Deploy"**:
   - **Start Command**: `celery -A celery_config worker --loglevel=info --concurrency=2`
5. Copia tutte le variabili d'ambiente dal servizio "web" al servizio "worker"

### Step 4: Configura Environment Variables
Nel dashboard Railway, vai su **Variables** e aggiungi (su ENTRAMBI i servizi "web" e "worker"):

```
TELEGRAM_BOT_TOKEN=<il-tuo-bot-token>
BOT_USERNAME=<il-tuo-bot-username>
OPENAI_API_KEY=<la-tua-api-key>
SECRET_KEY=<genera-chiave-random-per-produzione>
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
STORAGE_PATH=/app/storage
REDIS_URL=<auto-generato-da-railway>
DATABASE_URL=<auto-generato-da-railway>
```

**IMPORTANTE**: `DATABASE_URL` e `REDIS_URL` sono auto-generati da Railway.

### Step 5: Configura Build
Railway leggerà automaticamente:
- `railway.json` per configurazione
- `Procfile` per comando di start (servizio web)
- `Procfile.worker` per configurazione worker
- `requirements_multitenant.txt` per dipendenze

Verifica che `railway.json` esista:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements_multitenant.txt"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 100
  }
}
```

### Step 6: Deploy
1. Railway inizierà il deployment automaticamente
2. Monitora i logs in tempo reale
3. Una volta completato, Railway fornirà un URL pubblico

---

## 4. Configurazione Bot Telegram

### Step 1: Configura Webhook (Opzionale)
Se vuoi che il bot Telegram funzioni via webhook invece di polling:

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://<il-tuo-dominio-railway>.up.railway.app/telegram/webhook"
```

### Step 2: Configura Telegram Login Widget
1. Vai su [@BotFather](https://t.me/botfather)
2. Usa comando `/setdomain`
3. Seleziona il tuo bot
4. Inserisci il dominio Railway: `<il-tuo-progetto>.up.railway.app`

Questo abiliterà il Telegram Login Widget sul tuo sito.

### Step 3: Test Bot
1. Cerca il tuo bot su Telegram
2. Invia `/start`
3. Verifica che risponda

---

## 5. Testing

### Test Health Check
```bash
curl https://<il-tuo-dominio>.up.railway.app/api/health
```

Risposta attesa:
```json
{
  "status": "healthy",
  "service": "Socrate AI Multi-tenant API",
  "version": "1.0.0"
}
```

### Test Login Web
1. Vai su `https://<il-tuo-dominio>.up.railway.app`
2. Click "Login con Telegram"
3. Autorizza il bot
4. Dovresti essere reindirizzato alla dashboard

### Test Upload Documento
1. Dalla dashboard, click "Carica Documento"
2. Seleziona un PDF di test
3. Verifica che appaia in elaborazione
4. Attendi che diventi "Pronto"

### Test Processing Asincrono (Celery)

#### Setup Locale con Docker Compose
```bash
# Avvia Redis e PostgreSQL
docker-compose -f docker-compose.dev.yml up redis postgres -d

# Terminal 1: Avvia Celery Worker
celery -A celery_config worker --loglevel=info

# Terminal 2: Avvia Flask API
python api_server.py

# Terminal 3: Monitora Redis
redis-cli MONITOR
```

#### Test Flow Completo
1. Carica un documento dalla dashboard
2. Osserva i log del worker Celery:
   ```
   [INFO] Starting document processing: <doc_id> for user <user_id>
   [INFO] Processing document: filename.pdf
   [INFO] Running memvid encoder...
   [INFO] Memvid encoder completed successfully
   [INFO] Document processing completed: <doc_id>
   ```
3. La progress bar nel frontend dovrebbe aggiornarsi in tempo reale
4. Dopo il completamento, il documento apparirà con status "Pronto"

#### Verifica Celery Status
```bash
# Controlla worker attivi
celery -A celery_config inspect active

# Controlla task registrati
celery -A celery_config inspect registered

# Controlla stats
celery -A celery_config inspect stats
```

---

## 6. Struttura Progetto

```
memvid/
├── api_server.py              # Main Flask app con autenticazione
├── Procfile                   # Railway start command
├── railway.json               # Railway configuration
├── requirements_multitenant.txt
├── .env.example
│
├── core/
│   ├── database.py            # SQLAlchemy models (User, Document, ChatSession)
│   ├── document_operations.py # Multi-tenant document ops
│   ├── rag_wrapper.py         # RAG pipeline wrapper
│   ├── content_generators.py  # Quiz, summary, mindmap generators
│   └── llm_client.py          # OpenAI/Anthropic client
│
├── templates/
│   ├── index.html             # Landing page con Telegram Login
│   └── dashboard.html         # Main dashboard
│
├── static/
│   ├── css/
│   └── js/
│       └── dashboard.js       # Frontend logic
│
└── memvidBeta/               # Codice esistente (integrato via wrapper)
    └── chat_app/
        ├── core/
        │   └── rag_pipeline_robust.py
        └── ...
```

---

## 7. Troubleshooting

### Problema: "Database not found"
**Soluzione**: Verifica che Railway PostgreSQL sia collegato e `DATABASE_URL` sia settato.

```bash
# Nel Railway dashboard, vai su Variables e verifica DATABASE_URL
# Dovrebbe essere simile a: postgresql://user:pass@host:5432/railway
```

### Problema: "Telegram auth failed"
**Soluzione**:
1. Verifica `TELEGRAM_BOT_TOKEN` in Railway Variables
2. Assicurati di aver configurato il dominio in @BotFather
3. Controlla che `BOT_USERNAME` sia corretto (senza @)

### Problema: "Storage quota exceeded"
**Soluzione**: Railway ha un volume limitato. Configura storage esterno (S3):

```python
# In api_server.py, modifica STORAGE_PATH per usare S3
import boto3
s3 = boto3.client('s3')
# ... implementa upload su S3
```

### Problema: "memvid not available"
**Soluzione**: Il wrapper RAG è configurato per funzionare anche senza memvidBeta:

1. Verifica che `memvidBeta` sia nella directory
2. Controlla i logs per errori di import
3. In alternativa, il sistema userà risposte placeholder

---

## 8. Monitoraggio e Logs

### Visualizza Logs Railway
```bash
# Installa Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link progetto
railway link

# Tail logs
railway logs
```

### Metriche Utili
- **Uptime**: Monitora health check `/api/health`
- **Database Size**: Controlla storage PostgreSQL
- **Error Rate**: Filtra logs per "ERROR"

---

## 9. Prossimi Passi

### Funzionalità Implementate ✓
- [x] Integrazione completa memvid encoder per documenti caricati
- [x] Processing asincrono documenti (Celery + Redis)
- [x] Status polling in tempo reale (frontend)
- [x] Multi-tenant database con isolamento dati
- [x] Autenticazione Telegram Login Widget

### Funzionalità da Implementare
- [ ] Integrazione RAG pipeline per query/tools
- [ ] Storage S3 per file grandi
- [ ] Rate limiting per tier free/pro
- [ ] Analytics dashboard
- [ ] Telegram bot handlers multi-tenant
- [ ] Cleanup automatico file con Celery Beat

### Miglioramenti
- [ ] Caching risultati query (Redis)
- [ ] CDN per assets statici
- [ ] Backup automatici database
- [ ] Monitoring (Sentry, New Relic)

---

## 📞 Support

- **Docs Railway**: https://docs.railway.app
- **Telegram API**: https://core.telegram.org/bots
- **Issues**: https://github.com/Cilluzzo79/Datapdfimg/issues

---

**Versione**: 1.0.0
**Ultimo aggiornamento**: 2025-01-12
