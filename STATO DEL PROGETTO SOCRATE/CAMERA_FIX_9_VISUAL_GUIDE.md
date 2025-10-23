# Camera FIX 9 - Visual Guide

**Diagrams and Flowcharts for Understanding FIX 9**

---

## 1. Problem Visualization: Oppo Odd/Even Bug

### FIX 8 Behavior (BROKEN)

```
User Timeline                     Browser State                    Result
─────────────────────────────────────────────────────────────────────────────

T0: Click camera button
    └─> Camera app opens          input.files = []                 ✓ Ready

T1: User takes Photo 1 (ODD)
    Stays in camera app           input.files = []                 ⏳ Pending
                                  (Photo 1 in OS buffer)

T2: User takes Photo 2 (EVEN)
    Returns to browser            input.files = [Photo1]           🔥 Race!
                                  (Photo 2 in OS buffer)

T3: change event fires
    processCameraFile() runs      Processing Photo 1...            ✓ OK

T4: Processing completes
    cameraInput.value = ''        input.files = []                 ❌ LOST!
                                  (Photo 2 destroyed!)

T5: User takes Photo 3 (ODD)
    Stays in camera app           input.files = []                 ⏳ Pending
                                  (Photo 3 in OS buffer)

T6: User takes Photo 4 (EVEN)
    Returns to browser            input.files = [Photo3]           🔥 Race!
                                  (Photo 4 in OS buffer)

T7: change event fires
    processCameraFile() runs      Processing Photo 3...            ✓ OK

T8: Processing completes
    cameraInput.value = ''        input.files = []                 ❌ LOST!
                                  (Photo 4 destroyed!)

──────────────────────────────────────────────────────────────────────────────
FINAL RESULT: Photos 1, 3 captured ✅
              Photos 2, 4 LOST ❌
              Success Rate: 50%
```

### FIX 9 Behavior (CORRECT)

```
User Timeline                     Browser State                    Tracker State           Result
────────────────────────────────────────────────────────────────────────────────────────────────────

T0: Click camera button
    └─> Camera app opens          input.files = []                 processed = {}          ✓ Ready

T1: User takes Photo 1 (ODD)
    Stays in camera app           input.files = []                 processed = {}          ⏳ Pending
                                  (Photo 1 in OS buffer)

T2: User takes Photo 2 (EVEN)
    Returns to browser            input.files = [Photo1]           processed = {}          ✅ Ready
                                  (Photo 2 in OS buffer)

T3: change event fires
    processCameraFile() runs
    getNewFiles([Photo1])         Processing Photo 1...            processed = {}          ✅ Processing
    → [Photo1] (new)

T4: Processing completes
    markProcessed(Photo1)         input.files = [Photo1]           processed = {           ✅ Captured
    ⚠️ NO INPUT RESET              (Photo 2 in OS buffer)           Photo1: {...}          Photo 1
                                                                  }                       ⏳ Photo 2 pending

T5: User takes Photo 3 (ODD)
    Stays in camera app           input.files = [Photo1]           processed = {           ⏳ Pending
                                  (Photo 2, 3 in OS buffer)        Photo1: {...}
                                                                  }

T6: User takes Photo 4 (EVEN)
    Returns to browser            input.files = [Photo1,           processed = {           ✅ Ready
                                                Photo2,            Photo1: {...}
                                                Photo3]            }
                                  (Photo 4 in OS buffer)

T7: change event fires
    processCameraFile() runs
    getNewFiles([P1, P2, P3])     Processing Photo 2, 3...         processed = {           ✅ Processing
    → [Photo2, Photo3]                                             Photo1: {...}
    (Photo1 filtered)                                              }

T8: Processing completes
    markProcessed(Photo2, 3)      input.files = [P1, P2, P3]       processed = {           ✅ Captured
    ⚠️ NO INPUT RESET              (Photo 4 in OS buffer)           Photo1: {...},         Photos 1-3
                                                                    Photo2: {...},         ⏳ Photo 4 pending
                                                                    Photo3: {...}
                                                                  }

T9: User clicks "Upload"
    uploadBatch() SUCCESS         input.files = []                 processed = {}          ✅ Session
    cleanupCameraSession()        (NOW safe to reset)              (tracker reset)        complete
                                                                                          All 4 photos
                                                                                          uploaded ✅

─────────────────────────────────────────────────────────────────────────────────────────────────────
FINAL RESULT: Photos 1, 2, 3, 4 ALL captured ✅
              Photos LOST: 0 ❌
              Success Rate: 100%
```

---

## 2. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIX 9 CAMERA SYSTEM DATA FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ User Action  │
│ (Camera)     │
└──────┬───────┘
       │
       │ Takes photo(s)
       │
       ▼
┌────────────────────────────────────────┐
│ OS Camera App                          │
│ - Buffers photos in memory             │
│ - Returns to browser when user exits   │
└────────────────┬───────────────────────┘
                 │
                 │ On focus return
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ Browser FileInput                                            │
│ <input type="file" accept="image/*" capture="environment">  │
│ input.files = FileList [Photo1, Photo2, ...]                │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ change/input event
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ processCameraFile()                                          │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 1. Get files from input                                  ││
│ │    const files = Array.from(cameraInput.files)           ││
│ │                                                           ││
│ │ 2. Filter NEW files (deduplication)                      ││
│ │    const newFiles = cameraFileTracker.getNewFiles(files) ││
│ │                                                           ││
│ │    ┌────────────────────────────────────────┐            ││
│ │    │ CameraFileTracker                      │            ││
│ │    │ ────────────────────────                │            ││
│ │    │ Map<fileKey, {imageId, timestamp}>     │            ││
│ │    │                                         │            ││
│ │    │ getFileKey(file):                      │            ││
│ │    │   "name::size::lastModified"           │            ││
│ │    │                                         │            ││
│ │    │ isProcessed(file):                     │            ││
│ │    │   return Map.has(fileKey)              │            ││
│ │    └────────────────────────────────────────┘            ││
│ │                                                           ││
│ │ 3. Process ONLY new files in parallel                    ││
│ │    await Promise.allSettled(                             ││
│ │      newFiles.map(file => handleCameraCaptureAsync(file))││
│ │    )                                                      ││
│ └──────────────────┬───────────────────────────────────────┘│
└────────────────────┼────────────────────────────────────────┘
                     │
                     │ For each file
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ handleCameraCaptureAsync(file)                               │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 1. Validate file (type, size)                            ││
│ │                                                           ││
│ │ 2. Create Blob URL (memory-efficient)                    ││
│ │    const blobUrl = URL.createObjectURL(file)             ││
│ │                                                           ││
│ │ 3. Validate image (decodable, non-corrupt)               ││
│ │    await validateImageUrl(blobUrl)                       ││
│ │                                                           ││
│ │ 4. Generate unique image ID                              ││
│ │    const imageId = `img-${Date.now()}-${random()}`       ││
│ │                                                           ││
│ │ 5. Add to captured images                                ││
│ │    capturedImages.push({id, file, blobUrl, timestamp})   ││
│ │                                                           ││
│ │ 6. Return imageId (for tracker)                          ││
│ │    return imageId                                        ││
│ └──────────────────┬───────────────────────────────────────┘│
└────────────────────┼────────────────────────────────────────┘
                     │
                     │ Returns imageId
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ processCameraFile() (continued)                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 4. Mark successful files as processed                    ││
│ │    successful.forEach((result, index) => {               ││
│ │      const imageId = result.value                        ││
│ │      cameraFileTracker.markProcessed(newFiles[index],    ││
│ │                                       imageId)            ││
│ │    })                                                     ││
│ │                                                           ││
│ │ 5. ⚠️ CRITICAL: Do NOT reset input                       ││
│ │    (Preserves buffered photos in OS memory)              ││
│ │                                                           ││
│ │ 6. Show preview modal                                    ││
│ │    showBatchPreview()                                    ││
│ └──────────────────┬───────────────────────────────────────┘│
└────────────────────┼────────────────────────────────────────┘
                     │
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ showBatchPreview()                                           │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Display modal with:                                      ││
│ │ - Gallery of all captured images (thumbnails)            ││
│ │ - Document name input                                    ││
│ │ - Action buttons:                                        ││
│ │   [📷 Add Another Photo] [❌ Cancel] [☁️ Upload]         ││
│ └──────────────────────────────────────────────────────────┘│
└────────────────────┬───────────────────────────────────────┘
                     │
                     │ User chooses action
                     │
         ┌───────────┴────────────┬─────────────────┐
         │                        │                 │
         ▼                        ▼                 ▼
┌─────────────────┐    ┌──────────────────┐  ┌───────────────┐
│ Add Another     │    │ Cancel Batch     │  │ Upload Batch  │
│ Photo           │    │                  │  │               │
└────────┬────────┘    └────────┬─────────┘  └───────┬───────┘
         │                      │                    │
         │                      │                    │
         │ openCamera()         │ cleanupCamera      │ uploadBatch()
         │ (session continues)  │ Session()          │
         │                      │                    │
         └──────────┐           │                    │
                    │           │                    │
                    ▼           ▼                    ▼
         ┌────────────────────────────┐   ┌──────────────────┐
         │ Back to camera             │   │ Upload to server │
         │ (tracker persists)         │   │                  │
         └────────────────────────────┘   └────────┬─────────┘
                                                    │
                                                    │ On success
                                                    │
                                                    ▼
                                         ┌────────────────────────┐
                                         │ cleanupCameraSession() │
                                         │ ────────────────────── │
                                         │ 1. Revoke Blob URLs    │
                                         │ 2. Clear capturedImages│
                                         │ 3. tracker.reset()     │
                                         │ 4. input.value = ''    │
                                         └────────────────────────┘
```

---

## 3. State Machine Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FIX 9 CAMERA STATE MACHINE                           │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────┐
                    │        [IDLE]               │
                    │  capturedImages = []        │
                    │  tracker.processed = {}     │
                    │  input.value = ''           │
                    └──────────┬──────────────────┘
                               │
                               │ window.openCamera()
                               │ → cameraInput.click()
                               │
                               ▼
                    ┌─────────────────────────────┐
                    │    [CAMERA_OPEN]            │
                    │  OS camera app opens        │
                    │  User can take photos       │
                    └──────────┬──────────────────┘
                               │
                               │ User takes photo(s)
                               │
                               ▼
                    ┌─────────────────────────────┐
                    │     [CAPTURING]             │
                    │  Photos buffered in OS      │
                    │  Waiting for user to return │
                    └──────────┬──────────────────┘
                               │
                               │ User returns to browser
                               │ → change/input event fires
                               │ (or polling detects files)
                               │
                               ▼
                    ┌─────────────────────────────┐
          ┌────────│    [PROCESSING]             │
          │        │  isProcessing = true        │
          │        │  getNewFiles() filters      │
          │        │  handleCameraCaptureAsync() │
          │        │  markProcessed()            │
          │        │  input NOT reset ⚠️         │
          │        └──────────┬──────────────────┘
          │                   │
          │                   │ Processing complete
          │                   │ isProcessing = false
          │                   │
          │        ┌──────────┴─────────────────────────┐
          │        │                                    │
          │        │ More photos buffered?              │
          │        │ (User took another while           │
          │        │  processing was happening)         │
          │        │                                    │
          │        │ YES                     NO         │
          │        │                                    │
          │        ▼                         ▼          │
          │  ┌──────────┐        ┌─────────────────────┴─────┐
          │  │ change   │        │     [PREVIEWING]           │
          │  │ event    │        │  Modal shows gallery       │
          │  │ fires    │        │  User can:                 │
          │  │ again    │        │  - Add Another Photo       │
          │  └────┬─────┘        │  - Cancel Batch            │
          │       │              │  - Upload Batch            │
          └───────┘              └─────────────┬──────────────┘
                                               │
                    ┌──────────────────────────┼───────────────────────┐
                    │                          │                       │
                    │                          │                       │
                    ▼                          ▼                       ▼
         ┌──────────────────┐      ┌───────────────────┐   ┌─────────────────────┐
         │ [ADD ANOTHER     │      │ [CANCEL BATCH]    │   │ [UPLOAD BATCH]      │
         │  PHOTO]          │      │                   │   │                     │
         │                  │      │ Confirm dialog    │   │ FormData upload     │
         │ Modal closes     │      │ ↓                 │   │ ↓                   │
         │ openCamera()     │      │ YES               │   │ SUCCESS             │
         └────────┬─────────┘      └─────────┬─────────┘   └──────────┬──────────┘
                  │                          │                        │
                  │                          │                        │
                  │ Session                  │ Session                │ Session
                  │ continues                │ ends                   │ ends
                  │                          │                        │
                  ▼                          ▼                        ▼
         ┌─────────────────┐      ┌────────────────────┐   ┌────────────────────┐
         │ [CAMERA_OPEN]   │      │ cleanupCamera      │   │ cleanupCamera      │
         │ (loop back)     │      │ Session()          │   │ Session()          │
         │                 │      │ ↓                  │   │ ↓                  │
         │ Tracker         │      │ tracker.reset()    │   │ tracker.reset()    │
         │ persists        │      │ input.value = ''   │   │ input.value = ''   │
         └─────────────────┘      │ capturedImages=[]  │   │ capturedImages=[]  │
                                  │ ↓                  │   │ ↓                  │
                                  │ [IDLE]             │   │ [IDLE]             │
                                  └────────────────────┘   └────────────────────┘

════════════════════════════════════════════════════════════════════════════
State Invariants:
  - Input is NEVER reset while state ∈ {CAMERA_OPEN, CAPTURING, PROCESSING, PREVIEWING}
  - Input is ONLY reset when transitioning to [IDLE]
  - Tracker persists across CAMERA_OPEN → PROCESSING loops (multi-photo capture)
  - Blob URLs are only revoked in cleanupCameraSession() (transition to IDLE)
```

---

## 4. Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FIX 9 MEMORY ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ JavaScript Heap                                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ cameraInput.files (FileList)                                 │ │
│  │ ──────────────────────────────                               │ │
│  │                                                               │ │
│  │  [0] File {                                                  │ │
│  │        name: "IMG_1234.jpg",                                 │ │
│  │        size: 2097152,  // 2MB                                │ │
│  │        lastModified: 1729584000000,                          │ │
│  │        type: "image/jpeg",                                   │ │
│  │        ⚠️ Blob data: ~2MB in memory                          │ │
│  │      }                                                        │ │
│  │                                                               │ │
│  │  [1] File { ... }  // ~2MB                                   │ │
│  │  [2] File { ... }  // ~2MB                                   │ │
│  │  ...                                                          │ │
│  │  [19] File { ... } // ~2MB                                   │ │
│  │                                                               │ │
│  │  Total: 20 files × 2MB = ~40MB                               │ │
│  │  Lifecycle: Until cameraInput.value = '' in cleanup          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ capturedImages (Array)                                       │ │
│  │ ──────────────────────────                                   │ │
│  │                                                               │ │
│  │  [                                                            │ │
│  │    {                                                          │ │
│  │      id: "img-1729584000000-abc123",      // ~50 bytes       │ │
│  │      file: File { ... },                  // Reference only  │ │
│  │      blobUrl: "blob:http://.../abc123",   // ~100 bytes      │ │
│  │      timestamp: 1729584000000             // 8 bytes         │ │
│  │    },                                                         │ │
│  │    { ... },                                                   │ │
│  │    { ... },                                                   │ │
│  │    ...                                                        │ │
│  │  ]                                                            │ │
│  │                                                               │ │
│  │  Total: 20 images × ~160 bytes = ~3.2KB                      │ │
│  │  Lifecycle: Until capturedImages = [] in cleanup             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ cameraFileTracker.processedFiles (Map)                       │ │
│  │ ──────────────────────────────────────                       │ │
│  │                                                               │ │
│  │  Map {                                                        │ │
│  │    "IMG_1234.jpg::2097152::1729584000000" => {               │ │
│  │      imageId: "img-1729584000000-abc123",  // ~50 bytes      │ │
│  │      timestamp: 1729584000000,             // 8 bytes        │ │
│  │      fileName: "IMG_1234.jpg"              // ~20 bytes      │ │
│  │    },                                                         │ │
│  │    "IMG_1235.jpg::2097152::1729584001000" => { ... },        │ │
│  │    ...                                                        │ │
│  │  }                                                            │ │
│  │                                                               │ │
│  │  Total: 20 entries × ~200 bytes = ~4KB                       │ │
│  │  Lifecycle: Until tracker.reset() in cleanup                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ Browser Blob Storage (Separate from JS Heap)                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Blob URLs (Managed by browser)                               │ │
│  │ ──────────────────────────────                               │ │
│  │                                                               │ │
│  │  blob:http://localhost:5000/abc123 → File { ... } (2MB)      │ │
│  │  blob:http://localhost:5000/def456 → File { ... } (2MB)      │ │
│  │  blob:http://localhost:5000/ghi789 → File { ... } (2MB)      │ │
│  │  ...                                                          │ │
│  │                                                               │ │
│  │  Total: 20 Blob URLs referencing 40MB of file data           │ │
│  │  (File data is SAME as cameraInput.files, not duplicated)    │ │
│  │                                                               │ │
│  │  Lifecycle: Until URL.revokeObjectURL() in cleanup           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════════
TOTAL MEMORY USAGE (20 photos):
  File data (input.files):       40MB  (99.9%)
  Blob URLs (references only):   <1KB  (0.0%)
  capturedImages metadata:       3.2KB (0.0%)
  Tracker metadata:              4KB   (0.0%)
  ────────────────────────────────────────────
  TOTAL:                         ~40MB (100%)

FIX 9 Overhead: 7.2KB / 40MB = 0.018% (negligible)
```

---

## 5. Deduplication Algorithm

```
┌─────────────────────────────────────────────────────────────────────────┐
│               FIX 9 DEDUPLICATION ALGORITHM                             │
└─────────────────────────────────────────────────────────────────────────┘

Input: cameraInput.files = FileList [File1, File2, File3, File1 (duplicate)]
                                      ↓
                         ┌────────────────────────┐
                         │ getNewFiles(fileList)  │
                         └──────────┬─────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │ Convert to array               │
                    │ files = Array.from(fileList)   │
                    └──────────┬──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────────────────┐
                    │ Filter with deduplication      │
                    │ files.filter(f => {            │
                    │   return !isProcessed(f)       │
                    │ })                              │
                    └──────────┬──────────────────────┘
                               │
                               │ For each file
                               │
            ┌──────────────────┼──────────────────┬─────────────┐
            │                  │                  │             │
            ▼                  ▼                  ▼             ▼
        ┌───────┐          ┌───────┐         ┌───────┐     ┌───────┐
        │ File1 │          │ File2 │         │ File3 │     │ File1 │
        └───┬───┘          └───┬───┘         └───┬───┘     └───┬───┘
            │                  │                 │             │
            ▼                  ▼                 ▼             ▼
        ┌───────────────────────────────────────────────────────┐
        │ getFileKey(file)                                      │
        │ ─────────────────                                     │
        │ return `${file.name}::${file.size}::${file.lastModified}` │
        └───┬───────────────┬───────────────┬───────────────┬───┘
            │               │               │               │
            ▼               ▼               ▼               ▼
        "IMG_1234.jpg     "IMG_1235.jpg   "IMG_1236.jpg   "IMG_1234.jpg
         ::2097152         ::2097152       ::2097152       ::2097152
         ::1729584000000"  ::1729584001000"::1729584002000"::1729584000000"
                                                           (DUPLICATE KEY!)
            │               │               │               │
            ▼               ▼               ▼               ▼
        ┌───────────────────────────────────────────────────────┐
        │ processedFiles.has(key)                              │
        │ ────────────────────────                             │
        │ Check if key exists in Map                           │
        └───┬───────────────┬───────────────┬───────────────┬───┘
            │               │               │               │
            ▼               ▼               ▼               ▼
        false           false           false           true (if File1
        (NEW)           (NEW)           (NEW)           was processed)
            │               │               │               │
            ▼               ▼               ▼               ▼
        INCLUDE         INCLUDE         INCLUDE         EXCLUDE
            │               │               │
            └───────────────┴───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ newFiles =    │
                    │ [File1,       │
                    │  File2,       │
                    │  File3]       │
                    │               │
                    │ (File1 dup    │
                    │  filtered     │
                    │  out)         │
                    └───────────────┘

════════════════════════════════════════════════════════════════════════
KEY INSIGHT: File.lastModified is CRITICAL
  - Same filename + size can occur if user deletes and retakes photo
  - lastModified timestamp changes each time camera captures
  - Ensures unique key for each physical photo

EXAMPLE:
  User takes IMG_1234.jpg → 1729584000000
  User deletes photo in camera app
  User takes new IMG_1234.jpg → 1729584120000

  Keys are different:
    "IMG_1234.jpg::2097152::1729584000000" (old)
    "IMG_1234.jpg::2097152::1729584120000" (new)

  Both photos processed correctly ✅
```

---

## 6. Session Lifecycle Timeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  FIX 9 SESSION LIFECYCLE TIMELINE                       │
└─────────────────────────────────────────────────────────────────────────┘

Time   Event                           State Changes
──────────────────────────────────────────────────────────────────────────
T0     User clicks "📷 Camera" button
       └─> window.openCamera()          capturedImages = []
                                        tracker.processedFiles = {}
                                        input.value = ''
                                        State: [IDLE] → [CAMERA_OPEN]

T1     Camera app opens
       User sees camera viewfinder      State: [CAMERA_OPEN]

T2     User takes Photo 1
       └─> OS buffers photo             State: [CAMERA_OPEN] → [CAPTURING]

T3     User returns to browser
       └─> change event fires            State: [CAPTURING] → [PROCESSING]
           input.files = [Photo1]

T4     processCameraFile() executes
       ├─> getNewFiles([Photo1])        newFiles = [Photo1] (all new)
       │   → [Photo1] (new)
       │
       ├─> handleCameraCaptureAsync()   capturedImages = [
       │                                  {id: "img-1", file: Photo1, ...}
       │                                ]
       │
       ├─> markProcessed(Photo1)        tracker.processedFiles = {
       │                                  "Photo1-key": {...}
       │                                }
       │
       └─> showBatchPreview()           State: [PROCESSING] → [PREVIEWING]
           ⚠️ input NOT reset!           input.files = [Photo1] (preserved)

T5     Modal shows 1 photo
       User clicks "📷 Add Another"
       └─> addAnotherPhoto()            State: [PREVIEWING] → [CAMERA_OPEN]
           Modal closes                 (session continues, tracker persists)

T6     Camera reopens
       User takes Photo 2               State: [CAMERA_OPEN] → [CAPTURING]

T7     User returns to browser
       └─> change event fires            State: [CAPTURING] → [PROCESSING]
           input.files = [Photo1,        (Photo1 still in input!)
                          Photo2]

T8     processCameraFile() executes
       ├─> getNewFiles([P1, P2])        newFiles = [Photo2] (P1 filtered)
       │   → [Photo2] (P1 skipped)      console: "Filtered 1 duplicate file(s)"
       │
       ├─> handleCameraCaptureAsync()   capturedImages = [
       │                                  {id: "img-1", file: Photo1, ...},
       │                                  {id: "img-2", file: Photo2, ...}
       │                                ]
       │
       ├─> markProcessed(Photo2)        tracker.processedFiles = {
       │                                  "Photo1-key": {...},
       │                                  "Photo2-key": {...}
       │                                }
       │
       └─> showBatchPreview()           State: [PROCESSING] → [PREVIEWING]
           ⚠️ input NOT reset!           input.files = [P1, P2] (preserved)

T9     Modal shows 2 photos
       User enters document name
       User clicks "☁️ Upload"
       └─> uploadBatch()                State: [PREVIEWING] → [UPLOADING]

T10    FormData created
       ├─> files appended to FormData   FormData: [Photo1, Photo2]
       └─> POST /api/upload/batch       Network request sent

T11    Server responds 200 OK
       └─> Upload SUCCESS               State: [UPLOADING] → [CLEANUP]

T12    cleanupCameraSession() executes
       ├─> Revoke Blob URLs             URL.revokeObjectURL(img-1.blobUrl)
       │                                URL.revokeObjectURL(img-2.blobUrl)
       │
       ├─> Clear images                 capturedImages = []
       │
       ├─> Reset tracker                tracker.processedFiles = {}
       │                                tracker.sessionStartTime = now
       │
       └─> Reset input                  input.value = ''
                                        input.files = []

T13    Modal closes
       └─> closePreviewModal()          State: [CLEANUP] → [IDLE]

T14    Success message shown
       Document list refreshed          Ready for next session ✅

──────────────────────────────────────────────────────────────────────────
Total session time: ~60 seconds (typical)
Photos captured: 2/2 (100% success rate)
Memory leaked: 0 bytes (all Blob URLs revoked)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Author**: Frontend Architect Prime
