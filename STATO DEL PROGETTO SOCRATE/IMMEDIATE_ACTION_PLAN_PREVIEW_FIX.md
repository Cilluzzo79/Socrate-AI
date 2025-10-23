# Immediate Action Plan: Preview Issue Diagnosis

**Date**: 20 Ottobre 2025, ore 04:30
**Priority**: HIGH
**Estimated Time**: 2-4 hours
**Status**: READY TO EXECUTE

---

## Problem Statement

After 6 fixes, user still reports:
> "Preview foto alternante - prima foto non appare, altre appaiono intermittentemente"

**Root Cause**: Unknown - needs data-driven diagnosis

**Hypothesis**: Modal DOM lifecycle issue (innerHTML replacement, image load timing, or data URL handling)

---

## Step 1: Deploy Debug Utilities (30 minutes)

### 1A. Add Preview Image Diagnostics

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Location**: After line 663 in `showBatchPreview()` function

**Add this code**:

```javascript
/**
 * Debug utility for diagnosing preview image issues
 * EXPOSED TO GLOBAL SCOPE for Eruda console access
 */
window.debugPreviewImages = function() {
    const modal = document.getElementById('image-preview-modal');
    const images = modal.querySelectorAll('img[src^="data:image"]'); // Only preview images

    const report = {
        timestamp: new Date().toISOString(),
        modal_visible: modal.style.display === 'flex',
        modal_has_active_class: modal.classList.contains('active'),
        capturedImages_count: capturedImages.length,
        rendered_images_count: images.length,
        capturedImages_details: capturedImages.map((img, idx) => ({
            index: idx,
            file_name: img.file.name,
            file_size: img.file.size,
            file_type: img.file.type,
            dataUrl_length: img.dataUrl.length,
            dataUrl_prefix: img.dataUrl.substring(0, 50)
        })),
        rendered_images_details: Array.from(images).map((img, idx) => ({
            index: idx,
            src_length: img.src.length,
            src_prefix: img.src.substring(0, 50),
            complete: img.complete,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            loading_state: img.loading,
            display_style: img.style.display,
            visible_in_viewport: img.getBoundingClientRect().width > 0
        }))
    };

    console.log('[DEBUG] Preview Images Report:', report);
    console.table(report.rendered_images_details);

    // Check for mismatches
    if (report.capturedImages_count !== report.rendered_images_count) {
        console.error('[DEBUG] MISMATCH: Captured images count !== Rendered images count', {
            captured: report.capturedImages_count,
            rendered: report.rendered_images_count
        });
    }

    // Check for incomplete images
    const incompleteImages = report.rendered_images_details.filter(img => !img.complete || img.naturalWidth === 0);
    if (incompleteImages.length > 0) {
        console.error('[DEBUG] INCOMPLETE IMAGES DETECTED:', incompleteImages);
    }

    return report;
};

console.log('[BATCH] Debug utility registered: window.debugPreviewImages()');
```

### 1B. Add Image Load Event Tracking

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Location**: Replace lines 582-594 (previewsHTML generation)

**Replace with**:

```javascript
// Generate preview HTML for all images with load tracking
console.log('[BATCH] Generating preview HTML for', capturedImages.length, 'images');
const previewsHTML = capturedImages.map((img, index) => `
    <div style="position: relative; display: inline-block; margin: 0.5rem;" data-image-index="${index}">
        <img src="${img.dataUrl}"
             data-image-index="${index}"
             onload="console.log('[PREVIEW-IMG-${index}] ✅ Loaded successfully', {complete: this.complete, dimensions: this.naturalWidth + 'x' + this.naturalHeight})"
             onerror="console.error('[PREVIEW-IMG-${index}] ❌ Failed to load', {src_length: this.src.length})"
             style="max-width: 150px; max-height: 150px; border-radius: var(--radius-md); border: 2px solid var(--color-border-primary);">
        <button onclick="removeImage(${index})"
                style="position: absolute; top: -8px; right: -8px; background: var(--color-error); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 14px; line-height: 1;">
            ×
        </button>
        <div style="text-align: center; font-size: 0.75rem; color: var(--color-text-muted); margin-top: 0.25rem;">
            Foto ${index + 1}
        </div>
    </div>
`).join('');
```

### 1C. Update Version String

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Line**: 4

**Change from**:
```javascript
 * VERSION: FIX-DUPLICATE-UPLOAD-19OCT2025
```

**Change to**:
```javascript
 * VERSION: DEBUG-PREVIEW-DIAGNOSTICS-20OCT2025
```

**Line**: 7

**Change from**:
```javascript
console.log('[DASHBOARD.JS] VERSION: FIX-DUPLICATE-UPLOAD-19OCT2025');
```

**Change to**:
```javascript
console.log('[DASHBOARD.JS] VERSION: DEBUG-PREVIEW-DIAGNOSTICS-20OCT2025');
```

---

## Step 2: Deploy to Railway (5 minutes)

```bash
cd D:\railway\memvid
git add static/js/dashboard.js
git commit -m "feat: add preview image diagnostics for debugging alternating display issue

- Add window.debugPreviewImages() utility for Eruda console
- Add onload/onerror handlers to preview <img> elements
- Track image load states, dimensions, and visibility
- Version bump: DEBUG-PREVIEW-DIAGNOSTICS-20OCT2025"

git push
```

**Wait for Railway deployment**: ~2-3 minutes

---

## Step 3: User Test Protocol (15 minutes)

Send this message to the user:

```
Ciao! Ho aggiunto strumenti di diagnostica per capire il problema delle foto alternanti.

Per favore segui questi passi ESATTAMENTE:

1. Apri la dashboard e apri Eruda console (icona in basso a destra)
2. Vai sulla tab "Console" in Eruda
3. Scatta la PRIMA foto con il pulsante camera
4. Guarda se la foto appare nel modal
5. Vai su Eruda console e cerca i log che iniziano con [PREVIEW-IMG-0]
6. Screenshot della console
7. Screenshot del modal con la prima foto

8. Scatta la SECONDA foto
9. Guarda se ENTRAMBE le foto appaiono nel modal
10. Vai su Eruda console
11. Screenshot della console
12. Screenshot del modal con le due foto

13. Scatta la TERZA foto
14. Guarda se TUTTE E TRE le foto appaiono nel modal
15. Vai su Eruda console e digita: debugPreviewImages()
16. Screenshot della console (con la tabella che appare)
17. Screenshot del modal con le tre foto

Inviami tutti i 6 screenshot numerati.

IMPORTANTE: Non chiudere il modal, non ricaricare la pagina fino a dopo aver fatto tutti gli screenshot.
```

---

## Step 4: Data Analysis (30-60 minutes)

When you receive screenshots, analyze:

### 4A. Check Image Load Events

Look for `[PREVIEW-IMG-0]`, `[PREVIEW-IMG-1]`, `[PREVIEW-IMG-2]` logs:

**Scenario A - Images Load Successfully**:
```
[PREVIEW-IMG-0] ✅ Loaded successfully {complete: true, dimensions: '1024x768'}
[PREVIEW-IMG-1] ✅ Loaded successfully {complete: true, dimensions: '1024x768'}
[PREVIEW-IMG-2] ✅ Loaded successfully {complete: true, dimensions: '1024x768'}
```
→ **Conclusion**: Images load fine, issue is CSS/visibility related

**Scenario B - Images Fail to Load**:
```
[PREVIEW-IMG-0] ❌ Failed to load {src_length: 50000}
```
→ **Conclusion**: Data URL issue, need to switch to Blob URLs

**Scenario C - Images Load but Dimensions Are 0**:
```
[PREVIEW-IMG-1] ✅ Loaded successfully {complete: true, dimensions: '0x0'}
```
→ **Conclusion**: Browser bug with data URLs, need Blob URLs

### 4B. Check debugPreviewImages() Output

Look at the table in console:

**Key columns to check**:
- `complete`: Should be `true` for all images
- `naturalWidth`: Should be >0 (e.g., 1024, 2048)
- `visible_in_viewport`: Should be `true` for all images

**Mismatch Check**:
- `capturedImages_count` should equal `rendered_images_count`
- If not equal → DOM rendering issue

### 4C. Check Modal Screenshots

Compare what user SEES vs. what console says:

**Scenario A - Modal shows all images, console says all loaded**:
→ Bug resolved by debug code changes (timing issue)

**Scenario B - Modal shows 2/3 images, console says 3/3 loaded**:
→ CSS or z-index issue

**Scenario C - Modal shows 2/3 images, console says 2/3 loaded**:
→ Data URL corruption or FileReader issue

---

## Step 5: Targeted Fix (Based on Data)

### If Scenario: Images Load Fine (Complete=true, naturalWidth>0)

**Root Cause**: CSS or DOM rendering timing

**Fix**: Use `requestAnimationFrame` for DOM updates

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Line**: 596-644

**Wrap modal content update in RAF**:

```javascript
// Show modal first
console.log('[BATCH] Setting modal.style.display = flex...');
modal.style.display = 'flex';
modal.classList.add('active');

// Wait for next paint cycle, THEN update content
requestAnimationFrame(() => {
    requestAnimationFrame(() => {
        console.log('[BATCH] Updating modal content after RAF...');

        modal.querySelector('.modal-content').innerHTML = `
            <!-- Existing modal HTML -->
        `;

        console.log('[BATCH] Modal content updated');
    });
});
```

---

### If Scenario: Images Fail to Load (Complete=false or onerror fires)

**Root Cause**: Data URL size limits or mobile Safari bug

**Fix**: Switch to Blob URLs

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Function**: `handleCameraCapture()` and `showBatchPreview()`

**Changes**:

1. Store Blob URLs instead of data URLs:
```javascript
// In handleCameraCapture(), line 535-538
// REMOVE FileReader, use Blob URL directly
capturedImages.push({
    file: file,
    blobUrl: URL.createObjectURL(file) // Use Blob URL instead of data URL
});
```

2. Update preview generation:
```javascript
// In showBatchPreview(), line 584
<img src="${img.blobUrl}" <!-- Use blobUrl instead of dataUrl -->
```

3. Cleanup Blob URLs when modal closes:
```javascript
// In closePreviewModal(), line 700
window.closePreviewModal = function() {
    // Revoke Blob URLs to free memory
    capturedImages.forEach(img => {
        if (img.blobUrl) {
            URL.revokeObjectURL(img.blobUrl);
        }
    });

    const modal = document.getElementById('image-preview-modal');
    modal.classList.remove('active');
    modal.style.display = 'none';
    capturedImages = [];
}
```

---

### If Scenario: Mismatch in Count (captured ≠ rendered)

**Root Cause**: innerHTML replacement losing elements

**Fix**: Incremental DOM updates instead of full replacement

**File**: `D:\railway\memvid\static\js\dashboard.js`
**Function**: `showBatchPreview()`

**Replace innerHTML logic with**:

```javascript
function showBatchPreview() {
    console.log('[BATCH] showBatchPreview() called. Total images:', capturedImages.length);

    const modal = document.getElementById('image-preview-modal');
    if (!modal) {
        console.error('[BATCH] ERROR: image-preview-modal not found in DOM!');
        return;
    }

    let modalContent = modal.querySelector('.modal-content');

    // First time: create structure
    if (!modalContent.querySelector('.image-gallery')) {
        modalContent.innerHTML = `
            <h2 style="color: var(--color-text-primary); margin-bottom: var(--space-4);">
                📸 Foto Acquisite (<span id="photo-count">0</span>)
            </h2>
            <div class="image-gallery" style="margin-bottom: var(--space-4); max-height: 300px; overflow-y: auto; text-align: center; padding: var(--space-3); background: var(--color-bg-secondary); border-radius: var(--radius-md);"></div>
            <div class="batch-controls"><!-- Buttons here --></div>
        `;
    }

    const gallery = modalContent.querySelector('.image-gallery');
    const photoCount = modalContent.querySelector('#photo-count');

    // Clear gallery and re-render (preserves other elements)
    gallery.innerHTML = '';
    photoCount.textContent = capturedImages.length;

    capturedImages.forEach((img, index) => {
        const container = document.createElement('div');
        container.style.cssText = 'position: relative; display: inline-block; margin: 0.5rem;';
        container.dataset.imageIndex = index;

        const imgElement = document.createElement('img');
        imgElement.src = img.dataUrl;
        imgElement.dataset.imageIndex = index;
        imgElement.style.cssText = 'max-width: 150px; max-height: 150px; border-radius: var(--radius-md); border: 2px solid var(--color-border-primary);';

        imgElement.onload = () => {
            console.log(`[PREVIEW-IMG-${index}] ✅ Loaded`, {
                complete: imgElement.complete,
                dimensions: `${imgElement.naturalWidth}x${imgElement.naturalHeight}`
            });
        };

        imgElement.onerror = (e) => {
            console.error(`[PREVIEW-IMG-${index}] ❌ Failed`, e);
        };

        container.appendChild(imgElement);
        gallery.appendChild(container);
    });

    // Show modal
    modal.style.display = 'flex';
    modal.classList.add('active');
}
```

---

## Step 6: Test and Verify (30 minutes)

After deploying targeted fix:

1. User repeats test protocol
2. Verify ALL images appear consistently
3. Verify Eruda Network shows only 1 POST to `/upload-batch`
4. Verify PDF created successfully

**Success criteria**:
- ✅ All 3 photos appear in preview
- ✅ No "alternating" or intermittent display
- ✅ Console shows all `[PREVIEW-IMG-*] ✅ Loaded`
- ✅ `debugPreviewImages()` shows `complete: true` for all images

---

## Estimated Timeline

| Step | Duration | Total Elapsed |
|------|----------|---------------|
| 1. Add debug code | 30 min | 0:30 |
| 2. Deploy | 5 min | 0:35 |
| 3. User testing | 15 min | 0:50 |
| 4. Analyze data | 30 min | 1:20 |
| 5. Implement fix | 30 min | 1:50 |
| 6. Deploy + verify | 30 min | 2:20 |

**Total**: ~2.5 hours to resolution

**Worst case** (if Blob URL refactor needed): +2 hours = 4.5 hours

---

## Rollback Plan

If diagnostic deployment breaks something:

```bash
git revert HEAD
git push
```

Railway will auto-deploy previous working version.

---

## Next Steps After Resolution

1. **Remove debug code** (keep only critical logging)
2. **Refactor duplicate prevention** (consolidate Fixes 2+6)
3. **Add integration test** for camera batch flow
4. **Document final solution** in CAMERA_BATCH_ISSUE_ANALYSIS.md

---

**Status**: READY TO EXECUTE
**Priority**: HIGH
**Confidence**: 85% this will diagnose and fix the issue
