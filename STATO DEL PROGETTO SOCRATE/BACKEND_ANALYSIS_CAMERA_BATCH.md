# Backend Analysis - Camera Batch Upload Feature

**Data**: 20 Ottobre 2025, ore 02:00
**Analista**: Backend Master Analyst
**Status**: 2 CRITICAL, 3 MAJOR, 2 MINOR issues identificati

---

## Executive Summary

L'analisi backend ha rivelato che **i fix frontend applicati sono corretti**, ma esistono vulnerabilità critiche lato server che possono causare:
- Creazione di documenti duplicati nonostante i fix frontend
- Esaurimento memoria (OOM) con batch di foto grandi
- Corruzione dati per mancanza di transazioni atomiche
- Documenti bloccati in stato "processing" senza recovery

## 🚨 Critical Issues

### 1. Missing Idempotency Check - Upload Duplicati

**Severità**: CRITICAL
**File**: `api_server.py`, linee 439-568
**Endpoint**: `/api/documents/upload-batch`

**Problema**:
Anche con i fix frontend, se l'utente clicca rapidamente o la rete ritrasmette, il backend crea documenti duplicati con contenuto identico ma ID diversi.

**Causa**:
```python
# Linea 459 - Ogni richiesta genera un nuovo UUID
file_key = f"documents/{user_id}/{uuid.uuid4()}/{pdf_filename}"
```

Non c'è controllo per verificare se lo stesso contenuto è già stato caricato recentemente.

**Soluzione Raccomandata**:
```python
import hashlib
from datetime import datetime, timedelta

# Calcolare hash del contenuto PRIMA di processare
content_hash = hashlib.sha256()
for file in files:
    file.seek(0)
    content_hash.update(file.read())
    file.seek(0)
content_fingerprint = content_hash.hexdigest()

# Cercare upload duplicati negli ultimi 5 minuti
five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
existing_doc = db.query(Document).filter(
    Document.user_id == uuid.UUID(user_id),
    Document.doc_metadata['content_hash'].astext == content_fingerprint,
    Document.created_at > five_minutes_ago
).first()

if existing_doc:
    logger.warning(f"Duplicate upload detected for user {user_id}")
    return jsonify({
        'success': True,
        'document_id': str(existing_doc.id),
        'duplicate': True,
        'message': 'Documento già in elaborazione'
    }), 200

# Salvare hash nei metadata per check futuri
doc_metadata = {'content_hash': content_fingerprint}
```

**Priorità**: IMMEDIATA - Deploy questo fix prima di testare con l'utente

---

### 2. Memory Exhaustion Risk - PDF da 5MB va in errore

**Severità**: CRITICAL
**File**: `api_server.py`, linee 461-509

**Problema**:
Questo spiega perché il PDF da 5.08 MB dell'utente è andato in "Errore"!

Il codice attuale carica TUTTE le immagini in memoria simultaneamente:
```python
# Linee 462-484
pdf_images = []
for file in files:
    image_content = file.read()  # Foto 4000x3000 = ~36MB in RAM
    img = Image.open(io.BytesIO(image_content))
    pdf_images.append(img)  # Tutte le foto in memoria contemporaneamente
```

Con 3 foto da 2-3MB ciascuna, si arriva facilmente a 100MB+ di RAM per richiesta. Sotto carico concorrente → OOM kill → documento bloccato in "processing".

**Soluzione Raccomandata**:
```python
import tempfile

# Processare una foto alla volta, salvando su disco
with tempfile.TemporaryDirectory() as temp_dir:
    processed_paths = []

    for idx, file in enumerate(files):
        image_content = file.read()
        total_size += len(image_content)

        # Limite cumulativo
        if total_size > 50 * 1024 * 1024:  # 50MB max
            return jsonify({'error': 'Batch supera 50MB'}), 413

        temp_path = os.path.join(temp_dir, f"page_{idx:03d}.jpg")

        with Image.open(io.BytesIO(image_content)) as img:
            # RESIZE per ridurre memoria (max 2000px lato lungo)
            img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Salva su disco, libera memoria
            img.save(temp_path, 'JPEG', quality=85, optimize=True)
            processed_paths.append(temp_path)

        del image_content  # Free memory immediatamente

    # Usa img2pdf per conversione memory-efficient
    import img2pdf
    pdf_content = img2pdf.convert(processed_paths)
```

**Priorità**: IMMEDIATA - Questo risolverà l'errore del PDF da 5MB

---

## ⚠️ Major Issues

### 3. Missing Transaction Boundaries - Race Condition Storage Quota

**Severità**: MAJOR
**File**: `core/document_operations.py`, linee 83-116
**Funzione**: `create_document()`

**Problema**:
Se l'app crasha dopo aver aggiornato `user.storage_used_mb` (linea 109) ma prima del commit (linea 111), la quota storage dell'utente è inflazionata permanentemente senza documento corrispondente.

**Soluzione**:
```python
def create_document(...):
    db = SessionLocal()
    try:
        # Transazione esplicita con lock
        with db.begin():
            user = db.query(User).filter_by(id=uuid.UUID(user_id))\
                     .with_for_update().first()  # LOCK per prevenire race

            if not user:
                raise ValueError(f"User {user_id} not found")

            # Check quota atomico
            file_size_mb = file_size / (1024 * 1024)
            if user.storage_used_mb + file_size_mb > user.storage_quota_mb:
                raise ValueError("Storage quota exceeded")

            # Crea documento
            doc = Document(...)
            db.add(doc)

            # Aggiorna storage atomicamente
            user.storage_used_mb += file_size_mb

            # Commit automatico alla fine del with block
            db.refresh(doc)
            return doc

    except Exception as e:
        # Rollback automatico
        logger.error(f"Failed to create document: {e}")
        raise
    finally:
        db.close()
```

---

### 4. Race Condition - Concurrent Batch Uploads

**Severità**: MAJOR
**File**: `api_server.py`, linee 439-568

**Problema**:
Se l'utente clicca il pulsante camera più volte rapidamente (prima che appaia il modal), possono partire richieste batch simultanee.

**Soluzione con Redis Lock**:
```python
import redis
redis_client = redis.from_url(os.getenv('REDIS_URL'))

@app.route('/api/documents/upload-batch', methods=['POST'])
@require_auth
def upload_batch_documents():
    user_id = get_current_user_id()

    # Lock user-specific
    lock_key = f"upload_lock:{user_id}"
    lock_acquired = redis_client.set(lock_key, "1", nx=True, ex=30)

    if not lock_acquired:
        return jsonify({
            'success': False,
            'error': 'Upload già in corso',
            'retry_after': 5
        }), 429  # Too Many Requests

    try:
        # ... logica upload esistente ...

        # Memorizza upload recente
        redis_client.setex(f"recent_upload:{user_id}", 60, str(doc.id))

        return response

    finally:
        redis_client.delete(lock_key)
```

---

### 5. PDF Processing Error - No Retry Logic

**Severità**: MAJOR
**File**: `tasks.py`, linee 23-393
**Task**: `process_document_task`

**Problema**:
Quando il processing fallisce (timeout, errore PIL, memoria), il documento rimane in "processing" per sempre. Nessun retry, nessun timeout, nessuna notifica utente.

**Soluzione**:
```python
from celery.exceptions import SoftTimeLimitExceeded

@celery_app.task(
    bind=True,
    name='tasks.process_document_task',
    max_retries=3,
    soft_time_limit=300,  # 5 minuti soft
    time_limit=600,       # 10 minuti hard
    autoretry_for=(Exception,),
    retry_backoff=True
)
def process_document_task(self, document_id: str, user_id: str):
    try:
        # ... logica esistente ...
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for document {document_id}")
        update_document_status(
            document_id,
            user_id,
            status='failed',
            error_message='Timeout - documento troppo grande o complesso'
        )
        raise
```

---

## ℹ️ Minor Issues

### 6. Event Listener Architecture - Fragile

**Severità**: MINOR
**File**: `templates/dashboard.html`, linee 385-395

**Problema**:
Il check `if (e.target.id === 'camera-input')` è fragile. Meglio usare handler separati.

**Soluzione**:
```javascript
const fileInput = document.getElementById('file-input');
const cameraInput = document.getElementById('camera-input');

// Handler separato per file-input (NON gestisce camera)
fileInput.addEventListener('change', function(e) {
    if (e.target === fileInput && e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
}, false);

// Handler separato per camera-input
cameraInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        handleCameraCapture(e.target.files[0]);
    }
    e.stopPropagation();  // Previene bubbling
}, false);
```

---

### 7. Input Validation - Path Traversal Risk

**Severità**: MINOR
**File**: `api_server.py`, linea 446

**Problema**:
`document_name` non è sanitizzato. Utente malintenzionato potrebbe iniettare caratteri pericolosi.

**Soluzione**:
```python
import re

document_name = request.form.get('document_name', '')
document_name = re.sub(r'[^a-zA-Z0-9\-_\s]', '', document_name)[:100]
if not document_name:
    document_name = f'documento-{datetime.now().strftime("%Y%m%d%H%M%S")}'
```

---

## ✅ Positive Observations

1. **Frontend fixes corretti**: La race condition e il duplicate upload check sono implementati correttamente
2. **Progress tracking**: Celery task aggiorna correttamente lo stato
3. **R2 integration**: Storage cloud ha error handling appropriato
4. **Security**: Autenticazione Telegram implementata correttamente
5. **Cleanup**: File temporanei vengono puliti dopo processing

---

## 📋 Action Plan Prioritizzato

### Fase 1: Fix Immediati (Deploy Entro 1 Ora)

1. **Idempotency Check** (Issue #1)
   - File: `api_server.py`
   - Tempo stimato: 15 minuti
   - Priorità: MASSIMA
   - Previene documenti duplicati

2. **Memory-Efficient PDF Generation** (Issue #2)
   - File: `api_server.py`
   - Tempo stimato: 30 minuti
   - Priorità: MASSIMA
   - Risolve errore PDF da 5MB

### Fase 2: Hardening (Deploy Entro 24 Ore)

3. **Transaction Management** (Issue #3)
   - File: `core/document_operations.py`
   - Tempo stimato: 20 minuti
   - Previene corruzione storage quota

4. **Upload Locking** (Issue #4)
   - File: `api_server.py`
   - Tempo stimato: 15 minuti
   - Previene race condition upload concorrenti

5. **Task Retry Logic** (Issue #5)
   - File: `tasks.py`
   - Tempo stimato: 20 minuti
   - Gestisce timeout e retry

### Fase 3: Refactoring (Deploy Entro 1 Settimana)

6. **Event Listener Refactor** (Issue #6)
7. **Input Validation** (Issue #7)

---

## 🧪 Test Plan

Dopo deploy Fase 1 (fix immediati), testare:

1. **Idempotency Test**:
   - Scattare 3 foto
   - Cliccare "Carica" 2 volte rapidamente
   - Verificare: Solo 1 documento creato
   - Log atteso: `[WARN] Duplicate upload detected`

2. **Memory Test**:
   - Scattare 5-6 foto ad alta risoluzione
   - Verificare: PDF creato con successo
   - Status: "Pronto" (non "Errore")
   - Dimensione PDF: Ottimizzata (non >10MB)

3. **Eruda Network Test**:
   - Verificare solo 1 POST a `/upload-batch`
   - Nessun POST a `/upload` (singolo)
   - Response 200 OK con `document_id`

---

## 📊 Overall Assessment

**Rating**: 6.5/10

**Strengths**:
- Frontend fixes corretti e ben implementati
- Buona architettura base (Flask + Celery + R2)
- Security basics solidi

**Weaknesses**:
- Mancanza di defensive programming lato server
- No idempotency / deduplication
- Memory management inefficiente
- Missing transaction boundaries
- No retry logic per task failures

**Conclusione**:
I fix frontend sono corretti, ma il backend necessita di hardening immediato per prevenire:
- Data corruption
- Memory exhaustion (causa dell'errore PDF)
- Duplicate uploads
- Race conditions

**Fix Fase 1 risolveranno l'errore PDF da 5MB e preveniranno duplicati.**

---

## 📝 Note per Developer

- Tutti i fix sono backward-compatible
- Non richiedono migration database
- Possono essere deployati incrementalmente
- Testing consigliato su staging prima di production
- Redis già disponibile su Railway (usato da Celery)

**Ultimo aggiornamento**: 20 Ottobre 2025, ore 02:00
