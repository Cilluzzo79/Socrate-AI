# FIX 11 Alternative A: Deployment Plan

**Approach**: OCR Pre-PDF in api_server.py
**Timeline**: 3.5 hours to production
**Risk Level**: LOW
**Dependencies**: None (pure Python, existing stack)

---

## Implementation Checklist

### Phase 1: Code Implementation (2 hours)

#### Task 1.1: Modify `api_server.py` (60 min)

**File**: `D:\railway\memvid\api_server.py`
**Location**: Lines 439-658 (function `upload_batch_documents`)

**Changes**:

```python
# INSERT AFTER LINE 560 (after image processing loop, before PDF creation)

        # ============================================================================
        # FIX 11 ALT A: Apply OCR to all images BEFORE PDF creation
        # ============================================================================
        ocr_texts = []
        logger.info(f"[BATCH-OCR] Applying OCR to {len(processed_paths)} images...")

        for idx, img_path in enumerate(processed_paths):
            try:
                # Read processed image from disk
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()

                # Apply OCR using existing core.ocr_processor
                from core.ocr_processor import extract_text_from_image
                ocr_result = extract_text_from_image(img_bytes, f"page_{idx+1}.jpg")

                if ocr_result['success'] and ocr_result.get('text'):
                    ocr_text = ocr_result['text'].strip()
                    ocr_texts.append(ocr_text)
                    char_count = len(ocr_text)
                    word_count = len(ocr_text.split())
                    logger.info(f"[BATCH-OCR] ✅ Page {idx+1}: {char_count} chars, {word_count} words extracted")
                else:
                    ocr_texts.append("")
                    error_msg = ocr_result.get('error', 'Unknown error')
                    logger.warning(f"[BATCH-OCR] ⚠️ Page {idx+1}: OCR failed - {error_msg}")

            except Exception as e:
                logger.error(f"[BATCH-OCR] ❌ Error on page {idx+1}: {e}", exc_info=True)
                ocr_texts.append("")

        # Validate OCR results
        successful_ocr = sum(1 for text in ocr_texts if len(text.strip()) > 0)
        logger.info(f"[BATCH-OCR] Summary: {successful_ocr}/{len(ocr_texts)} pages successfully OCR'd")

        if successful_ocr == 0:
            logger.error("[BATCH-OCR] ❌ All OCR attempts failed, PDF will have no text")
            return jsonify({
                'error': 'Nessun testo estratto dalle immagini. Verificare la qualità delle foto.'
            }), 400
```

**Then MODIFY line 633** (in the `update_document_status` call):

```python
# REPLACE EXISTING (lines 628-638):
update_document_status(
    str(doc.id),
    user_id,
    status='processing',
    doc_metadata={
        'task_id': task.id,
        'source_images_count': len(files),
        'content_hash': content_fingerprint
    }
)

# WITH NEW VERSION:
update_document_status(
    str(doc.id),
    user_id,
    status='processing',
    doc_metadata={
        'task_id': task.id,
        'source_images_count': len(files),
        'content_hash': content_fingerprint,
        'ocr_texts': ocr_texts,  # FIX 11 ALT A: Pre-computed OCR
        'has_ocr_metadata': True,  # Flag for encoder
        'ocr_summary': {
            'total_pages': len(ocr_texts),
            'successful_pages': successful_ocr,
            'total_characters': sum(len(t) for t in ocr_texts),
            'total_words': sum(len(t.split()) for t in ocr_texts)
        }
    }
)
```

**Testing Checkpoint**:
- Verify syntax (no Python errors)
- Verify imports work
- Verify OCR function exists in `core.ocr_processor`

---

#### Task 1.2: Modify `tasks.py` (30 min)

**File**: `D:\railway\memvid\tasks.py`
**Location**: Lines 95-150 (function `process_document_task`)

**Changes**:

**STEP 1**: Add OCR metadata extraction (INSERT AFTER line 100):

```python
        # ============================================================================
        # FIX 11 ALT A: Extract OCR metadata if available
        # ============================================================================
        ocr_metadata = None
        if doc.doc_metadata and doc.doc_metadata.get('has_ocr_metadata'):
            ocr_texts = doc.doc_metadata.get('ocr_texts', [])
            if ocr_texts and len(ocr_texts) > 0:
                ocr_metadata = {
                    'ocr_texts': ocr_texts,
                    'page_count': len(ocr_texts)
                }
                logger.info(f"[FIX-11-ALT-A] Found pre-computed OCR metadata for {len(ocr_texts)} pages")
                logger.info(f"[FIX-11-ALT-A] Total OCR text: {sum(len(t) for t in ocr_texts)} characters")
            else:
                logger.warning("[FIX-11-ALT-A] has_ocr_metadata=True but ocr_texts is empty")
        else:
            logger.info("[FIX-11-ALT-A] No OCR metadata found, will use PyPDF2 extraction")
```

**STEP 2**: Pass OCR metadata to encoder (MODIFY line 144):

```python
        # REPLACE EXISTING (line 144):
        success = process_file_in_sections(
            file_path=temp_file_path,
            chunk_size=optimal_config['chunk_size'],
            overlap=optimal_config['overlap'],
            output_format='json',
            max_pages=None,
            max_chunks=optimal_config['max_chunks']
        )

        # WITH NEW VERSION:
        success = process_file_in_sections(
            file_path=temp_file_path,
            chunk_size=optimal_config['chunk_size'],
            overlap=optimal_config['overlap'],
            output_format='json',
            max_pages=None,
            max_chunks=optimal_config['max_chunks'],
            ocr_metadata=ocr_metadata  # FIX 11 ALT A: Pass pre-computed OCR
        )
```

**Testing Checkpoint**:
- Verify metadata extraction logic
- Verify parameter passing to `process_file_in_sections`

---

#### Task 1.3: Modify `memvid_sections.py` (30 min)

**File**: `D:\railway\memvid\memvidBeta\encoder_app\memvid_sections.py`
**Location**: Lines 109-260 (function `read_file_in_sections`)

**Changes**:

**STEP 1**: Update function signature (MODIFY line 109):

```python
# REPLACE:
def read_file_in_sections(file_path, section_size=50000, max_pages=None):

# WITH:
def read_file_in_sections(file_path, section_size=50000, max_pages=None, ocr_metadata=None):
    """
    Legge un file dividendolo in sezioni gestibili.
    Restituisce una lista di sezioni di testo.

    Args:
        file_path: Percorso del file
        section_size: Dimensione massima di ogni sezione in caratteri
        max_pages: Numero massimo di pagine da elaborare (solo per PDF)
        ocr_metadata: Optional dict with pre-computed OCR texts (FIX 11 ALT A)
                      Format: {'ocr_texts': ['text1', 'text2', ...], 'page_count': N}

    Returns:
        List[str]: Lista di sezioni di testo
    """
```

**STEP 2**: Add OCR metadata handling for PDFs (INSERT AFTER line 125, BEFORE line 126):

```python
    # PDF - elaborazione speciale
    if file_extension == ".pdf":
        try:
            import PyPDF2

            # ============================================================================
            # FIX 11 ALT A: Check for pre-computed OCR metadata
            # ============================================================================
            use_precomputed_ocr = (
                ocr_metadata is not None and
                ocr_metadata.get('ocr_texts') is not None and
                len(ocr_metadata.get('ocr_texts', [])) > 0
            )

            if use_precomputed_ocr:
                # Use OCR texts from API instead of PyPDF2 extraction
                ocr_texts = ocr_metadata['ocr_texts']
                page_count = len(ocr_texts)

                update_activity(f"Using pre-computed OCR metadata for {page_count} pages")
                print(f"[FIX-11-ALT-A] 📄 Using pre-computed OCR for {page_count} pages")
                print(f"[FIX-11-ALT-A] Total OCR text: {sum(len(t) for t in ocr_texts)} characters")

                sections = []
                current_section = ""
                current_size = 0

                for i, ocr_text in enumerate(ocr_texts):
                    page_num = i + 1
                    update_activity(f"Processing page {page_num}/{page_count} from OCR metadata")

                    if ocr_text.strip():
                        page_content = f"\n## Pagina {page_num}\n\n{ocr_text}\n\n"

                        # Se aggiungendo questa pagina superiamo la dimensione massima,
                        # avviamo una nuova sezione
                        if current_size + len(page_content) > section_size and current_size > 0:
                            sections.append(current_section)
                            current_section = page_content
                            current_size = len(page_content)
                            print(f"[FIX-11-ALT-A] New section started at page {page_num}")
                        else:
                            current_section += page_content
                            current_size += len(page_content)
                    else:
                        # Empty OCR text for this page
                        print(f"[FIX-11-ALT-A] ⚠️ Page {page_num} has no OCR text, skipping")

                    # Forza una nuova sezione ogni 15 pagine per sicurezza
                    if (page_num) % 15 == 0 and current_section:
                        update_activity(f"Forcing new section after page {page_num}")
                        sections.append(current_section)
                        current_section = ""
                        current_size = 0
                        print(f"[FIX-11-ALT-A] Section forced after page {page_num}")
                        gc.collect()

                # Aggiungi l'ultima sezione
                if current_section:
                    update_activity("Adding final section")
                    sections.append(current_section)

                print(f"[FIX-11-ALT-A] ✅ File divided into {len(sections)} sections using OCR metadata")
                return sections

            else:
                # FALLBACK: No OCR metadata, use normal PyPDF2 extraction
                print("[FIX-11-ALT-A] No OCR metadata found, using PyPDF2 extraction")
                # Continue with existing PyPDF2 code below...
```

**STEP 3**: The existing PyPDF2 code (lines 128-256) remains UNCHANGED as fallback.

**Testing Checkpoint**:
- Verify function signature updated
- Verify OCR metadata branch logic
- Verify fallback to PyPDF2 works if no metadata

---

### Phase 2: Local Testing (1 hour)

#### Test 2.1: Unit Test - OCR Extraction (15 min)

**Test Case**: Upload 3 images via `/api/documents/upload-batch`

**Expected Results**:
- ✅ OCR applied to all 3 images
- ✅ `ocr_texts` array in document metadata
- ✅ Logs show `[BATCH-OCR] ✅ Page 1: X chars extracted`
- ✅ Document created with `has_ocr_metadata: true`

**Verification**:
```bash
# Check database
python -c "
from core.database import SessionLocal, Document
db = SessionLocal()
doc = db.query(Document).order_by(Document.created_at.desc()).first()
print('OCR metadata:', doc.doc_metadata.get('has_ocr_metadata'))
print('OCR texts count:', len(doc.doc_metadata.get('ocr_texts', [])))
print('OCR summary:', doc.doc_metadata.get('ocr_summary'))
"
```

---

#### Test 2.2: Integration Test - Worker Processing (20 min)

**Test Case**: Trigger Celery worker to process PDF with OCR metadata

**Setup**:
1. Ensure Redis running: `docker-compose -f docker-compose.dev.yml up redis -d`
2. Start Celery worker: `celery -A celery_config worker --loglevel=info`
3. Upload 3 images via dashboard

**Expected Results**:
- ✅ Worker logs show `[FIX-11-ALT-A] Found pre-computed OCR metadata for 3 pages`
- ✅ Encoder uses OCR texts (not PyPDF2)
- ✅ Document status becomes "ready"
- ✅ Metadata JSON created with chunks from OCR text

**Verification**:
```bash
# Check worker logs
tail -f celery-worker.log | grep "FIX-11-ALT-A"

# Expected output:
# [FIX-11-ALT-A] Found pre-computed OCR metadata for 3 pages
# [FIX-11-ALT-A] Total OCR text: 1234 characters
# [FIX-11-ALT-A] 📄 Using pre-computed OCR for 3 pages
# [FIX-11-ALT-A] ✅ File divided into N sections using OCR metadata
```

---

#### Test 2.3: Query Test - RAG Pipeline (15 min)

**Test Case**: Query processed document

**Setup**:
1. Wait for document status = "ready"
2. Use dashboard to query: "Riassumi il contenuto"

**Expected Results**:
- ✅ Query returns relevant answer
- ✅ Sources include chunks from OCR text
- ✅ No errors in query processing

---

#### Test 2.4: Fallback Test - Text-Based PDF (10 min)

**Test Case**: Upload normal text-based PDF (not from camera)

**Expected Results**:
- ✅ No OCR metadata in document
- ✅ Worker uses PyPDF2 extraction (fallback)
- ✅ Document processes successfully
- ✅ Logs show `[FIX-11-ALT-A] No OCR metadata found, using PyPDF2 extraction`

**Verification**: Ensure backwards compatibility with existing text PDFs.

---

### Phase 3: Railway Staging Deployment (30 min)

#### Pre-Deployment Checklist

- ✅ All local tests passing
- ✅ Git committed and tagged: `v1.0.0-fix-11-alt-a-staging`
- ✅ Google Cloud Vision API quota checked (>1000 calls available)
- ✅ Railway staging environment configured

---

#### Staging Deployment Steps

**Step 1**: Create staging branch (5 min)

```bash
git checkout -b fix-11-alt-a-staging
git add api_server.py tasks.py memvidBeta/encoder_app/memvid_sections.py
git commit -m "feat(FIX-11-ALT-A): Pre-compute OCR in API before PDF encoding

- Apply Google Cloud Vision OCR to batch images BEFORE PDF creation
- Pass OCR texts via document metadata to encoder
- Encoder uses OCR metadata if available, falls back to PyPDF2
- Resolves 'O characters extracted' error for image-based PDFs
- Zero new dependencies, pure Python stack
- Performance: Enables parallel OCR in future (2x faster potential)

Related: #FIX-11, image-based PDF processing
"
git push origin fix-11-alt-a-staging
```

**Step 2**: Deploy to Railway staging (10 min)

```bash
# Link to Railway staging environment
railway environment staging

# Deploy
railway up

# Monitor deployment
railway logs --tail --service web
railway logs --tail --service worker
```

**Step 3**: Health check (5 min)

```bash
# Check API health
curl https://staging.socrate.ai/api/health

# Check worker health (upload test document)
# Use Railway dashboard to trigger batch upload
```

---

#### Staging Tests

**Test 3.1**: Real mobile photos (10 min)

1. Use smartphone to capture 3 photos (3-5MB each)
2. Upload via staging dashboard
3. Monitor worker logs in Railway dashboard
4. Verify document becomes "ready"
5. Test query functionality

**Expected Worker Logs**:
```
[BATCH-OCR] Applying OCR to 3 images...
[BATCH-OCR] ✅ Page 1: 234 chars, 45 words extracted
[BATCH-OCR] ✅ Page 2: 189 chars, 38 words extracted
[BATCH-OCR] ✅ Page 3: 276 chars, 52 words extracted
[BATCH-OCR] Summary: 3/3 pages successfully OCR'd
[FIX-11-ALT-A] Found pre-computed OCR metadata for 3 pages
[FIX-11-ALT-A] ✅ File divided into 1 sections using OCR metadata
```

---

### Phase 4: Production Deployment (30 min)

#### Pre-Production Checklist

- ✅ Staging tests successful (3+ test batches)
- ✅ No errors in Railway logs
- ✅ Google Cloud Vision API working
- ✅ Query functionality verified
- ✅ Performance acceptable (<20s per batch)

---

#### Production Deployment Steps

**Step 1**: Merge to main (5 min)

```bash
git checkout main
git merge fix-11-alt-a-staging
git tag v1.0.0-fix-11-alt-a
git push origin main --tags
```

**Step 2**: Railway auto-deploy (10 min)

Railway automatically deploys when main branch updated.

Monitor:
```bash
railway environment production
railway logs --tail --service web
railway logs --tail --service worker
```

**Step 3**: Smoke test (5 min)

1. Upload 3 test photos via production dashboard
2. Verify processing completes
3. Test query
4. Check Google Cloud Vision dashboard for API calls

**Step 4**: User notification (10 min)

Send message to test users:
```
🎉 Aggiornamento completato!

Problema risolto: batch upload di foto dalla camera ora funziona correttamente.

✅ Le tue foto verranno processate con OCR automatico
✅ Puoi caricare fino a 3-5 foto insieme
✅ Tempo di elaborazione: ~15-20 secondi

Grazie per la pazienza!
```

---

## Monitoring Plan (First 24 Hours)

### Metrics to Track

**Success Rate**:
```sql
-- Query database for success rate
SELECT
  COUNT(*) FILTER (WHERE status = 'ready') * 100.0 / COUNT(*) as success_rate
FROM documents
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND doc_metadata->>'has_ocr_metadata' = 'true';
```

**Processing Time**:
```sql
-- Average processing time
SELECT AVG(EXTRACT(EPOCH FROM (processing_completed_at - created_at))) as avg_seconds
FROM documents
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND status = 'ready'
  AND doc_metadata->>'has_ocr_metadata' = 'true';
```

**OCR Failure Rate**:
```bash
# Check worker logs
railway logs --service worker | grep "BATCH-OCR.*failed"
```

---

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Success rate | <95% | <90% | Investigate worker logs |
| Processing time | >30s | >60s | Check OCR API latency |
| Memory usage | >75% | >85% | Scale workers |
| OCR failures | >5% | >10% | Check image quality, API quota |

---

### Monitoring Commands

**Check recent uploads**:
```bash
railway run python -c "
from core.database import SessionLocal, Document
from sqlalchemy import desc
db = SessionLocal()
recent = db.query(Document).filter(
    Document.doc_metadata['has_ocr_metadata'].astext == 'true'
).order_by(desc(Document.created_at)).limit(10).all()

for doc in recent:
    print(f'{doc.filename}: {doc.status} - OCR pages: {len(doc.doc_metadata.get(\"ocr_texts\", []))}')
"
```

**Check Google Cloud Vision usage**:
- Go to: https://console.cloud.google.com/apis/api/vision.googleapis.com/quotas
- Verify: "Text Detection" quota not exceeded
- Check: Cost estimate for current month

---

## Rollback Procedure

### When to Rollback

**Immediate rollback if**:
1. Success rate drops below 90% within first hour
2. Worker crashes or OOM errors
3. Google Cloud Vision API quota exceeded
4. Processing time consistently >60s
5. Critical bugs reported by users

---

### Rollback Steps (5 minutes)

**Step 1**: Revert to previous version

```bash
# Find previous good commit
git log --oneline -5

# Revert to previous version (before FIX-11-ALT-A merge)
git revert HEAD --no-edit
git push origin main
```

**Step 2**: Railway auto-deploys rollback

Monitor deployment:
```bash
railway logs --tail --service web
railway logs --tail --service worker
```

**Step 3**: Verify rollback successful

1. Check API health: `/api/health`
2. Test single photo upload (should work - uses old OCR task)
3. Test batch upload (will fail with "0 characters" again)

**Step 4**: Communicate to users

```
⚠️ Rollback effettuato per problemi tecnici.

Temporaneamente: usare upload singolo per ogni foto (non batch).

Stiamo lavorando alla soluzione definitiva.
```

---

### Post-Rollback Analysis

**Data to collect**:
1. Railway worker logs (last 1 hour before rollback)
2. Google Cloud Vision API error logs
3. Failed document IDs and metadata
4. User error reports

**Root cause investigation**:
- Worker memory usage charts
- API latency graphs
- Error rate by time of day
- Specific image characteristics that failed

---

## Post-Deployment Tasks

### Week 1: Validation

- ✅ Monitor success rate daily
- ✅ Collect user feedback
- ✅ Analyze Google Cloud Vision costs
- ✅ Review worker performance metrics

### Week 2-4: Optimization

**If all stable, consider optimizations**:

1. **Parallel OCR** (performance improvement):
   - Use ThreadPoolExecutor for 3 simultaneous OCR calls
   - Expected: 2x faster processing

2. **OCR Caching** (cost reduction):
   - Store OCR results in Redis by image hash
   - Avoid re-OCR on duplicate uploads

3. **Quality Checks** (better UX):
   - Detect low-confidence OCR
   - Prompt user to retake blurry photos

---

## Success Criteria

### Definition of Done

- ✅ Image-based PDFs (3 photos) process without "0 characters" error
- ✅ Processing time <20 seconds per batch
- ✅ Success rate >95% for 7 consecutive days
- ✅ Query functionality works on batch-uploaded PDFs
- ✅ Zero worker crashes for 7 consecutive days
- ✅ Google Cloud Vision cost <$5/week
- ✅ No user complaints about batch upload failures

### Long-Term Success (3 months)

- ✅ Architecture proven stable
- ✅ OCR metadata pattern reused for other features
- ✅ Parallel OCR optimization implemented
- ✅ Total OCR cost <$15/month
- ✅ No technical debt requiring refactoring

---

## Appendix: Troubleshooting Guide

### Problem: OCR returns empty text

**Symptoms**: `[BATCH-OCR] ⚠️ Page X: OCR failed`

**Possible Causes**:
1. Google Cloud Vision API key invalid
2. Network connectivity issue
3. Image quality too low (blurry, dark)
4. API quota exceeded

**Debug Steps**:
```bash
# Check API credentials
railway run python -c "
import os
print('GOOGLE_CLOUD_VISION_API_KEY:', os.getenv('GOOGLE_CLOUD_VISION_API_KEY')[:20] + '...')
print('GOOGLE_APPLICATION_CREDENTIALS_JSON:', 'SET' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') else 'NOT SET')
"

# Test OCR directly
railway run python -c "
from core.ocr_processor import extract_text_from_image
import requests

# Download test image
img_url = 'https://example.com/test-image.jpg'
img_bytes = requests.get(img_url).content

result = extract_text_from_image(img_bytes, 'test.jpg')
print('Success:', result['success'])
print('Text length:', len(result.get('text', '')))
print('Error:', result.get('error'))
"
```

---

### Problem: Worker OOM (out of memory)

**Symptoms**: Worker crashes during batch processing

**Possible Causes**:
1. OCR + PDF creation exceeds memory limit
2. Too many concurrent batch uploads

**Solution**:
```bash
# Scale worker to larger instance
railway up --service worker --replicas 2

# Or increase memory limit in Railway dashboard
# Settings > Resources > Memory Limit: 1GB → 2GB
```

---

### Problem: Processing takes >60 seconds

**Symptoms**: Documents stuck in "processing" for long time

**Debug Steps**:
```bash
# Check Celery task queue length
railway run python -c "
from celery_config import celery_app
inspect = celery_app.control.inspect()
print('Active tasks:', inspect.active())
print('Reserved tasks:', inspect.reserved())
"

# Check Google Cloud Vision API latency
# Monitor in Google Cloud Console > APIs > Vision API > Metrics
```

**Solution**:
- Add more Celery workers: `railway up --service worker --replicas 3`
- Optimize OCR (implement parallel processing)

---

### Problem: Metadata too large for JSONB

**Symptoms**: Database error when saving document

**Debug Steps**:
```bash
# Check metadata size
railway run python -c "
from core.database import SessionLocal, Document
import json

db = SessionLocal()
doc = db.query(Document).order_by(Document.created_at.desc()).first()

metadata_json = json.dumps(doc.doc_metadata)
print('Metadata size:', len(metadata_json), 'bytes')
print('OCR texts:', len(doc.doc_metadata.get('ocr_texts', [])))
print('Total OCR chars:', sum(len(t) for t in doc.doc_metadata.get('ocr_texts', [])))
"
```

**Solution**:
If metadata >1MB, store OCR texts in R2 instead:
```python
# In api_server.py, store OCR in R2
ocr_r2_key = f"users/{user_id}/documents/{doc_id}/ocr_texts.json"
upload_file(json.dumps(ocr_texts).encode(), ocr_r2_key, 'application/json')

# In metadata, reference R2 key instead
doc_metadata = {
    'ocr_r2_key': ocr_r2_key,  # Reference to R2 object
    'has_ocr_metadata': True
}
```

---

## Contact & Support

**Implementation Lead**: Claude Code Agent
**Timeline**: 3.5 hours to production
**Status**: Ready for implementation

**Questions?** Check:
1. FIX_11_STRATEGIC_ASSESSMENT.md (strategic context)
2. CAMERA_BATCH_ISSUE_ANALYSIS.md (historical context)
3. Railway logs: `railway logs --tail --service worker`
