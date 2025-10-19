# Guida Completa Sistema Socrate AI
## Architettura, Funzionamento e Roadmap Implementazione

**Data**: 14 Ottobre 2025
**Versione**: 1.0

---

## Indice

1. [Architettura Generale](#1-architettura-generale)
2. [Flusso Upload e Elaborazione](#2-flusso-upload-e-elaborazione)
3. [Sistema Asincrono Celery](#3-sistema-asincrono-celery)
4. [Storage Cloudflare R2](#4-storage-cloudflare-r2)
5. [Database PostgreSQL](#5-database-postgresql)
6. [Autenticazione Telegram](#6-autenticazione-telegram)
7. [Sistema Query AI](#7-sistema-query-ai)
8. [Monitoraggio e Debug](#8-monitoraggio-e-debug)
9. [Roadmap Implementazione](#9-roadmap-implementazione)
10. [Checklist Pre-Lancio](#10-checklist-pre-lancio)

---

## 1. Architettura Generale

### 1.1 Componenti del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     CLOUDFLARE                               │
│  ┌─────────────┐                    ┌──────────────┐        │
│  │     R2      │◄───────────────────┤  CDN (futuro)│        │
│  │ File Storage│                    └──────────────┘        │
│  └─────────────┘                                             │
└────────────▲────────────────────────────────────────────────┘
             │
             │ S3 API (upload/download)
             │
┌────────────┴─────────────────────────────────────────────────┐
│                        RAILWAY                                │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │   Web Service    │          │  Worker Service  │         │
│  │   (Flask API)    │          │  (Celery Worker) │         │
│  │                  │          │                  │         │
│  │ • REST API       │◄────────►│ • Processa docs  │         │
│  │ • Auth Telegram  │  Redis   │ • Memvid encoder │         │
│  │ • Upload R2      │  Queue   │ • Download R2    │         │
│  │ • Dashboard      │          │ • Cleanup        │         │
│  └────────┬─────────┘          └────────┬─────────┘         │
│           │                              │                   │
│           │         ┌──────────┐        │                   │
│           └────────►│PostgreSQL│◄───────┘                   │
│                     │ Database │                             │
│                     └──────────┘                             │
│                                                               │
│           ┌──────────┐                                       │
│           │  Redis   │                                       │
│           │Task Queue│                                       │
│           └──────────┘                                       │
└───────────────────────────────────────────────────────────────┘
             │
             │ API Calls
             │
┌────────────┴─────────────────────────────────────────────────┐
│                    SERVIZI ESTERNI                            │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  OpenRouter  │         │   Telegram   │                  │
│  │  (AI APIs)   │         │   (OAuth)    │                  │
│  └──────────────┘         └──────────────┘                  │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Tecnologie Utilizzate

| Componente | Tecnologia | Versione | Scopo |
|------------|------------|----------|-------|
| **Backend** | Flask | 3.0.0 | REST API server |
| **Database** | PostgreSQL | 15+ | Dati utenti, documenti, sessioni |
| **Queue** | Redis | 7+ | Task queue per Celery |
| **Worker** | Celery | 5.3+ | Elaborazione asincrona |
| **Storage** | Cloudflare R2 | - | File storage (S3-compatible) |
| **AI** | OpenRouter | - | LLM APIs (GPT-4, Claude, etc.) |
| **Auth** | Telegram Login Widget | - | OAuth senza password |
| **Encoder** | memvid | Custom | Chunking documenti/video |
| **Deploy** | Railway | - | PaaS hosting |

---

## 2. Flusso Upload e Elaborazione

### 2.1 Diagramma Flusso Completo

```
┌──────────┐
│  Utente  │
│ (Browser)│
└────┬─────┘
     │
     │ 1. Upload file via /api/documents/upload
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    WEB SERVICE                          │
│                                                         │
│  Step 1: Ricevi file                                   │
│  ├─ Leggi file.read() → bytes                         │
│  ├─ Genera UUID documento                              │
│  └─ Valida tipo/dimensione                             │
│                                                         │
│  Step 2: Upload su R2                                  │
│  ├─ Genera key: users/{user_id}/docs/{doc_id}/file.pdf│
│  ├─ Upload file_content → R2 (boto3)                  │
│  └─ Ricevi conferma upload                             │
│                                                         │
│  Step 3: Crea record database                          │
│  ├─ INSERT INTO documents (id, user_id, filename,     │
│  │   file_path=R2_key, status='processing')           │
│  └─ COMMIT                                              │
│                                                         │
│  Step 4: Accoda task Celery                            │
│  ├─ task = process_document_task.delay(doc_id, user_id)│
│  ├─ Salva task_id in documents.metadata                │
│  └─ Ritorna 201 Created al browser                     │
└────────────┬────────────────────────────────────────────┘
             │
             │ Task inviato a Redis queue
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                   REDIS QUEUE                           │
│                                                         │
│  Queue: documents                                       │
│  ├─ Task: process_document_task                        │
│  ├─ Args: (doc_id, user_id)                           │
│  └─ State: PENDING                                      │
└────────────┬────────────────────────────────────────────┘
             │
             │ Worker preleva task
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                  WORKER SERVICE                         │
│                                                         │
│  Step 1: Download da R2                                │
│  ├─ Recupera doc.file_path da database                 │
│  ├─ Download file_data = s3.get_object(R2_key)        │
│  ├─ Salva in temp: /tmp/xyz/file.pdf                  │
│  └─ Update state: PROCESSING (progress: 20%)          │
│                                                         │
│  Step 2: Elabora con memvid                            │
│  ├─ process_file_in_sections(temp_file)               │
│  ├─ Genera: file_sections_metadata.json                │
│  ├─ Genera: file_sections_index.json                   │
│  └─ Update state: PROCESSING (progress: 80%)          │
│                                                         │
│  Step 3: Salva metadati                                │
│  ├─ Carica metadata.json → R2                          │
│  ├─ UPDATE documents SET                                │
│  │   status='ready',                                    │
│  │   total_chunks=N,                                    │
│  │   metadata={...}                                     │
│  └─ Update state: SUCCESS (progress: 100%)            │
│                                                         │
│  Step 4: Cleanup                                        │
│  ├─ shutil.rmtree(temp_dir)                            │
│  └─ Task completato                                     │
└────────────┬────────────────────────────────────────────┘
             │
             │ Notifica completamento
             │
             ▼
┌──────────┐
│  Utente  │ Polling /api/documents/{id}/status ogni 2 sec
│(Dashboard)│ Vede progress bar 0% → 20% → 80% → 100%
└──────────┘
```

### 2.2 File Coinvolti

| File | Funzione | Riga Chiave |
|------|----------|-------------|
| `api_server.py` | Endpoint upload | 338-418 |
| `core/s3_storage.py` | Upload/download R2 | 46-110 |
| `core/document_operations.py` | CRUD documenti | - |
| `tasks.py` | Task elaborazione | 22-278 |
| `celery_config.py` | Config Celery | - |

### 2.3 Tempistiche Tipiche

| Fase | Durata | Bottleneck |
|------|--------|------------|
| Upload R2 | 1-3 sec | Dimensione file |
| Queue delay | <1 sec | Worker disponibili |
| Download R2 | 1-2 sec | Dimensione file |
| Memvid encoding | 10-60 sec | Numero pagine/chunk |
| Upload metadata | <1 sec | - |
| Cleanup | <1 sec | - |
| **TOTALE** | **15-70 sec** | **Encoding** |

---

## 3. Sistema Asincrono Celery

### 3.1 Perché Celery?

**Problema senza Celery:**
```python
# Richiesta HTTP
file = request.files['file']
# ❌ Elaborazione SINCRONA (blocca il server)
result = process_file(file)  # 60 secondi!!!
# Browser in attesa... timeout dopo 30 sec
return jsonify(result)
```

**Soluzione con Celery:**
```python
# Richiesta HTTP
file = request.files['file']
# ✅ Accoda task ASINCRONO (ritorno immediato)
task = process_file_task.delay(file_id)  # <1 secondo
# Browser riceve subito risposta
return jsonify({'task_id': task.id, 'status': 'processing'})
```

### 3.2 Componenti Celery

**1. Broker (Redis)**
- Memorizza la coda dei task
- Gestisce priorità e routing
- Garantisce delivery dei task

**2. Worker (Celery Worker)**
- Processi separati dal web server
- Eseguono i task in background
- Scalabili orizzontalmente (più worker = più capacità)

**3. Backend (Redis)**
- Memorizza i risultati dei task
- Consente tracking stato (PENDING, PROCESSING, SUCCESS, FAILURE)

### 3.3 Configurazione Attuale

**File: `celery_config.py`**
```python
celery_app = Celery(
    'socrate_ai',
    broker='redis://...',     # Dove sono le code
    backend='redis://...',    # Dove sono i risultati
    include=['tasks']         # Quali moduli hanno task
)

# Routing: quale task va in quale coda
celery_app.conf.task_routes = {
    'tasks.process_document_task': {'queue': 'documents'},  # Alta priorità
    'tasks.cleanup_old_documents': {'queue': 'maintenance'} # Bassa priorità
}
```

**File: `tasks.py`**
```python
@celery_app.task(bind=True, name='tasks.process_document_task')
def process_document_task(self, document_id: str, user_id: str):
    # bind=True: accesso a self per update_state()
    # name: nome esplicito del task

    # Aggiorna stato
    self.update_state(
        state='PROCESSING',
        meta={'status': 'Downloading...', 'progress': 20}
    )

    # ... elaborazione ...

    return {'success': True, 'document_id': document_id}
```

### 3.4 Come Monitorare i Task

**1. Dalla Dashboard (frontend):**
```javascript
// Polling ogni 2 secondi
setInterval(async () => {
    const status = await fetch(`/api/documents/${doc_id}/status`);
    const data = await status.json();

    progressBar.value = data.progress;
    statusText.innerText = data.message;

    if (data.ready) {
        clearInterval(this);
        showSuccessMessage();
    }
}, 2000);
```

**2. Dai Log Railway:**
```bash
# Worker Service logs
[INFO] Task tasks.process_document_task[abc-123] received
[INFO] Starting document processing: doc-id for user user-id
[INFO] Downloading file from R2: users/user-id/docs/doc-id/file.pdf
[INFO] Starting memvid encoder...
[INFO] Document processing completed: doc-id
[INFO] Task tasks.process_document_task[abc-123] succeeded
```

**3. Da Python (programmaticamente):**
```python
from celery.result import AsyncResult

task = AsyncResult(task_id)

print(f"State: {task.state}")  # PENDING, PROCESSING, SUCCESS, FAILURE
print(f"Info: {task.info}")    # Meta data (progress, status message)
print(f"Result: {task.result}") # Return value del task (se SUCCESS)
```

### 3.5 Gestione Errori

**Cosa succede se un task fallisce?**

```python
# In tasks.py
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: str, user_id: str):
    try:
        # ... elaborazione ...
    except TemporaryError as e:
        # Errore temporaneo (R2 down) → Retry
        raise self.retry(exc=e, countdown=60)
    except PermanentError as e:
        # Errore permanente (file corrotto) → Fail
        update_document_status(document_id, user_id, status='failed',
                               error_message=str(e))
        return {'success': False, 'error': str(e)}
```

**Log degli errori:**
```
[ERROR] Task tasks.process_document_task[abc-123] raised unexpected: ValueError('File corrupted')
Traceback (most recent call last):
  File "tasks.py", line 120, in process_document_task
    result = process_file(file_path)
ValueError: File corrupted
```

### 3.6 Scaling dei Worker

**Su Railway:**

1. **Verticale** (più potenza):
   - Settings → Resources → Increase memory/CPU

2. **Orizzontale** (più worker):
   - Duplicate Worker Service
   - Entrambi leggono dalla stessa Redis queue
   - Carico distribuito automaticamente

**Esempio con 2 worker:**
```
User A upload doc → Queue → Worker 1 (busy)
User B upload doc → Queue → Worker 2 (free) ← prende questo task
User C upload doc → Queue → Attende Worker 1 o 2
```

---

## 4. Storage Cloudflare R2

### 4.1 Perché R2 invece di Filesystem Locale?

**Problema Filesystem Locale:**
```
Web Service Container       Worker Service Container
├─ /app/uploads/           ├─ /app/uploads/
│  └─ file1.pdf  ❌        │  └─ (vuoto)  ❌

File caricato su Web → Non visibile su Worker!
Container effimeri → Riavvio = perdita dati
```

**Soluzione R2:**
```
Web Service              Cloudflare R2              Worker Service
   │                          │                          │
   │ 1. Upload file          │                          │
   ├────────────────────────►│                          │
   │                          │ File salvato             │
   │                          │                          │
   │                          │  2. Download file        │
   │                          │◄─────────────────────────┤
   │                          │                          │
   Entrambi accedono allo stesso storage!
```

### 4.2 Struttura Bucket

```
socrate-ai-storage (bucket R2)
│
├── users/
│   ├── user-uuid-1/
│   │   └── docs/
│   │       ├── doc-uuid-a/
│   │       │   ├── documento.pdf
│   │       │   ├── documento_sections_metadata.json
│   │       │   └── documento_sections_index.json
│   │       │
│   │       └── doc-uuid-b/
│   │           └── video.mp4
│   │
│   └── user-uuid-2/
│       └── docs/
│           └── doc-uuid-c/
│               └── slides.pptx
│
└── test/  (per script di test)
```

**Vantaggi struttura:**
- Isolamento GDPR per utente
- Facile calcolo storage per utente
- Eliminazione utente = delete folder
- Backup selettivo per tier

### 4.3 Operazioni R2 nel Codice

**Upload (api_server.py:359-369):**
```python
from core.s3_storage import upload_file, generate_file_key

# Genera chiave univoca
file_key = generate_file_key(user_id, doc_id, filename)
# → "users/abc-123/docs/xyz-789/documento.pdf"

# Upload
upload_success = upload_file(file_content, file_key, mime_type)

# Salva chiave nel database
doc.file_path = file_key  # NON path locale!
```

**Download (tasks.py:69-95):**
```python
from core.s3_storage import download_file

# Recupera chiave dal database
doc = get_document_by_id(document_id, user_id)
file_key = doc.file_path  # "users/abc-123/docs/xyz-789/documento.pdf"

# Download
file_data = download_file(file_key)  # → bytes

# Salva temporaneamente
with open(temp_file_path, 'wb') as f:
    f.write(file_data)
```

**Delete (da implementare):**
```python
from core.s3_storage import delete_file

# Elimina file R2
delete_file(doc.file_path)

# Elimina record database
delete_document(document_id, user_id)
```

### 4.4 Costi R2 Reali

**Free Tier**: 10GB storage + operazioni illimitate lettura

**Scenario 100 utenti** (media 50MB/utente):
- Storage: 5GB
- Operazioni: ~10,000 upload + ~100,000 download
- **Costo**: €0 (dentro free tier)

**Scenario 1000 utenti** (media 50MB/utente):
- Storage: 50GB
- Eccedenza: 40GB × €0.014/GB = €0.56/mese
- Operazioni: Ancora dentro free tier
- **Costo**: €0.56/mese

**Confronto AWS S3:**
- Storage: 50GB × $0.023 = $1.15
- Egress: 50GB × $0.09 = $4.50 (assumendo 1 download per file)
- **Costo**: $5.65/mese (10× più costoso!)

### 4.5 Debugging R2

**Test connessione:**
```bash
python test_r2_connection.py
```

Output atteso:
```
R2 CONFIGURATION TEST
====================================
1. Checking Environment Variables:
R2_ACCESS_KEY_ID: ✅ SET
R2_SECRET_ACCESS_KEY: ✅ SET
R2_ENDPOINT_URL: ✅ SET
  Value: https://abc123.r2.cloudflarestorage.com
R2_BUCKET_NAME: socrate-ai-storage

2. Checking boto3 installation:
✅ boto3 installed successfully

3. Creating S3 client:
✅ S3 client created successfully

4. Testing bucket access:
✅ Successfully connected to bucket: socrate-ai-storage
   Bucket is empty (no objects found)

5. Testing file upload:
✅ Successfully uploaded test file: test/connection_test.txt

6. Testing file download:
✅ Successfully downloaded test file
✅ Downloaded data matches uploaded data

7. Cleaning up test file:
✅ Successfully deleted test file

8. Testing core.s3_storage module:
✅ Module imported successfully
✅ Module upload successful
✅ Module download successful
✅ Module cleanup successful

====================================
✅ ALL TESTS PASSED!
====================================
```

---

## 5. Database PostgreSQL

### 5.1 Schema Completo

```sql
-- Utenti
CREATE TABLE users (
    id UUID PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    photo_url TEXT,
    email VARCHAR(255),

    -- Subscription
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free, pro, enterprise
    storage_quota_mb INTEGER DEFAULT 500,
    storage_used_mb INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,

    -- Settings JSON
    settings JSONB DEFAULT '{}'
);

-- Documenti
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- File info
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(50),
    file_size BIGINT,  -- bytes
    file_path TEXT,    -- Chiave R2: users/{user_id}/docs/{doc_id}/file.pdf

    -- Processing
    status VARCHAR(20) DEFAULT 'processing',  -- uploading, processing, ready, failed
    processing_progress INTEGER DEFAULT 0,     -- 0-100%
    error_message TEXT,

    -- Content metadata
    language VARCHAR(10),    -- it, en, es
    total_chunks INTEGER,
    total_tokens INTEGER,
    duration_seconds INTEGER,  -- per video
    page_count INTEGER,        -- per PDF

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,

    -- Metadata JSON
    doc_metadata JSONB DEFAULT '{}'  -- task_id, metadata_file, index_file, etc.
);

-- Sessioni chat (query AI)
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Request
    command_type VARCHAR(20) NOT NULL,  -- quiz, summary, analyze, outline
    request_data JSONB NOT NULL,        -- {query: "...", options: {...}}

    -- Response
    response_data JSONB,                -- {answer: "...", sources: [...]}
    response_format VARCHAR(10),        -- markdown, html, json

    -- Metadata
    channel VARCHAR(20) NOT NULL,       -- telegram, web_app, api
    llm_model VARCHAR(50),              -- gpt-4o, claude-3.5-sonnet
    tokens_used INTEGER,                -- FUTURO: per tracking costi
    generation_time_ms INTEGER,

    -- Success tracking
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indici per performance
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_document_id ON chat_sessions(document_id);
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
```

### 5.2 Relazioni

```
users (1) ──────< (N) documents
  │                      │
  │                      │
  │                      │
  └────────< (N) chat_sessions >────┘
             (può riferirsi a un documento)
```

### 5.3 Operazioni CRUD

**File: `core/database.py` e `core/document_operations.py`**

```python
# CREATE utente (da Telegram OAuth)
user = get_or_create_user(
    telegram_id=12345678,
    first_name="Mario",
    username="mariorossi"
)

# CREATE documento
doc = create_document(
    user_id=user_id,
    filename="documento.pdf",
    file_path="users/abc/docs/xyz/documento.pdf",
    file_size=1024000,
    mime_type="application/pdf"
)
# → Status iniziale: 'processing'

# READ documenti utente
documents = get_user_documents(user_id, status='ready')

# UPDATE status documento
update_document_status(
    document_id,
    user_id,
    status='ready',
    processing_progress=100,
    total_chunks=50,
    total_tokens=12000
)

# DELETE documento
delete_document(document_id, user_id)
# → Elimina record (TODO: anche file R2)

# CREATE sessione chat
session = create_chat_session(
    user_id=user_id,
    document_id=document_id,
    command_type='summary',
    request_data={'query': 'Riassumi il documento'},
    channel='web_app'
)

# UPDATE sessione con risposta
update_chat_session(
    session_id=session.id,
    response_data={'answer': 'Il documento parla di...', 'sources': [...]},
    success=True
)

# READ statistiche utente
stats = get_user_stats(user_id)
# → {total_documents: 5, ready_documents: 3, total_sessions: 20, ...}
```

### 5.4 UUID Cross-Database

**Problema**: PostgreSQL usa tipo `UUID` nativo, SQLite no.

**Soluzione**: Custom TypeDecorator `GUID` (database.py:30-62)

```python
class GUID(TypeDecorator):
    """
    PostgreSQL → UUID nativo
    SQLite    → CHAR(36) con conversione automatica
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value  # UUID object
        else:
            return str(value)  # "abc-123-def-456"

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
```

**Uso nei modelli:**
```python
class Document(Base):
    id = Column(GUID, primary_key=True, default=uuid.uuid4)  # ✅
    user_id = Column(GUID, ForeignKey('users.id'))           # ✅

    # ❌ SBAGLIATO (solo PostgreSQL):
    # id = Column(UUID(as_uuid=True), primary_key=True)
```

---

## 6. Autenticazione Telegram

### 6.1 Perché Telegram Login Widget?

**Vantaggi:**
- ✅ Zero configurazione password
- ✅ Zero gestione email/reset password
- ✅ Multi-device automatico (stesso account Telegram)
- ✅ Sicuro (OAuth verificato da Telegram)
- ✅ UX fluida (se utente ha Telegram già loggato)

**Svantaggi:**
- ❌ Richiede account Telegram
- ❌ Non adatto a utenti business senza Telegram

**Alternativa futura**: Aggiungere anche Google/GitHub OAuth per enterprise tier.

### 6.2 Come Funziona

```
┌──────────┐                                    ┌──────────┐
│  Browser │                                    │ Telegram │
│   User   │                                    │ Servers  │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │ 1. Visita https://socrate-ai.app/            │
     │                                                │
     ▼                                                │
┌─────────────────────────────────────┐             │
│  Landing Page                       │             │
│  <script src="telegram-widget.js">  │             │
│  <div id="telegram-login">          │             │
│    Bot: @SocrateAIBot               │             │
│  </div>                              │             │
└────┬────────────────────────────────┘             │
     │                                                │
     │ 2. Click "Login with Telegram"                │
     ├───────────────────────────────────────────────►│
     │                                                │
     │         3. Telegram OAuth flow               │
     │            (se non già loggato)              │
     │◄───────────────────────────────────────────────┤
     │                                                │
     │ 4. Redirect con user data + hash              │
     │    /auth/telegram/callback?                    │
     │    id=123&first_name=Mario&hash=abc...        │
     │                                                │
     ▼                                                │
┌─────────────────────────────────────┐             │
│  Flask: verify_telegram_auth()      │             │
│                                      │             │
│  1. Calcola hash con BOT_TOKEN      │             │
│  2. Confronta con hash ricevuto     │             │
│  3. Se match → Utente autenticato   │             │
│  4. Crea sessione                    │             │
│  5. Redirect /dashboard              │             │
└─────────────────────────────────────┘             │
```

### 6.3 Verifica Sicurezza

**File: `api_server.py:56-85`**

```python
def verify_telegram_auth(auth_data: dict) -> bool:
    """
    Verifica che i dati vengano effettivamente da Telegram
    e non siano stati manomessi
    """
    # 1. Estrai hash ricevuto
    check_hash = auth_data.pop('hash', None)

    # 2. Crea stringa di verifica (tutti i parametri ordinati)
    data_check_string = '\n'.join([
        f"{k}={v}" for k, v in sorted(auth_data.items())
    ])
    # Esempio: "first_name=Mario\nid=123456\nusername=mariorossi"

    # 3. Calcola hash con secret key (SHA256 del bot token)
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # 4. Confronta
    return calculated_hash == check_hash
```

**Cosa previene:**
- ❌ Attaccante invia `id=999&first_name=Admin` → Hash non corrisponde
- ❌ Attaccante modifica `id=123` → Hash non corrisponde
- ✅ Solo Telegram può generare hash validi (conosce BOT_TOKEN)

### 6.4 Gestione Sessione

**Flask Session** (cookie criptato):

```python
# Dopo login verificato
session['user_id'] = str(user.id)
session['telegram_id'] = user.telegram_id
session['first_name'] = user.first_name

# Ogni richiesta protetta
@require_auth
def protected_endpoint():
    user_id = session.get('user_id')  # Recupera da cookie
    # ... operazioni ...
```

**Configurazione:**
```python
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
# ⚠️ Su Railway: usa SECRET_KEY random generato (es. openssl rand -hex 32)
```

### 6.5 Setup Bot Telegram

**1. Crea bot:**
```
Telegram → Cerca @BotFather → /newbot
Nome: Socrate AI Bot
Username: SocrateAIBot

BotFather ti darà: TOKEN (es. 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
```

**2. Configura dominio:**
```
@BotFather → /setdomain → @SocrateAIBot
Domain: web-production-38b1c.up.railway.app
```

**3. Aggiungi variabili Railway:**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=SocrateAIBot
```

---

## 7. Sistema Query AI

### 7.1 Flusso Query (da implementare)

```
┌──────────┐
│  Utente  │
│(Dashboard)│
└────┬─────┘
     │
     │ POST /api/query
     │ {document_id: "...", query: "Riassumi il capitolo 3"}
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                  FLASK API (Web Service)                │
│                                                         │
│  Step 1: Verifica autenticazione                       │
│  Step 2: Carica documento e metadata da R2             │
│  Step 3: Usa memvid per trovare chunk rilevanti        │
│  Step 4: Costruisci prompt per OpenRouter              │
│  Step 5: Chiama OpenRouter API                         │
│  Step 6: Salva risposta in chat_sessions               │
│  Step 7: Ritorna risposta al browser                   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Componenti da Implementare

**1. Memvid Query Engine**
```python
# Da implementare in: core/memvid_query.py

def find_relevant_chunks(query: str, metadata_file: str, top_k: int = 5) -> list:
    """
    Trova i chunk più rilevanti per la query

    Args:
        query: Domanda utente
        metadata_file: Path al metadata JSON su R2
        top_k: Numero chunk da ritornare

    Returns:
        Lista di chunk: [
            {'text': '...', 'page': 3, 'score': 0.89},
            ...
        ]
    """
    # 1. Carica metadata da R2
    metadata = json.loads(download_file(metadata_file))

    # 2. Calcola embeddings query
    query_embedding = get_embedding(query)

    # 3. Calcola similarity con ogni chunk
    scores = []
    for chunk in metadata['chunks']:
        chunk_embedding = chunk.get('embedding') or get_embedding(chunk['text'])
        similarity = cosine_similarity(query_embedding, chunk_embedding)
        scores.append((chunk, similarity))

    # 4. Ordina per score e ritorna top_k
    scores.sort(key=lambda x: x[1], reverse=True)
    return [{'text': chunk['text'], 'page': chunk['page'], 'score': score}
            for chunk, score in scores[:top_k]]
```

**2. OpenRouter Client**
```python
# Da implementare in: core/openrouter_client.py

import openai

# OpenRouter è compatibile con API OpenAI
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY')
)

def query_with_context(query: str, context_chunks: list, model: str = "gpt-4o-mini") -> dict:
    """
    Esegui query AI con contesto documento

    Args:
        query: Domanda utente
        context_chunks: Lista chunk rilevanti
        model: Modello da usare

    Returns:
        {
            'answer': '...',
            'sources': [{'page': 3, 'text': '...'}],
            'tokens_used': 1500,
            'cost_usd': 0.00045
        }
    """
    # 1. Costruisci prompt con contesto
    context_text = "\n\n".join([
        f"[Pagina {c['page']}]\n{c['text']}"
        for c in context_chunks
    ])

    prompt = f"""Basandoti sul seguente contenuto del documento, rispondi alla domanda.

CONTENUTO:
{context_text}

DOMANDA: {query}

RISPOSTA:"""

    # 2. Chiama OpenRouter
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Sei un assistente che risponde basandosi solo sul contenuto fornito."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    # 3. Estrai risultato
    answer = response.choices[0].message.content

    # 4. Calcola costi
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    cost = calcola_costo_query(input_tokens, output_tokens, model)

    return {
        'answer': answer,
        'sources': [{'page': c['page'], 'text': c['text'][:200]} for c in context_chunks],
        'tokens_used': input_tokens + output_tokens,
        'cost_usd': cost
    }
```

**3. Endpoint Query**
```python
# In api_server.py (già esistente, da completare)

@app.route('/api/query', methods=['POST'])
@require_auth
def custom_query():
    user_id = get_current_user_id()
    data = request.json

    document_id = data.get('document_id')
    query = data.get('query')

    # 1. Verifica documento
    doc = get_document_by_id(document_id, user_id)
    if doc.status != 'ready':
        return jsonify({'error': 'Document not ready'}), 400

    # 2. Trova chunk rilevanti
    metadata_file = doc.doc_metadata['metadata_file']
    relevant_chunks = find_relevant_chunks(query, metadata_file, top_k=5)

    # 3. Query OpenRouter
    result = query_with_context(query, relevant_chunks, model='gpt-4o-mini')

    # 4. Salva sessione
    session = create_chat_session(
        user_id=user_id,
        document_id=document_id,
        command_type='query',
        request_data={'query': query},
        channel='web_app'
    )

    update_chat_session(
        session_id=str(session.id),
        response_data=result,
        success=True,
        tokens_used=result['tokens_used']
    )

    # 5. Ritorna risposta
    return jsonify({
        'success': True,
        'answer': result['answer'],
        'sources': result['sources']
    })
```

### 7.3 Modelli Consigliati per Tier

```python
TIER_MODELS = {
    'free': 'gpt-4o-mini',              # Economico, veloce
    'pro': 'gpt-4o',                    # Bilanciato qualità/costo
    'enterprise': 'claude-3.5-sonnet'   # Massima qualità
}

def get_model_for_user(user: User) -> str:
    return TIER_MODELS.get(user.subscription_tier, 'gpt-4o-mini')
```

---

## 8. Monitoraggio e Debug

### 8.1 Log Railway in Real-Time

**Web Service logs:**
```
2025-10-14 20:15:32 [INFO] User logged in: 123456789 (Mario)
2025-10-14 20:15:45 [INFO] Document uploaded: abc-123 by user xyz-789
2025-10-14 20:15:46 [INFO] File uploaded to R2: users/xyz/docs/abc/documento.pdf
2025-10-14 20:15:46 [INFO] Processing task queued: task-id-123 for document abc-123
```

**Worker Service logs:**
```
2025-10-14 20:15:47 [INFO] Task tasks.process_document_task[task-id-123] received
2025-10-14 20:15:47 [INFO] Starting document processing: abc-123 for user xyz-789
2025-10-14 20:15:48 [INFO] Downloading file from R2: users/xyz/docs/abc/documento.pdf
2025-10-14 20:15:50 [INFO] File downloaded to temp: /tmp/xyz/documento.pdf
2025-10-14 20:15:51 [INFO] Starting memvid encoder...
2025-10-14 20:16:30 [INFO] Memvid encoder completed successfully
2025-10-14 20:16:31 [INFO] Document processing completed: abc-123
2025-10-14 20:16:32 [INFO] Temporary files cleaned up: /tmp/xyz
2025-10-14 20:16:32 [INFO] Task tasks.process_document_task[task-id-123] succeeded in 45.2s
```

### 8.2 Dashboard Monitoring (da implementare)

**Metriche Chiave:**

```python
# Admin dashboard: /admin/monitoring

{
    "services": {
        "web": {"status": "healthy", "uptime": "99.9%"},
        "worker": {"status": "healthy", "queue_size": 3},
        "redis": {"status": "healthy", "memory": "45MB/512MB"},
        "postgres": {"status": "healthy", "connections": 15}
    },
    "documents": {
        "total": 1523,
        "processing": 8,
        "ready": 1480,
        "failed": 35,
        "avg_processing_time": "32s"
    },
    "users": {
        "total": 456,
        "free": 320,
        "pro": 120,
        "enterprise": 16,
        "active_today": 89
    },
    "costs": {
        "r2_storage_gb": 23.5,
        "r2_cost_monthly": "€0.18",
        "ai_cost_daily": "€12.45",
        "ai_cost_monthly": "€373.50"
    }
}
```

### 8.3 Alert System (da implementare)

**Email/Telegram alerts quando:**

```python
ALERT_THRESHOLDS = {
    'worker_queue_depth': 50,        # >50 task in coda
    'failed_documents_rate': 0.05,   # >5% documenti falliti
    'r2_storage_percent': 0.80,      # >80% free tier R2
    'ai_cost_daily': 50.00,          # >€50/giorno AI costs
    'api_error_rate': 0.10           # >10% API errors
}

# Controllo ogni 5 minuti (Celery beat task)
@celery_app.task
def check_alerts():
    if get_queue_depth() > ALERT_THRESHOLDS['worker_queue_depth']:
        send_alert("Worker queue depth: {depth}")

    if get_failed_rate() > ALERT_THRESHOLDS['failed_documents_rate']:
        send_alert("High failure rate: {rate}%")

    # ... altri controlli ...
```

### 8.4 Debug Common Issues

**Issue 1: Document stuck in "processing"**
```sql
-- Trova documenti bloccati (>1 ora in processing)
SELECT id, filename, created_at
FROM documents
WHERE status = 'processing'
  AND created_at < NOW() - INTERVAL '1 hour';

-- Manualmente marca come failed
UPDATE documents
SET status = 'failed',
    error_message = 'Processing timeout - please retry'
WHERE id = 'document-id';
```

**Issue 2: Worker non processa task**
```bash
# Railway Worker Service logs
# Cerca:
[ERROR] Consumer: Cannot connect to redis://...
# → Redis down o credenziali sbagliate

# Oppure:
[WARNING] No tasks registered
# → celery_config.py non importa tasks.py
```

**Issue 3: R2 upload fails**
```bash
# Web Service logs
# Cerca:
[ERROR] R2 ClientError uploading 'users/.../file.pdf': NoSuchBucket
# → Bucket non esiste

[ERROR] R2 ClientError uploading 'users/.../file.pdf': InvalidAccessKeyId
# → Credenziali R2 sbagliate
```

---

## 9. Roadmap Implementazione

### Fase 1: ✅ COMPLETATA - Infrastruttura Base
**Durata**: 2 settimane
**Status**: DONE

- [x] Setup Railway (Web + Worker + PostgreSQL + Redis)
- [x] Autenticazione Telegram
- [x] Upload documenti su R2
- [x] Elaborazione asincrona con Celery
- [x] Dashboard base
- [x] Sistema quote storage (database, non applicato)

### Fase 2: 🚧 IN CORSO - Storage e Costi
**Durata**: 1 settimana
**Status**: 80% complete

- [x] Integrazione R2 completa
- [x] Test upload/download
- [x] Documentazione costi OpenRouter
- [x] Strategia monetizzazione
- [ ] Applicare quote storage (pre-upload check)
- [ ] Test end-to-end upload → processing → ready

### Fase 3: ⏳ PROSSIMA - Query AI
**Durata**: 2 settimane
**Status**: 0% (TODO)

**Priority 1: Memvid Query Engine**
- [ ] `core/memvid_query.py`: Implementare `find_relevant_chunks()`
- [ ] Embeddings per chunk (sentence-transformers)
- [ ] Cosine similarity search
- [ ] Test con documenti reali

**Priority 2: OpenRouter Integration**
- [ ] `core/openrouter_client.py`: Client API
- [ ] Gestione modelli per tier (free=gpt-4o-mini, pro=gpt-4o, enterprise=claude)
- [ ] Tracking token e costi
- [ ] Error handling e retry logic

**Priority 3: Query Endpoint**
- [ ] Completare `/api/query` endpoint
- [ ] Salvare costi in `chat_sessions`
- [ ] Frontend chat interface
- [ ] Test con vari tipi di query

### Fase 4: Ottimizzazione e Monetizzazione
**Durata**: 2 settimane
**Status**: 0% (TODO)

**Priority 1: Caching e Performance**
- [ ] Cache Redis per query comuni
- [ ] Ottimizzazione chunk selection (solo top_k più rilevanti)
- [ ] Output length control per tier
- [ ] Load testing (100 query concorrenti)

**Priority 2: Quota Enforcement**
- [ ] Pre-upload storage check
- [ ] Monthly AI cost tracking per user
- [ ] Quota exceeded warnings
- [ ] Auto-disable quando quota superata

**Priority 3: Stripe Integration**
- [ ] Account Stripe setup
- [ ] Checkout flow (free → pro, free → enterprise)
- [ ] Webhook per subscription events
- [ ] Invoice generation
- [ ] Cancellation flow

### Fase 5: Dashboard e UX
**Durata**: 1 settimana
**Status**: 0% (TODO)

**Priority 1: User Dashboard**
- [ ] Storage usage progress bar
- [ ] Document list con filtri (ready, processing, failed)
- [ ] Query history
- [ ] "Upgrade to Pro" CTA button
- [ ] Account settings (change tier, view invoices)

**Priority 2: Admin Dashboard**
- [ ] Real-time metrics (users, documents, costs)
- [ ] Failed documents monitoring
- [ ] User activity logs
- [ ] Cost projections
- [ ] Manual interventions (reset quota, mark failed, etc.)

### Fase 6: Advanced Features
**Durata**: 3 settimane
**Status**: 0% (TODO)

**Priority 1: Advanced Document Types**
- [ ] Video processing (memvid video encoder)
- [ ] PPTX/DOCX support
- [ ] Excel/CSV parsing
- [ ] Image OCR (per slide/scansioni)

**Priority 2: Advanced AI Features**
- [ ] Quiz generation
- [ ] Mind map generation
- [ ] Outline/summary generation
- [ ] Multi-document queries
- [ ] Custom prompts (enterprise tier)

**Priority 3: Collaboration (Enterprise)**
- [ ] Team accounts
- [ ] Document sharing
- [ ] Permissions management
- [ ] Activity audit logs

### Fase 7: Scale & Production
**Durata**: Continuo
**Status**: 0% (TODO)

**Priority 1: Monitoring**
- [ ] Sentry error tracking
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] PagerDuty alerts

**Priority 2: Performance**
- [ ] CDN per file statici
- [ ] Database query optimization
- [ ] Horizontal scaling (più worker)
- [ ] Caching layer (Redis/Memcached)

**Priority 3: Compliance**
- [ ] GDPR compliance audit
- [ ] Terms of Service
- [ ] Privacy Policy
- [ ] Cookie consent
- [ ] Data export functionality

---

## 10. Checklist Pre-Lancio

### 10.1 Sicurezza

- [ ] `SECRET_KEY` randomizzato su Railway (non default!)
- [ ] HTTPS enforced (Railway lo fa automaticamente)
- [ ] Rate limiting su API endpoints (flask-limiter)
- [ ] CORS configurato correttamente (solo domini trusted)
- [ ] Telegram bot domain configurato
- [ ] R2 buckets privati (no public access)
- [ ] Environment variables non committate su Git
- [ ] Database passwords strong (Railway auto-generate)
- [ ] SQL injection protected (SQLAlchemy ORM)
- [ ] XSS protected (Jinja2 auto-escape)

### 10.2 Performance

- [ ] Database indexes su colonne query frequenti
- [ ] Celery worker concurrency configurata (2-4 per worker)
- [ ] Redis maxmemory policy (allkeys-lru)
- [ ] File upload size limits (50MB free, 500MB pro, 5GB enterprise)
- [ ] Request timeout configurati (120s per upload)
- [ ] Connection pooling database (SQLAlchemy default)
- [ ] Lazy loading immagini dashboard
- [ ] Gzip compression abilitata (Railway default)

### 10.3 Monitoring

- [ ] Health check endpoints funzionanti (/api/health)
- [ ] Railway deployment notifications (email/Slack)
- [ ] Error logging configurato (Python logging)
- [ ] Failed document alerts (email admin)
- [ ] Storage usage monitoring (80% threshold)
- [ ] AI cost monitoring (daily/monthly reports)
- [ ] Uptime monitoring (UptimeRobot)

### 10.4 Business

- [ ] Stripe account setup e testato
- [ ] Prezzi tier finali decisi
- [ ] Terms of Service pubblicati
- [ ] Privacy Policy pubblicata
- [ ] Support email configurato (support@socrate-ai.com)
- [ ] Onboarding flow utenti testato
- [ ] Landing page con value proposition
- [ ] FAQ page
- [ ] Documentazione API (se enterprise ha accesso API)

### 10.5 Testing

- [ ] Upload PDF funzionante
- [ ] Processing completo end-to-end
- [ ] Query AI con risposta corretta
- [ ] Login Telegram funzionante
- [ ] Logout e re-login
- [ ] Storage quota enforcement
- [ ] Upgrade tier (free → pro)
- [ ] Payment flow completo
- [ ] Mobile responsive (dashboard)
- [ ] Cross-browser testing (Chrome, Safari, Firefox)

### 10.6 Documentazione

- [ ] README.md aggiornato
- [ ] API documentation (se public API)
- [ ] Setup guide per developer
- [ ] Troubleshooting common issues
- [ ] Architecture diagram
- [ ] Database schema documentato
- [ ] Environment variables documented
- [ ] Deployment guide

---

## Appendice A: Comandi Utili

### Railway CLI

```bash
# Login
railway login

# Link progetto
railway link

# Visualizza logs
railway logs --service web
railway logs --service worker

# Esegui comando nel container
railway run --service web python

# Deploy manuale
railway up

# Variabili
railway variables
```

### Database Management

```bash
# Connetti a PostgreSQL Railway
railway connect postgres

# Dump database
pg_dump $DATABASE_URL > backup.sql

# Restore database
psql $DATABASE_URL < backup.sql

# Migrations (futuro, con Alembic)
alembic revision --autogenerate -m "Add cost tracking"
alembic upgrade head
```

### Celery Management

```bash
# Status worker
celery -A celery_config inspect active

# Purge queue
celery -A celery_config purge

# Revoke task
celery -A celery_config revoke <task-id>

# Monitor (flower)
celery -A celery_config flower  # http://localhost:5555
```

### R2 Management

```bash
# Via AWS CLI (installare aws-cli)
aws s3 ls --endpoint-url=$R2_ENDPOINT_URL s3://socrate-ai-storage/

# Upload test file
aws s3 cp test.txt --endpoint-url=$R2_ENDPOINT_URL s3://socrate-ai-storage/test/

# Download
aws s3 cp --endpoint-url=$R2_ENDPOINT_URL s3://socrate-ai-storage/test/test.txt .

# Delete
aws s3 rm --endpoint-url=$R2_ENDPOINT_URL s3://socrate-ai-storage/test/test.txt
```

---

## Appendice B: Risorse Esterne

### Documentazione

- **Railway**: https://docs.railway.app/
- **Cloudflare R2**: https://developers.cloudflare.com/r2/
- **Celery**: https://docs.celeryq.dev/
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Telegram Login Widget**: https://core.telegram.org/widgets/login
- **OpenRouter**: https://openrouter.ai/docs

### Community

- **Discord Socrate AI**: (da creare)
- **GitHub Issues**: https://github.com/Cilluzzo79/Socrate-AI/issues
- **Stack Overflow tag**: [socrate-ai]

---

**Fine Documento**

Versione: 1.0
Ultimo Aggiornamento: 14 Ottobre 2025
Prossima Revisione: Dopo Fase 3 (Query AI implementata)
