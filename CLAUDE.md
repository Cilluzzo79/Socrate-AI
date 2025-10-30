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

**Modal GPU Deployment** (Reranking Service)
```bash
modal deploy modal_reranker.py  # Deploy GPU reranking service to Modal
# Health check: curl https://cilluzzo79--socrate-reranker-health.modal.run
# Note: Requires Modal account (30 GPU-hours/month free tier)
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
- `MODAL_RERANK_URL`: Modal GPU reranking endpoint (optional, falls back to local reranker)

## Key Files

**Core Application**
- `api_server.py`: Flask app entry point (Gunicorn target)
- `tasks.py`: Celery async tasks for document processing
- `celery_config.py`: Celery + Redis configuration

**Domain Logic**
- `core/database.py`: SQLAlchemy models and session management
- `core/document_operations.py`: Multi-tenant CRUD with user isolation
- `core/query_engine.py`: RAG retrieval engine with adaptive term specificity weighting (ATSW)
- `core/rag_wrapper.py`: Full RAG pipeline orchestration
- `core/modal_rerank_client.py`: HTTP client for Modal GPU reranking (cross-encoder)
- `core/reranker.py`: Local fallback reranker (diversity-based)

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
1. Edit retrieval logic in `core/query_engine.py` (chunk selection, embeddings, ATSW weighting)
2. Edit reranking in `core/reranker.py` (local fallback) or `core/modal_rerank_client.py` (GPU reranking)
3. Edit prompt construction in `core/rag_wrapper.py` (context formatting)
4. Edit LLM call in `core/llm_client.py` (model selection, parameters)

**Understanding RAG system architecture**
The RAG system uses a two-stage approach with adaptive term specificity weighting (ATSW):
- **Stage 1: Hybrid Retrieval** - Combines semantic (70%) + keyword (30%) search with proper noun boosting
- **Stage 2: Reranking** - Uses Modal GPU cross-encoder (SOTA) with fallback to local diversity reranker
- **Stage 3: Generation** - LLM generates answer using top-k reranked chunks
- **ATSW Algorithm** - Automatically detects and downweights generic terms (e.g., "ricetta", "documento") while boosting specific terms (e.g., "ossobuco", "lombardia")

Key files for RAG system understanding:
- `core/query_engine.py`: Main retrieval logic with ATSW
- `modal_reranker.py`: GPU reranking service (deployed on Modal)
- `core/modal_rerank_client.py`: Client for Modal GPU service
- `UNIVERSAL_RAG_IMPLEMENTATION.py`: Standalone ATSW implementation for testing
- `STATO DEL PROGETTO SOCRATE/`: Extensive RAG analysis, diagnosis, and evaluation reports

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

**Modal GPU reranking issues**
```bash
# Check Modal service health
curl https://cilluzzo79--socrate-reranker-health.modal.run

# View logs for Modal reranking
railway logs --service web | grep MODAL

# Expected patterns:
# - Success: "[MODAL SUCCESS] GPU reranked to X chunks"
# - Fallback: "[LOCAL-RERANKING] Using diversity reranker"
# - Cold start: 15-25 seconds is normal for GPU model loading
# - Warm requests: Should be <1 second

# If Modal always times out, check:
# 1. MODAL_RERANK_URL is set correctly
# 2. Modal service is deployed: modal deploy modal_reranker.py
# 3. Network connectivity from Railway to Modal
```

**RAG retrieval quality issues**
```bash
# Diagnose retrieval issues for specific documents
python diagnose_recipe_retrieval.py  # Test recipe retrieval
python test_ossobuco_diagnosis.py   # Specific ossobuco query test

# Run RAG evaluation framework
python run_baseline_eval.py          # Baseline (no reranking)
python run_crossencoder_eval.py      # With cross-encoder reranking

# Test universal RAG solution (ATSW)
python integrate_universal_rag.py --test

# Common issues:
# - Embedding dimension mismatch (384 vs 768): Re-encode documents
# - Generic terms drowning specific terms: ATSW should handle this
# - Query too vague: Add regional/domain qualifiers (e.g., "ossobuco milanese" vs "ossobuco")
```

**Database migrations (if schema changes)**
```bash
# Currently using direct SQLAlchemy, no Alembic migrations
# To reset: delete app.db (local) or use Railway DB console (prod)
python -c "from core.database import init_db; init_db()"
```

## Agent Collaboration Policy

**When to Use Specialized Agents**

Claude Code has access to specialized agents for complex, multi-step tasks. **ALWAYS** use the appropriate agent when the task matches their expertise domain.

### Available Agents

1. **backend-master-analyst**
   - **Use for**: Code review, debugging, security analysis of backend code
   - **Triggers**: API endpoints, database operations, authentication logic, async tasks
   - **When**: After implementing/modifying backend features, proactively for quality assurance

2. **rag-pipeline-architect**
   - **Use for**: RAG system diagnosis, optimization, evaluation
   - **Triggers**: Retrieval quality issues, embedding problems, reranking performance
   - **When**: RAG performance degradation, new RAG features, domain-specific retrieval

3. **frontend-architect-prime**
   - **Use for**: React/Next.js components, UI code review, frontend architecture
   - **Triggers**: Component implementation, state management, performance optimization
   - **When**: Building/reviewing frontend features, accessibility issues, performance bottlenecks

4. **ui-design-master**
   - **Use for**: UI/UX design analysis, interface critique, design system consultation
   - **Triggers**: User complaints about UI, design inconsistencies, new features needing design
   - **When**: Visual design issues, accessibility audits, brand consistency problems

5. **cognitive-load-ux-auditor**
   - **Use for**: Cognitive load analysis, usability evaluation, service comparison
   - **Triggers**: User confusion, complex workflows, educational interfaces
   - **When**: UX audits, learning curve issues, competitive analysis needed
   - **Expertise**: Reduces cognitive friction, evaluates information architecture, compares against competitors

### Agent Collaboration Protocol

**CRITICAL**: When multiple agents are needed, run them **IN PARALLEL** using a single message with multiple Task tool calls.

**Information Sharing**: Agents MUST exchange ALL detailed information necessary to achieve the final planned goal. Each agent should:
1. Share complete context and findings with other agents
2. Reference work done by other agents in their analysis
3. Build upon insights from parallel agent work
4. Provide actionable, implementable recommendations

**Example Parallel Execution**:
```
User: "The quiz interface has UX issues and the backend code needs review"
→ Launch ui-design-master + backend-master-analyst + cognitive-load-ux-auditor in parallel
→ Each agent analyzes their domain
→ Synthesize recommendations from all agents
→ Implement unified solution
```

## Documentation References

**Setup & Deployment**
- `QUICK_START_LOCAL.md`: Detailed local setup with troubleshooting
- `DEPLOYMENT_GUIDE.md`: Railway deployment step-by-step
- `ASYNC_DEPLOYMENT_CHECKLIST.md`: Async processing verification checklist
- `MODAL_SETUP_GUIDE.md`: Modal GPU service setup

**RAG System** (extensive documentation in `STATO DEL PROGETTO SOCRATE/`)
- `RAG_SYSTEM_ANALYSIS_REPORT.md`: Comprehensive RAG architecture analysis and optimization guide
- `UNIVERSAL_RAG_EXECUTIVE_SUMMARY.md`: Universal term specificity solution (ATSW)
- `UNIVERSAL_RAG_SOLUTION.md`: Detailed ATSW implementation guide
- `MODAL_GPU_DEPLOYMENT_SUCCESS_29_OCT.md`: Modal GPU reranking deployment report
- `RAG_EVALUATION_REPORT_28_OCT.md`: Evaluation framework and metrics
- `RECIPE_RETRIEVAL_DIAGNOSIS_COMPLETE.md`: Recipe domain retrieval analysis
- `RAG_BEST_PRACTICES_2025.md`: State-of-the-art RAG techniques

**Design System**
- `DESIGN_SYSTEM.md`: Frontend design system
- `UNIFIED_DESIGN_SYSTEM.md`: Comprehensive UI/UX guidelines
- `CHAT_REDESIGN_IMPLEMENTATION_GUIDE.md`: Chat interface redesign

**Project Status**
- `SESSION_REPORT_27_OCT_2025.md`: Recent development session summaries
- `DEPLOYMENT_SUCCESS.md`: Production deployment reports
