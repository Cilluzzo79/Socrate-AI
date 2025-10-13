# 🤖 Socrate AI - Sistema Multi-tenant di Knowledge Management

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema unificato per analisi documenti e video accessibile via **Web App** e **Telegram Bot** con autenticazione automatica.

## 📋 Caratteristiche Principali

### 🔐 Autenticazione Zero-Configuration
- Login con Telegram in **1 click** (nessuna configurazione API da parte dell'utente)
- Sistema OAuth ufficiale Telegram (sicuro e verificato)
- Sessioni persistent multi-dispositivo

### 📚 Gestione Documenti Multi-tenant
- Upload documenti (PDF, DOCX, TXT, video)
- **Processing asincrono con Celery + Redis**
- **Status polling in tempo reale** con progress bar
- Storage isolato per utente con quote configurabili
- Cancellazione con liberazione automatica storage

### 🧠 AI-Powered Content Generation
- **Quiz Interattivi**: Multiple choice, vero/falso, risposte brevi
- **Riassunti**: Brevi, medi, estesi, per sezioni
- **Mappe Mentali**: Visualizzazione concetti con relazioni
- **Schemi Gerarchici**: Outline dettagliati del contenuto
- **Analisi Avanzate**: Tematica, critica, comparativa, contestuale

### 🎯 Dual Access
- **Web Dashboard**: Interfaccia moderna e responsive
- **Telegram Bot**: Accesso diretto da chat (TODO: implementare handlers multi-tenant)

### 💾 Database Multi-tenant
- Isolamento completo dati tra utenti
- Schema ottimizzato con indici per performance
- Storico completo interazioni per analytics
- Supporto PostgreSQL (produzione) e SQLite (sviluppo)

---

## 🚀 Quick Start

### 1. Installazione Locale

```bash
# Clone repository
git clone https://github.com/Cilluzzo79/Datapdfimg.git
cd memvid

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installa dipendenze
pip install -r requirements_multitenant.txt

# Configura environment
cp .env.example .env
# Modifica .env con i tuoi valori

# Inizializza database
python -c "from core.database import init_db; init_db()"

# Avvia server
python api_server.py
```

### 2. Deployment Railway

Vedi **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** per istruzioni dettagliate.

**Quick Deploy**:
1. Fai fork di questo repository
2. Crea progetto Railway e collega GitHub
3. Aggiungi PostgreSQL database
4. Configura environment variables
5. Deploy automatico! 🎉

---

## 📊 Architettura

```
┌─────────────── USER ───────────────┐
│  Web Browser  │  Telegram App      │
└───────┬───────┴──────┬─────────────┘
        │              │
        ▼              ▼
┌─────────────────────────────────────┐
│       Flask API (api_server.py)     │
│  ┌─────────────────────────────┐   │
│  │ Telegram Login Widget Auth  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Multi-tenant Document Mgmt  │   │
│  │ + Upload & Status Polling   │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ RAG Pipeline (memvidBeta)   │   │
│  └─────────────────────────────┘   │
└──────────┬──────────┬───────────────┘
           │          │
           │          └──────────────┐
           ▼                         ▼
┌──────────────────┐   ┌─────────────────────────┐
│  PostgreSQL DB   │   │   Redis Message Broker  │
│  Multi-tenant    │   │   + Result Backend      │
│                  │   └────────┬────────────────┘
│  - users         │            │
│  - documents     │            ▼
│  - chat_sessions │   ┌─────────────────────────┐
└──────────────────┘   │  Celery Worker Pool     │
                       │  (tasks.py)             │
                       │                         │
                       │  - process_document_task│
                       │  - memvid encoder       │
                       │  - progress updates     │
                       └─────────────────────────┘
```

---

## 📁 Struttura Progetto

```
memvid/
├── api_server.py                     # Main Flask application
├── celery_config.py                  # Celery configuration (Redis)
├── tasks.py                          # Async document processing tasks
├── core/
│   ├── database.py                   # SQLAlchemy models
│   ├── document_operations.py        # Multi-tenant CRUD
│   ├── rag_wrapper.py               # RAG pipeline integration
│   ├── content_generators.py        # AI prompt templates
│   └── llm_client.py                # OpenAI/Anthropic client
├── templates/
│   ├── index.html                   # Landing page
│   └── dashboard.html               # User dashboard
├── static/js/
│   └── dashboard.js                 # Frontend logic + polling
├── memvidBeta/                      # Existing codebase (integrated)
├── Procfile                         # Railway web service
├── Procfile.worker                  # Railway worker service
├── docker-compose.dev.yml           # Local development
├── railway.json                     # Railway config
├── test_async_processing.py         # Test suite
├── start_async_dev.bat              # Windows dev startup
└── requirements_multitenant.txt     # Dependencies
```

---

## 🔧 Configurazione

### Environment Variables

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token
BOT_USERNAME=your_bot_username

# Database (auto-provided by Railway)
DATABASE_URL=postgresql://...

# Redis (auto-provided by Railway)
REDIS_URL=redis://...

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# App
SECRET_KEY=your-random-secret-key
FLASK_ENV=production
PORT=5000
STORAGE_PATH=/app/storage
```

### Subscription Tiers (Configurabile)

| Tier | Storage Quota | Features |
|------|---------------|----------|
| Free | 500 MB | Base features |
| Pro | 5 GB | Advanced analytics, priority processing |
| Enterprise | Unlimited | Custom integrations, dedicated support |

---

## 🧪 Testing

### Async Processing Test
```bash
# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Start Celery worker
celery -A celery_config worker --loglevel=info

# Start Flask API
python api_server.py

# Run async test suite
python test_async_processing.py
```

### Quick Start (Windows)
```bash
# Start everything with one command
start_async_dev.bat
```

### Manual Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Upload test document (requires auth)
curl -X POST -F "file=@test.pdf" \
  -b cookies.txt \
  http://localhost:5000/api/documents/upload

# Check processing status
curl http://localhost:5000/api/documents/<doc_id>/status \
  -b cookies.txt
```

---

## 📖 API Reference

### Authentication
- `POST /auth/telegram/callback` - Telegram OAuth callback
- `GET /logout` - Logout user

### User
- `GET /api/user/profile` - Get user profile
- `GET /api/user/stats` - Get user statistics

### Documents
- `GET /api/documents` - List user documents
- `GET /api/documents/<id>` - Get document details
- `GET /api/documents/<id>/status` - Get processing status (polling)
- `POST /api/documents/upload` - Upload new document (queues async task)
- `DELETE /api/documents/<id>` - Delete document

### Content Generation
- `POST /api/query` - Query document with AI
  - Parameters: `document_id`, `query`, `command_type` (quiz|summary|mindmap|outline|analyze)

### Utility
- `GET /api/health` - Health check endpoint

Vedi `api_server.py` per dettagli completi.

---

## 🛠️ Sviluppo

### Contribuire
1. Fork il repository
2. Crea feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

### Implementato ✓
- [x] Multi-tenant database with isolation
- [x] Telegram Login Widget authentication
- [x] Document upload and management
- [x] **Async processing with Celery + Redis**
- [x] **Real-time status polling**
- [x] **memvid encoder integration**
- [x] Frontend progress tracking

### Roadmap
- [ ] RAG pipeline integration for query tools
- [ ] Telegram bot handlers multi-tenant
- [ ] S3 storage backend
- [ ] Celery Beat for scheduled cleanup
- [ ] Stripe payment integration
- [ ] Advanced analytics dashboard
- [ ] Document sharing/collaboration
- [ ] WebSocket for real-time updates

---

## 📚 Documentazione

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Guida completa deployment Railway
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Riepilogo implementazione tecnica
- **[SOCRATE_AI_PROJECT_REPORT.md](SOCRATE_AI_PROJECT_REPORT.md)** - Report dettagliato progetto

---

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/Cilluzzo79/Datapdfimg/issues)
- **Telegram**: Contatta il bot per supporto
- **Docs**: Railway, Telegram Bot API, Flask

---

## 📄 License

Questo progetto è licenziato sotto MIT License - vedi [LICENSE](LICENSE) per dettagli.

---

## 👨‍💻 Autori

- **Implementazione Multi-tenant**: Sviluppata con Claude (Anthropic)
- **Sistema Base**: Progetto Socrate AI originale
- **Integrazione**: memvidBeta RAG pipeline

---

## 🙏 Riconoscimenti

- **Telegram** per il Login Widget sicuro e semplice
- **Railway** per deployment facile e veloce
- **OpenAI/Anthropic** per modelli AI potenti
- **Flask** community per framework eccellente
- **memvid** per sistema di processing documenti

---

**Versione**: 1.0.0
**Status**: ✅ Ready for Deployment
**Ultimo aggiornamento**: Gennaio 2025

---

## 🎯 Quick Links

- [🚀 Deployment Guide](DEPLOYMENT_GUIDE.md)
- [📝 Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [📊 Project Report](SOCRATE_AI_PROJECT_REPORT.md)
- [🐛 Report Bug](https://github.com/Cilluzzo79/Datapdfimg/issues/new)
- [💡 Request Feature](https://github.com/Cilluzzo79/Datapdfimg/issues/new)

---

Made with ❤️ using Flask, PostgreSQL, and AI
