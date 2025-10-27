# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

**Setup**
```bash
python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements_multitenant.txt
cp .env.example .env  # Configure: TELEGRAM_BOT_TOKEN, BOT_USERNAME, R2_*, OPENAI_API_KEY
python -c "from core.database import init_db; init_db()"
```

**Local Development - Simple (API only)**
```bash
python api_server.py  # Flask dev server on port 5000
```

**Local Development - Full Stack (with async processing)**
```bash
# Windows: Automated startup
start_async_dev.bat  # Starts Redis check, Celery worker, and Flask API in separate windows

# Manual startup (all platforms)
docker-compose -f docker-compose.dev.yml up redis -d  # Start Redis
celery -A celery_config worker --loglevel=info --concurrency=2  # Terminal 1
python api_server.py  # Terminal 2
```

**Testing**
```bash
python test_database_operations.py    # Database CRUD and multi-tenant isolation
python test_async_processing.py       # Async document processing (requires Redis + Celery worker)
python test_r2_connection.py          # Cloudflare R2 storage connectivity
```

**Railway Deployment**
```bash
railway link                    # Link to Railway project
railway up                      # Deploy current directory
railway logs --service web      # View web service logs
railway logs --service worker   # View Celery worker logs
```

## Architecture

**3-Tier Multi-Tenant System**

1. **Web Layer** (`api_server.py`)
   - Flask REST API with Telegram Login Widget authentication
   - Endpoints: document upload, status polling, AI queries, chat sessions
   - Multi-tenant: all operations scoped by `user_id` (Telegram ID)
   - Renders templates from `templates/`, serves static assets from `static/`

2. **Domain Layer** (`core/`)
   - `database.py`: SQLAlchemy models (User, Document, ChatSession, Message)
   - `document_operations.py`: Multi-tenant CRUD operations with user isolation
   - `s3_storage.py`: Cloudflare R2 integration for document/video/index storage
   - `query_engine.py`: RAG retrieval using sentence-transformers + metadata JSON
   - `llm_client.py`: OpenAI/Anthropic LLM wrapper for chat responses
   - `rag_wrapper.py`: RAG orchestration (query → retrieve → rerank → generate)
   - `content_generators.py`: Specialized prompts (quiz, outline, mindmap, summary)

3. **Async Processing Layer**
   - `celery_config.py`: Celery app with Redis broker/backend
   - `tasks.py`: `process_document_task` downloads PDF from R2, runs Memvid encoding, uploads video/index/embeddings to R2
   - `memvidBeta/encoder_app/`: Memvid QR-video encoder (converts documents → MP4 + JSON metadata)

**Data Flow**
```
User uploads PDF → Flask API → Save to R2 + DB (status: pending)
                                     ↓
                              Queue Celery task
                                     ↓
Worker: Download PDF → Memvid encode → Upload video/index to R2 → Update DB (status: completed)
                                     ↓
User queries document → RAG retrieval from R2 index → LLM generates answer
```

**Multi-Tenant Isolation**
- All database queries filtered by `user_id` in `document_operations.py`
- R2 keys namespaced: `documents/{user_id}/{doc_id}/{filename}`
- Session management via Flask sessions with Telegram auth

**Storage Strategy**
- **Local Dev**: SQLite + `./storage` directory
- **Production**: PostgreSQL + Cloudflare R2 (100MB max upload, 10 docs/user limit)

## Railway Deployment Architecture

**4 Services** (defined in `railway.json` + Procfiles):
1. **web**: `Procfile` → Gunicorn serving `api_server.py` (2 workers, 300s timeout)
2. **worker**: `Procfile.worker` → Celery worker via `start_worker_wrapper.py` (includes healthcheck)
3. **redis**: Railway template for Redis 7
4. **postgres**: Railway template for PostgreSQL

**Critical Environment Variables** (set in Railway):
- `DATABASE_URL`: Auto-provided by Railway Postgres (code normalizes `postgres://` → `postgresql://`)
- `REDIS_URL`: Auto-provided by Railway Redis
- `TELEGRAM_BOT_TOKEN`, `BOT_USERNAME`: Telegram Bot credentials
- `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`: Cloudflare R2
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM provider
- `SECRET_KEY`: Flask session secret (must be strong in production)

## Key Files

**Core Application**
- `api_server.py`: Flask app entry point (Gunicorn target)
- `tasks.py`: Celery async tasks for document processing
- `celery_config.py`: Celery + Redis configuration

**Domain Logic**
- `core/database.py`: SQLAlchemy models and session management
- `core/document_operations.py`: Multi-tenant CRUD with user isolation
- `core/query_engine.py`: RAG retrieval engine
- `core/rag_wrapper.py`: Full RAG pipeline orchestration

**Deployment**
- `Procfile`: Gunicorn web service command
- `Procfile.worker`: Celery worker with healthcheck wrapper
- `railway.json`: Railway build/deploy configuration
- `docker-compose.dev.yml`: Local Redis/Postgres for development

**Testing & Utilities**
- `test_database_operations.py`: Verifies multi-tenant isolation
- `test_async_processing.py`: End-to-end async document processing test
- `start_async_dev.bat`: Windows script to start full dev stack

## Common Workflows

**Adding a new API endpoint**
1. Add route in `api_server.py` with `@require_auth` decorator
2. Use `get_user_id_from_session()` to get authenticated user
3. Call functions from `core/document_operations.py` (always pass `user_id`)
4. Return JSON response with proper error handling

**Modifying RAG behavior**
1. Edit retrieval logic in `core/query_engine.py` (chunk selection, embeddings)
2. Edit reranking in `core/reranker.py` (semantic/keyword scoring)
3. Edit prompt construction in `core/rag_wrapper.py` (context formatting)
4. Edit LLM call in `core/llm_client.py` (model selection, parameters)

**Adding new async task**
1. Define task in `tasks.py` with `@celery_app.task` decorator
2. Update task state with `self.update_state()` for progress tracking
3. Call task with `.delay()` or `.apply_async()` from API
4. Poll task status via `AsyncResult(task_id).state`

## Troubleshooting

**Redis connection issues**
```bash
docker ps | findstr redis  # Check if Redis container is running
docker run -d -p 6379:6379 redis:7-alpine  # Start Redis if missing
```

**Celery worker not picking up tasks**
```bash
celery -A celery_config inspect active  # Check worker status
# Restart worker and verify Redis URL in .env matches running Redis
```

**R2 upload failures**
```bash
python test_r2_connection.py  # Verify R2 credentials
# Check R2_BUCKET_NAME, R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
```

**Database migrations (if schema changes)**
```bash
# Currently using direct SQLAlchemy, no Alembic migrations
# To reset: delete app.db (local) or use Railway DB console (prod)
python -c "from core.database import init_db; init_db()"
```

## Documentation References

- `QUICK_START_LOCAL.md`: Detailed local setup with troubleshooting
- `DEPLOYMENT_GUIDE.md`: Railway deployment step-by-step
- `ASYNC_DEPLOYMENT_CHECKLIST.md`: Async processing verification checklist
- `STATO DEL PROGETTO SOCRATE/`: Project status, RAG diagnostics, design system docs
