# Analisi Problemi Camera Batch Upload

**Data**: 19 Ottobre 2025
**Stato**: In Investigazione con Eruda Mobile Console Attivo

## Problemi Identificati dall'Utente

### 1. Primo Scatto Non Acquisito
**Sintomo**: "il primo scatto con camera, non viene ma acquisito tra le immagini"

**Causa Probabile - Race Condition**:
Il problema si trova in `dashboard.js` linee 526-554, funzione `handleCameraCapture()`:

```javascript
function handleCameraCapture(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        // L'immagine viene aggiunta all'array QUI (asincrono)
        capturedImages.push({
            file: file,
            dataUrl: e.target.result
        });
        showBatchPreview();
    };
    reader.readAsDataURL(file);  // Operazione ASINCRONA

    // PROBLEMA: Reset immediato prima che FileReader finisca
    document.getElementById('camera-input').value = '';
}
```

**Spiegazione**:
- `FileReader.readAsDataURL()` è un'operazione **asincrona**
- Il reset dell'input (`.value = ''`) avviene **immediatamente**
- Su mobile con immagini grandi o connessione lenta, il callback `reader.onload` potrebbe ritardare
- Se l'utente scatta la seconda foto prima che il primo FileReader finisca, la prima immagine potrebbe andare persa

**Soluzione Proposta**:
Spostare il reset dell'input DENTRO il callback `reader.onload`:

```javascript
function handleCameraCapture(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        capturedImages.push({
            file: file,
            dataUrl: e.target.result
        });
        showBatchPreview();

        // Reset DOPO che l'immagine è stata caricata
        document.getElementById('camera-input').value = '';
    };
    reader.readAsDataURL(file);
}
```

### 2. Scatti Successivi Acquisiti in Modo Alternato
**Sintomo**: "gli altri vengono acuisiti in modo aleterni nel catalgo"

**Possibili Cause**:
1. Stesso problema della race condition sopra
2. L'utente clicca rapidamente e il FileReader non fa in tempo
3. Il modal `showBatchPreview()` che si apre e chiude interferisce con il flusso

**Da Verificare con Eruda Console**:
- Guardare i log `[CAMERA]` per vedere quanti `handleCameraCapture` vengono chiamati
- Verificare se ci sono errori nel `FileReader.onerror`
- Controllare il valore di `capturedImages.length` prima di ogni `showBatchPreview()`

### 3. File Singoli Creati Oltre al PDF
**Sintomo**: "viene creato oltre i singoli file contenenti le singole immaggini un file in pdf che però dipende dal caricamento degli altri singoli file"

**Analisi Codice Backend** (`api_server.py` linee 439-568):
L'endpoint `/api/documents/upload-batch` dovrebbe creare **SOLO UN PDF**, non file singoli.

```python
# api_server.py linee 538-568
# Questo codice crea UN SOLO documento PDF
doc = create_document(
    user_id=user_id,
    filename=pdf_filename,  # Unico PDF
    original_filename=pdf_filename,
    file_path=file_key,
    file_size=pdf_size,
    mime_type='application/pdf'
)
```

**Possibile Causa**:
1. **Chiamate multiple agli endpoint**: Forse sia `/api/documents/upload-batch` CHE `/api/documents/upload` vengono chiamati
2. **Event listener duplicato sul file-input**: Il `file-input` normale potrebbe essere triggered insieme al `camera-input`

**Da Verificare con Eruda Console - Tab Network**:
- Quante richieste POST vengono fatte?
- A quali endpoint? `/api/documents/upload` o `/api/documents/upload-batch`?
- Quanti file vengono inviati in ogni richiesta?

## Potenziali Conflitti nel Codice

### Conflitto 1: Upload Area Click vs Camera Button

**dashboard.html linee 196-198**:
```javascript
uploadArea.addEventListener('click', () => {
    fileInput.click();  // Apre file-input NORMALE
});
```

**dashboard.html linee 179**:
```html
<button onclick="openCamera()">Scatta Foto</button>
```

Il pulsante "Scatta Foto" è DENTRO `uploadArea`. Questo potrebbe causare:
1. Click sul pulsante camera → `openCamera()` viene chiamato
2. Ma l'evento bubbling trigger anche il click listener dell'upload area
3. Entrambi i file input (normale e camera) vengono aperti

**Soluzione**: Stopare la propagazione dell'evento nel pulsante camera.

### Conflitto 2: File Input Change Listener

**dashboard.html linee 221-225**:
```javascript
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);  // Upload SINGOLO
    }
});
```

Se questo listener si attiva quando l'utente usa la camera, potrebbe uploadare i file singolarmente invece che in batch.

## Passi Debug Raccomandati

### Step 1: Verificare Sequenza Chiamate
Con Eruda console aperta, scattare 3 foto e verificare:
1. Quante volte viene chiamato `[CAMERA] handleCameraCapture`?
2. Quante volte viene chiamato `[BATCH] showBatchPreview`?
3. Qual è il valore di `capturedImages.length` ogni volta?

### Step 2: Verificare Network Tab
Nella tab Network di Eruda:
1. Filtrare per richieste POST
2. Verificare quante richieste a `/api/documents/upload-batch`
3. Verificare se ci sono richieste a `/api/documents/upload` (non dovrebbe)
4. Controllare i payload di ogni richiesta

### Step 3: Verificare Event Listener
Nel console Eruda, digitare:
```javascript
console.log('FileInput listeners:', getEventListeners(document.getElementById('file-input')));
console.log('CameraInput listeners:', getEventListeners(document.getElementById('camera-input')));
```

### Step 4: Test con Console Log Aggiuntivi
Aggiungere temporaneamente:
```javascript
// In handleFileUpload (dashboard.html)
async function handleFileUpload(file) {
    console.log('[SINGLE-UPLOAD] handleFileUpload called with:', file.name);
    // ...resto del codice
}
```

Questo aiuterà a capire se `handleFileUpload` viene mai chiamato quando si usa la camera.

## Fix Proposti

### Fix 1: Risoluzione Race Condition (PRIORITÀ ALTA)
**File**: `static/js/dashboard.js`
**Linee**: 526-554

Modificare `handleCameraCapture()` per resettare l'input SOLO dopo che FileReader ha completato:

```javascript
function handleCameraCapture(file) {
    console.log('[CAMERA] handleCameraCapture called with file:', file.name, file.type, file.size);

    const reader = new FileReader();
    reader.onload = function(e) {
        console.log('[CAMERA] FileReader onload - image loaded, length:', e.target.result.length);

        capturedImages.push({
            file: file,
            dataUrl: e.target.result
        });
        console.log('[CAMERA] Image added to batch. Total images:', capturedImages.length);

        // IMPORTANTE: Reset DOPO l'aggiunta all'array
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) {
            cameraInput.value = '';
            console.log('[CAMERA] Camera input reset AFTER image loaded');
        }

        console.log('[CAMERA] Calling showBatchPreview()...');
        showBatchPreview();
        console.log('[CAMERA] showBatchPreview() returned');
    };

    reader.onerror = function(error) {
        console.error('[CAMERA] FileReader error:', error);
        // Anche in caso di errore, reset input
        document.getElementById('camera-input').value = '';
    };

    reader.readAsDataURL(file);
}
```

### Fix 2: Prevenire Event Bubbling Camera Button (PRIORITÀ MEDIA)
**File**: `templates/dashboard.html`
**Linee**: 179

Modificare il pulsante camera per stopare la propagazione:

```html
<button type="button" class="btn-camera" id="camera-btn"
        onclick="event.stopPropagation(); openCamera();">
    <!-- SVG icon -->
    <span>Scatta Foto</span>
</button>
```

O meglio, rimuovere onclick e usare event listener:

```javascript
// In dashboard.html, dopo setupUploadHandlers()
document.getElementById('camera-btn')?.addEventListener('click', function(e) {
    e.stopPropagation();  // Previene trigger dell'upload area
    e.preventDefault();
    openCamera();
});
```

### Fix 3: Distinguere Camera Input da File Input (PRIORITÀ BASSA)
**File**: `templates/dashboard.html`
**Linee**: 221-225

Verificare che il listener del file-input normale non si triggeri mai per camera-input:

```javascript
fileInput.addEventListener('change', (e) => {
    // Verifica che non sia il camera-input
    if (e.target.id === 'camera-input') {
        console.warn('[CONFLICT] file-input listener triggered by camera-input!');
        return;  // Ignora
    }

    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});
```

## Informazioni da Raccogliere

Prima di applicare i fix, raccogliere:

1. **Eruda Console Logs**: Screenshot dei log `[CAMERA]` e `[BATCH]` durante una sessione di 3 foto
2. **Eruda Network Tab**: Screenshot delle richieste POST durante batch upload
3. **Numero di documenti creati**: Dopo batch upload di 3 foto, quanti documenti appaiono nella dashboard?
4. **Contenuto documenti**: I file singoli sono le immagini JPG o cosa?

## Note Aggiuntive

- Eruda è attivo e rimarrà attivo fino a risoluzione completi problemi
- Debug logs (prefisso `[CAMERA]` e `[BATCH]`) sono già presenti nel codice
- Versione JavaScript attuale: `DEBUG-BATCH-PREVIEW-19OCT2025`
- Backend endpoint `/api/documents/upload-batch` è corretto e crea solo 1 PDF

## Prossimi Passi

1. ✅ Eruda mobile console attivata
2. ✅ Debug logging attivo
3. ✅ Raccolta log e screenshot da test su smartphone
4. ✅ Analisi log per confermare ipotesi race condition
5. ✅ Applicazione Fix 1 (race condition) - DEPLOYED
6. ✅ Test dopo Fix 1 - CONFERMATO FUNZIONANTE
7. ✅ Applicazione Fix 2 (duplicate upload calls) - DEPLOYED
8. ✅ Applicazione Fix 3 (cache invalidation) - DEPLOYED
9. ✅ Consulenza Backend Master Analyst - COMPLETATA
10. ⏳ Applicazione Fix Backend (idempotency + memory-efficient PDF)
11. ⏳ Test dopo Fix Backend con Eruda Network tab
12. ⏳ Pulizia debug logs e rimozione Eruda

---

**Ultimo aggiornamento**: 20 Ottobre 2025, ore 02:00

## Changelog Fix Applicati

### Fix 1: Race Condition Camera Input (19 Ottobre 2025, ore 19:30)
**File**: `static/js/dashboard.js`
**Commit**: f1c4274

Spostato `cameraInput.value = ''` DENTRO il callback `reader.onload` per garantire che il reset avvenga DOPO che l'immagine sia stata caricata nell'array. Test utente ha confermato:
- Tutte le foto vengono acquisite correttamente
- Log Eruda mostrano sequenza corretta: `Total images: 1, 2, 3`
- Reset input avviene DOPO `FileReader onload`

### Fix 2: Duplicate Upload Calls (20 Ottobre 2025, ore 01:00)
**File**: `templates/dashboard.html` (linee 385-395)
**Commit**: 6f86030

Aggiunto check nel listener del `file-input` per ignorare eventi provenienti da `camera-input`:
```javascript
fileInput.addEventListener('change', (e) => {
    // Prevent handling camera-input events
    if (e.target.id === 'camera-input') {
        console.log('[CONFLICT] file-input listener blocked camera-input event');
        return;
    }
    // ... resto del codice
});
```

Questo dovrebbe risolvere:
- Chiamate duplicate a `/upload` (file singoli)
- Creazione di documenti individuali oltre al PDF batch
- **DA VERIFICARE CON TEST UTENTE SU ERUDA NETWORK TAB**

### Fix 3: Cache Invalidation (20 Ottobre 2025, ore 01:30)
**File**: `static/js/dashboard.js` (linee 4, 7)
**Commit**: c3040f0

Cambiato il version string DENTRO il file JavaScript da `GLOBAL-SCOPE-FIX-19OCT2025` a `FIX-DUPLICATE-UPLOAD-19OCT2025`:
```javascript
/**
 * VERSION: FIX-DUPLICATE-UPLOAD-19OCT2025
 */
console.log('[DASHBOARD.JS] VERSION: FIX-DUPLICATE-UPLOAD-19OCT2025');
```

Questo forza il browser a ricaricare il file perché il contenuto è cambiato, non solo il query parameter. Risolve il problema di cache aggressiva su mobile browser.

---

## Analisi Backend Master Analyst (20 Ottobre 2025, ore 02:00)

Consultato backend-master-analyst per analisi approfondita. Report completo: `BACKEND_ANALYSIS_CAMERA_BATCH.md`

### Problemi CRITICAL Identificati:

**1. Missing Idempotency Check** (Causa probabile dei duplicati)
- Nessun controllo per prevenire upload duplicati lato server
- Anche con fix frontend, doppio click o retry di rete crea documenti duplicati
- Soluzione: Hash contenuto + check negli ultimi 5 minuti

**2. Memory Exhaustion** ⚠️ (Causa dell'errore PDF da 5MB!)
- Tutte le immagini caricate in memoria simultaneamente
- Foto 4000x3000 = ~36MB RAM per immagine
- 3 foto = 100MB+ per richiesta → OOM kill → documento in "Errore"
- Soluzione: Processare immagini una alla volta, resize, salvataggio su disco

### Problemi MAJOR Identificati:

**3. Missing Transaction Boundaries**
- Race condition su `user.storage_used_mb`
- Crash tra update storage e commit → quota inflazionata permanentemente

**4. Race Condition Concurrent Uploads**
- Click rapidi multipli → upload batch simultanei
- Soluzione: Redis lock user-specific

**5. No Retry Logic**
- Task failure = documento bloccato in "processing" per sempre
- Nessun timeout handling
- Soluzione: Celery retry con soft/hard timeout

### Raccomandazione:

**FASE 1 (Deploy immediato):**
1. Idempotency check (previene duplicati)
2. Memory-efficient PDF generation (risolve errore PDF)

Questi 2 fix risolveranno i problemi principali riportati dall'utente.
