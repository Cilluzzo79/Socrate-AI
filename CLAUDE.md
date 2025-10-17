# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

- **Set up environment**
  ```bash
  python -m venv venv
  venv\Scripts\activate  # Windows
  source venv/bin/activate  # Unix
  pip install -r requirements_multitenant.txt
  cp .env.example .env  # then fill secrets
  python -c "from core.database import init_db; init_db()"
  ```
- **Run Flask API locally**
  ```bash
  python api_server.py
  ```
- **Start async stack (Redis + Celery worker + API)**
  ```bash
  docker-compose -f docker-compose.dev.yml up redis postgres -d
  celery -A celery_config worker --loglevel=info --concurrency=2
  python api_server.py
  ```
- **Smoke tests / diagnostics**
  ```bash
  python test_database_operations.py
  python test_async_processing.py
  python test_r2_connection.py
  ```
- **Railway deployment helpers**
  ```bash
  railway link
  railway logs --service web
  railway logs --service worker
  railway up
  ```

## High-Level Architecture

- **Flask web API (`api_server.py`)** handles Telegram-authenticated document management, file uploads, status polling, and AI query endpoints. It renders templates from `templates/` and serves static assets from `static/`.
- **Core domain layer (`core/`)** provides SQLAlchemy models (`database.py`), document CRUD plus storage orchestration (`document_operations.py`, `s3_storage.py`), RAG/query helpers (`query_engine.py`, `llm_client.py`, `rag_wrapper.py`), and content generators.
- **Async processing** relies on Celery configured in `celery_config.py` with Redis broker/result backend. Tasks in `tasks.py` download document blobs, run Memvid encoding, upload artifacts (video/index/embeddings) to Cloudflare R2 via `core/s3_storage.py`, and update database status.
- **Memvid encoder assets** live under `memvidBeta/encoder_app/` and legacy chat tooling under `memvid_chat/`. The worker wraps these modules to build QR-video knowledge bases.
- **Data flow**: Flask API persists metadata in PostgreSQL (or SQLite for dev), queues Celery tasks via Redis, workers process documents and push outputs to R2, then the API exposes processed metadata for querying.

## Project Structure Highlights

- `api_server.py`: Flask entrypoint (Gunicorn target in production).
- `tasks.py`: Celery tasks for async document processing.
- `celery_config.py`: Celery app configuration.
- `core/`: domain logic, database models, storage integrations, LLM wrappers.
- `templates/`, `static/`: frontend pages and assets (dashboard, login, polling JS).
- `memvidBeta/`: bundled Memvid encoder code leveraged by workers.
- `docker-compose.dev.yml`: local Redis/Postgres helpers.
- `Procfile`, `Procfile.worker`, `Procfile.railway`, `railway.json`, `nixpacks.toml`: Railway deployment configuration.

## Operational Notes

- Environment requires Telegram credentials (`TELEGRAM_BOT_TOKEN`, `BOT_USERNAME`), Cloudflare R2 access keys (`R2_*`), and LLM provider keys (`OPENAI_API_KEY` or compatible) set in `.env` or Railway variables.
- Storage path defaults to `./storage` locally; in production artifacts are persisted via R2. Ensure `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, and credentials are configured before running async tasks.
- Database URL defaults to SQLite but must be PostgreSQL in production; the code auto-normalizes `postgres://` to `postgresql://`.
- `test_async_processing.py` assumes Redis + Celery worker running; `start_async_dev.bat` bootstraps the full stack on Windows.

## Key References

- `README.md`, `README_MULTITENANT.md`, `QUICK_START_LOCAL.md`: onboarding and local setup guidance.
- `DEPLOYMENT_GUIDE.md`, `ASYNC_DEPLOYMENT_CHECKLIST.md`: Railway deployment and async troubleshooting.
- `STATO DEL PROGETTO SOCRATE/STATO_PROGETTO.md`: latest project status and roadmap.
- `IMPLEMENTATION_SUMMARY.md`, `ASYNC_IMPLEMENTATION_SUMMARY.md`: technical background and feature history.
