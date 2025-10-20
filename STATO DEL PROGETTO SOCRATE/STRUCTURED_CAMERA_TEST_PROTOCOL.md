# Structured Camera Batch Upload Test Protocol

**Created**: 20 Ottobre 2025, ore 03:45
**Purpose**: Systematic diagnosis of camera batch upload issues
**Agent Recommendations**: Backend Master Analyst + General-Purpose Agent

---

## Prerequisites

1. ✅ Eruda debug console enabled on dashboard
2. ✅ Debug utilities deployed (dashboard.js line 823-964)
3. ✅ Chrome DevTools Network tab open
4. ✅ Clear browser cache (CTRL+SHIFT+DEL → Cached images and files → Last hour)

---

## Test Scenario 1: Basic Camera Capture Flow

### Objective
Verify that camera capture correctly adds photos to `capturedImages` array and shows preview modal.

### Steps

1. **Reset State**
   ```javascript
   // In Eruda Console:
   window.resetCameraState()
   ```
   Expected output: `✅ Camera state reset. Cleared 0 images.`

2. **Verify Initial State**
   ```javascript
   window.debugCameraState()
   ```
   Expected output:
   ```json
   {
     "capturedImagesCount": 0,
     "capturedImagesDetails": [],
     "cameraInputElement": {
       "exists": true,
       "value": "",
       "filesLength": 0
     },
     "modalElement": {
       "exists": true,
       "display": "none",
       "hasActiveClass": false
     }
   }
   ```

3. **Click Camera Button**
   - Click "📷 Scatta Foto" button
   - Take 1 photo with device camera
   - Wait for camera app to return to browser

4. **Verify State After Photo 1**
   ```javascript
   window.debugCameraState()
   ```
   Expected output:
   ```json
   {
     "capturedImagesCount": 1,
     "capturedImagesDetails": [
       {
         "index": 0,
         "fileName": "image.jpg",
         "fileSize": 2000000,  // ~2MB
         "fileType": "image/jpeg",
         "dataUrlLength": 2700000  // base64 encoded
       }
     ],
     "cameraInputElement": {
       "value": "",  // MUST be empty (reset after capture)
       "filesLength": 0
     },
     "modalElement": {
       "display": "flex",  // MUST be visible
       "hasActiveClass": true
     }
   }
   ```

5. **Visual Verification**
   - [ ] Modal is visible with "📸 Foto Acquisite (1)" title
   - [ ] Preview shows 1 thumbnail image
   - [ ] Thumbnail matches the photo you took
   - [ ] "Carica Tutto (1)" button is visible

6. **Check Console Logs**
   - Filter Eruda logs for `[CAMERA]` tag
   - Expected sequence:
     ```
     [CAMERA] handleCameraCapture called with file: image.jpg
     [CAMERA] FileReader onload - image loaded
     [CAMERA] Image added to batch. Total images: 1
     [CAMERA] Camera input reset AFTER image loaded
     [CAMERA] Calling showBatchPreview()...
     [BATCH] showBatchPreview() called. Total images: 1
     [BATCH] Modal element found
     [BATCH] Generating preview HTML for 1 images
     [BATCH] Setting modal.style.display = flex...
     [BATCH] Modal should now be visible
     ```

7. **Check Network Tab**
   - Open Chrome DevTools → Network
   - Filter by "Fetch/XHR"
   - Expected: **NO requests** to `/api/documents/upload` or `/upload-batch`
   - Photos should stay in memory, not upload yet

---

## Test Scenario 2: Multi-Photo Batch Capture

### Objective
Verify that multiple photos accumulate in array and all show in preview.

### Steps

1. **Start from Scenario 1 completion** (1 photo captured, modal visible)

2. **Click "Aggiungi Foto" Button**
   - Click "📷 Aggiungi Foto" in modal
   - Take photo 2
   - Wait for camera app to return

3. **Verify State After Photo 2**
   ```javascript
   window.debugCameraState()
   ```
   Expected:
   ```json
   {
     "capturedImagesCount": 2,
     "capturedImagesDetails": [
       { "index": 0, "fileName": "image.jpg", ... },
       { "index": 1, "fileName": "image.jpg", ... }
     ],
     "modalElement": {
       "display": "flex",
       "hasActiveClass": true
     }
   }
   ```

4. **Visual Verification**
   - [ ] Modal title shows "📸 Foto Acquisite (2)"
   - [ ] Preview shows 2 thumbnails side-by-side
   - [ ] Both thumbnails match the photos taken
   - [ ] Button shows "Carica Tutto (2)"

5. **Repeat for Photo 3**
   - Click "📷 Aggiungi Foto" again
   - Take photo 3
   - Verify `capturedImagesCount: 3`
   - Visual check: 3 thumbnails visible

---

## Test Scenario 3: Batch Upload Execution

### Objective
Verify that "Carica Tutto" sends ONE request to `/upload-batch` with ALL photos merged.

### Steps

1. **Start from Scenario 2 completion** (3 photos captured)

2. **Monitor Network Tab**
   - Clear DevTools Network log
   - Keep Network tab visible

3. **Click "Carica Tutto (3)" Button**
   - Enter document name: "test-batch-upload"
   - Click "✅ Carica Tutto (3)"

4. **Verify Network Request**
   - [ ] Exactly **1 request** to `/api/documents/upload-batch`
   - [ ] **0 requests** to `/api/documents/upload` (single upload)
   - [ ] Request method: `POST`
   - [ ] Content-Type: `multipart/form-data`
   - [ ] FormData contains:
     - `files` (3 items)
     - `document_name` = "test-batch-upload"
     - `merge_images` = "true"

5. **Verify Backend Response**
   - [ ] Status: `200 OK` or `201 Created`
   - [ ] Response JSON contains:
     ```json
     {
       "success": true,
       "document_id": "uuid-here",
       "duplicate": false  // or true if reupload
     }
     ```

6. **Verify Document Creation**
   - Wait 2-3 seconds for dashboard refresh
   - Check documents grid for new document:
     - [ ] Document name: "test-batch-upload.pdf"
     - [ ] Status: "In elaborazione" → "Pronto"
     - [ ] File size: ~5-8 MB (3 photos merged)
     - [ ] Created date: today

7. **Download and Verify PDF**
   - Once status is "Pronto", click "🛠️ Strumenti"
   - Download the PDF
   - Open PDF with viewer
   - [ ] PDF has exactly 3 pages
   - [ ] Each page shows one of the 3 photos
   - [ ] Photo order matches capture order (1st photo = page 1, etc.)

---

## Test Scenario 4: Preview Alternating Issue Diagnosis

### Objective
Diagnose why user reports "first photo doesn't appear, second appears, third doesn't" pattern.

### Steps

1. **Reset State**
   ```javascript
   window.resetCameraState()
   ```

2. **Systematic Photo Capture**
   - Take photo 1, immediately run `window.debugCameraState()` → record result
   - Click "Aggiungi Foto", take photo 2, run `window.debugCameraState()` → record result
   - Click "Aggiungi Foto", take photo 3, run `window.debugCameraState()` → record result
   - Click "Aggiungi Foto", take photo 4, run `window.debugCameraState()` → record result

3. **Data to Collect for Each Photo**
   ```javascript
   // After EACH photo, record:
   {
     photoNumber: 1,  // 2, 3, 4...
     capturedImagesCount: X,  // Should increment 1→2→3→4
     modalVisible: true/false,
     thumbnailsVisible: X,  // How many thumbnails rendered
     timestamp: "HH:MM:SS"
   }
   ```

4. **Pattern Analysis**
   - If `capturedImagesCount` increments correctly BUT thumbnails don't appear:
     → **Frontend rendering issue** in `showBatchPreview()` line 570-660

   - If `capturedImagesCount` stays same or skips numbers (1→3→5):
     → **Event listener race condition** - camera-input being reset prematurely

   - If modal doesn't appear for some photos:
     → **CSS/display issue** - check `modal.style.display` and `hasActiveClass`

---

## Test Scenario 5: Idempotency Check

### Objective
Verify backend prevents duplicate uploads when user clicks "Carica" multiple times rapidly.

### Steps

1. **Capture 2 photos**
   - Take photo 1, click "Aggiungi Foto", take photo 2
   - Modal shows 2 photos

2. **Rapid Double-Click Upload**
   - Click "Carica Tutto (2)" button **TWICE RAPIDLY** (within 500ms)

3. **Verify Network Behavior**
   - DevTools Network tab should show:
     - [ ] 2 requests to `/upload-batch` (both clicked)
     - [ ] First request: `200 OK` with `duplicate: false`
     - [ ] Second request: `200 OK` with `duplicate: true`

4. **Verify Database**
   - Dashboard should show **ONLY 1 NEW DOCUMENT**
   - Document ID from both responses should be IDENTICAL

5. **Verify Backend Logs**
   - Open Railway logs:
     ```bash
     railway logs --service web | grep "Duplicate upload detected"
     ```
   - Expected: One log entry with `[WARN] Duplicate upload detected for user XXX`

---

## Test Scenario 6: Memory Efficiency Test (Large Photos)

### Objective
Verify backend can handle 5-6 high-resolution photos without OOM error.

### Steps

1. **Capture 5-6 High-Res Photos**
   - Use camera at highest resolution setting
   - Take 5 photos (or 6 if device allows)
   - Each photo should be 3-5 MB

2. **Monitor Upload**
   - Click "Carica Tutto (5)"
   - Watch progress indicator

3. **Expected Behavior**
   - [ ] Upload progress bar reaches 100%
   - [ ] Document status: "In elaborazione" → "Pronto" (NOT "Errore")
   - [ ] PDF created successfully
   - [ ] PDF size: 15-30 MB (optimized from original ~20-30MB total)

4. **Verify Backend Logs**
   - No `MemoryError`, `OOM`, or `SIGKILL` messages
   - Logs should show:
     ```
     Created PDF: 5 pages, XXXXX bytes
     Resized images to max 2000px
     Using temporary disk storage
     ```

---

## Expected Results Summary

| Test Scenario | Pass Criteria |
|--------------|---------------|
| 1. Basic Capture | Modal appears, 1 thumbnail visible, `capturedImagesCount: 1` |
| 2. Multi-Photo | All thumbnails visible, count increments correctly |
| 3. Batch Upload | 1 request to `/upload-batch`, PDF with N pages created |
| 4. Preview Alternating | All photos appear in preview, no skipping pattern |
| 5. Idempotency | Duplicate detected, only 1 document created |
| 6. Large Photos | No OOM error, PDF created with optimized size |

---

## Data Collection Template

Copy this to Eruda console after each test:

```javascript
const testResults = {
  scenario: "Scenario 1: Basic Capture",
  timestamp: new Date().toISOString(),
  state: window.debugCameraState(),
  visualChecks: {
    modalVisible: true/false,
    thumbnailsCount: X,
    thumbnailsMatchPhotos: true/false
  },
  networkChecks: {
    requestCount: X,
    requestEndpoint: "/upload-batch",
    responseStatus: 200,
    documentCreated: true/false
  },
  notes: "Any observations..."
};

console.log(JSON.stringify(testResults, null, 2));
```

---

## Troubleshooting Guide

### Issue: Modal Doesn't Appear
**Diagnosis Steps**:
1. Run `window.debugCameraState()` → check `modalElement.display`
2. If `display: "none"` → check console for errors in `showBatchPreview()`
3. Check CSS: `.modal.active { display: flex !important; }`

**Possible Causes**:
- CSS not loaded (cache issue)
- JavaScript error preventing modal show
- Event listener not firing

### Issue: Photos Appear Alternately (1st no, 2nd yes, 3rd no)
**Diagnosis Steps**:
1. Run `window.debugCameraState()` after each photo
2. Check `capturedImagesCount` increments (1→2→3→4)
3. Check `capturedImagesDetails` array length

**Possible Causes**:
- FileReader race condition (FIXED in commit f1c4274)
- Event listener firing twice (FIXED in commit 612a3d5)
- CSS `:nth-child` hiding odd/even thumbnails (unlikely but check)

### Issue: Multiple Documents Created (Duplicates)
**Diagnosis Steps**:
1. Check Network tab for multiple `/upload-batch` requests
2. Check backend logs for idempotency warnings
3. Verify `content_hash` in database metadata

**Possible Causes**:
- Frontend not preventing double-click (check dashboard.html)
- Backend idempotency check failing (check SQLAlchemy query)
- Redis cache miss causing duplicate detection failure

---

## Logs to Collect

**Frontend (Eruda Console)**:
- Filter for `[CAMERA]`, `[BATCH]`, `[FILE-INPUT]` tags
- Copy all logs during test

**Backend (Railway)**:
```bash
# Web service
railway logs --service web | grep -E "(Batch upload|Duplicate|upload-batch)" | tail -50

# Celery worker
railway logs --service celery-worker | grep -E "(Processing|PDF created)" | tail -30
```

---

## Success Criteria

All 6 test scenarios pass with:
- ✅ No console errors
- ✅ All photos appear in preview
- ✅ Single request to `/upload-batch`
- ✅ PDF created with all pages
- ✅ No duplicate documents
- ✅ No OOM errors for large batches

---

**Last Updated**: 20 Ottobre 2025, ore 03:45
**Next Review**: After user completes testing and provides data
