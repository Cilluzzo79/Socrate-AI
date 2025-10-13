# Quick Start - Testing Locale

## Stato Attuale

✅ **Database Operations**: Tutti i test passano!
- Multi-tenant isolation funziona
- CRUD operations funzionano
- Status updates funzionano
- Chat sessions funzionano
- User statistics funzionano

⏳ **Async Processing**: Richiede Redis e Celery worker

## Step per Test Completo con Async

### 1. Avvia Docker Desktop

**Windows**:
- Cerca "Docker Desktop" nel menu Start
- Avvia l'applicazione
- Attendi che Docker sia "Running" (icona verde)

### 2. Avvia Redis

```bash
# Opzione A: Con Docker Compose (consigliato)
docker-compose -f docker-compose.dev.yml up redis -d

# Opzione B: Con comando Docker diretto
docker run -d -p 6379:6379 --name redis-socrate redis:7-alpine

# Verifica che Redis sia in esecuzione
docker ps | findstr redis
```

### 3. Verifica connessione Redis

```bash
# Test connessione (richiede redis-cli installato)
# Oppure verifica che il container sia "Up"
docker ps
```

### 4. Avvia Celery Worker

Apri un nuovo terminale/prompt dei comandi:

```bash
cd D:\railway\memvid

# Attiva virtual environment se ne hai uno
# venv\Scripts\activate

# Avvia worker
celery -A celery_config worker --loglevel=info --concurrency=2
```

Dovresti vedere:
```
[INFO] celery@COMPUTERNAME ready.
[INFO] registered tasks:
  - tasks.process_document_task
  - tasks.cleanup_old_documents
```

### 5. Avvia Flask API

Apri un altro nuovo terminale:

```bash
cd D:\railway\memvid

# Attiva virtual environment
# venv\Scripts\activate

# Avvia API server
python api_server.py
```

Dovresti vedere:
```
[INFO] Starting Socrate AI API server on port 5000
[INFO] Bot Username: ...
[INFO] Storage Path: ./storage
 * Running on http://0.0.0.0:5000
```

### 6. Run Test Async Processing

In un terzo terminale:

```bash
cd D:\railway\memvid

python test_async_processing.py
```

### Alternativa: Usa lo Script Automatico (Windows)

```bash
# Questo script apre automaticamente 2 finestre
start_async_dev.bat
```

Poi in un terzo terminale:
```bash
python test_async_processing.py
```

## Test tramite Web UI

1. Apri browser: http://localhost:5000

2. Per testare senza autenticazione Telegram (modalità dev):
   - Commenta il decorator `@require_auth` in `api_server.py`
   - Oppure configura Telegram Login Widget

3. Upload un PDF di test

4. Osserva la progress bar aggiornarsi in tempo reale

## Troubleshooting

### Docker Desktop non si avvia

**Problema**: "error during connect: open //./pipe/dockerDesktopLinuxEngine"

**Soluzione**:
1. Apri Docker Desktop dal menu Start
2. Attendi che mostri "Engine running"
3. Riprova i comandi docker

### Redis non si connette

**Problema**: Connection refused su porta 6379

**Soluzione**:
```bash
# Verifica che Redis container sia in esecuzione
docker ps

# Se non c'è, avvialo:
docker run -d -p 6379:6379 redis:7-alpine

# Test connessione
docker exec -it <container-id> redis-cli ping
# Dovrebbe rispondere: PONG
```

### Celery worker non si avvia

**Problema**: "celery_config" module not found

**Soluzione**:
```bash
# Assicurati di essere nella directory corretta
cd D:\railway\memvid

# Verifica che il file esista
dir celery_config.py

# Riprova
celery -A celery_config worker --loglevel=info
```

### API server non si avvia

**Problema**: Port 5000 già in uso

**Soluzione**:
```bash
# Cambia porta nel .env
PORT=5001

# Oppure trova e termina il processo che usa porta 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Test fallisce: memvidBeta not found

**Problema**: Import error per memvid_sections

**Soluzione**:
```bash
# Verifica che la cartella esista
dir memvidBeta\encoder_app\memvid_sections.py

# Se manca, il task salterà la codifica e restituirà errore
# Questo è normale per test puri del sistema async
```

## Test Rapidi senza Full Integration

Se vuoi solo verificare il sistema async senza memvid encoder:

### Test 1: Database Operations (già fatto ✅)
```bash
python test_database_operations.py
```

### Test 2: Celery Connection
```python
# test_celery_simple.py
from celery_config import celery_app

result = celery_app.control.inspect().active()
print(f"Workers: {result}")
```

### Test 3: Task Queue
```python
# test_task_queue.py
from tasks import process_document_task

# Queue a test task
task = process_document_task.delay('test-doc-id', 'test-user-id')
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")
```

## Status Checklist

**Completati** ✅:
- [x] Database schema e models
- [x] Multi-tenant operations
- [x] Document CRUD
- [x] User statistics
- [x] Celery configuration
- [x] Async task implementation
- [x] API endpoints (upload, status polling)
- [x] Frontend polling integration
- [x] Test suite database operations

**Da Testare** ⏳:
- [ ] Redis connection
- [ ] Celery worker execution
- [ ] Document processing task
- [ ] memvid encoder integration
- [ ] Frontend real-time progress
- [ ] End-to-end upload flow

**Ready for Railway** 🚀:
- Una volta testato localmente
- Deploy con 4 servizi: Web, Worker, Redis, PostgreSQL
- Seguire DEPLOYMENT_GUIDE.md

## Prossimi Step

1. **Avvia Docker Desktop**
2. **Avvia Redis** con docker-compose
3. **Avvia Celery Worker** in terminal separato
4. **Avvia Flask API** in terminal separato
5. **Run test** `python test_async_processing.py`
6. **Test Web UI** http://localhost:5000

oppure

1. **Avvia Docker Desktop**
2. **Run** `start_async_dev.bat` (avvia tutto automaticamente)
3. **Run test** `python test_async_processing.py`

---

**Domande? Issues?**
- Vedi DEPLOYMENT_GUIDE.md
- Vedi ASYNC_IMPLEMENTATION_SUMMARY.md
- Controlla i logs di Celery worker e Flask API
