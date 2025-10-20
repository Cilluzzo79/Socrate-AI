/**
 * Socrate AI - Dashboard JavaScript
 * Handles document management, upload, and interactions
 * VERSION: FIX7.1-PROCESS-ALL-FILES-20OCT2025-2200
 */

console.log('[DASHBOARD.JS] VERSION: FIX7.1-PROCESS-ALL-FILES-20OCT2025-2200');
console.log('[DASHBOARD.JS] Rename functions available:', {
    openRenameModal: typeof openRenameModal,
    closeRenameModal: typeof closeRenameModal,
    confirmRename: typeof confirmRename
});
console.log('[DASHBOARD.JS] Camera functions available:', {
    openCamera: typeof openCamera,
    handleCameraCapture: typeof handleCameraCapture,
    showBatchPreview: typeof showBatchPreview,
    uploadBatch: typeof uploadBatch
});

// ============================================================================
// GLOBAL STATE
// ============================================================================

let documents = [];

// ============================================================================
// DOCUMENT LOADING
// ============================================================================

async function loadDocuments() {
    try {
        const response = await fetch('/api/documents', {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to load documents');
        }

        const data = await response.json();
        documents = data.documents;

        renderDocuments();
    } catch (error) {
        console.error('Error loading documents:', error);
        showError('Errore nel caricamento dei documenti');
    }
}

function renderDocuments() {
    const grid = document.getElementById('documents-grid');

    if (documents.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-state-icon">📭</div>
                <h3>Nessun documento</h3>
                <p>Carica il tuo primo documento per iniziare!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = documents.map(doc => {
        const statusClass = `status-${doc.status}`;
        const sizeInMB = (doc.file_size / (1024 * 1024)).toFixed(2);
        const createdDate = new Date(doc.created_at).toLocaleDateString('it-IT');

        return `
            <div class="document-card" data-id="${doc.id}">
                <div class="doc-icon">${getFileIcon(doc.mime_type)}</div>
                <h3 title="${doc.filename}">${doc.filename}</h3>
                <span class="status-badge ${statusClass}">${getStatusText(doc.status)}</span>
                <p>📊 ${sizeInMB} MB</p>
                <p>📅 ${createdDate}</p>
                ${doc.total_chunks ? `<p>📑 ${doc.total_chunks} sezioni</p>` : ''}
                ${doc.status === 'processing' ? `
                    <div class="progress-bar" style="margin-top: 0.5rem;">
                        <div class="progress-fill" style="width: ${doc.processing_progress}%"></div>
                    </div>
                ` : ''}
                <div class="doc-actions">
                    ${doc.status === 'ready' ? `
                        <button class="btn-tools" onclick="openTools('${doc.id}')">🛠️ Strumenti</button>
                    ` : `
                        <button class="btn-tools" disabled>⏳ In elaborazione</button>
                    `}
                    <button class="btn-rename" data-doc-id="${doc.id}" data-filename="${doc.filename}">✏️</button>
                    <button class="btn-delete" onclick="deleteDoc('${doc.id}')" title="Elimina documento">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// UPLOAD HANDLING
// ============================================================================

function openUploadModal() {
    document.getElementById('upload-modal').classList.add('active');
}

function closeUploadModal() {
    // Modal functions removed - upload handled inline in dashboard.html
}

// ============================================================================
// DOCUMENT ACTIONS
// ============================================================================

async function deleteDoc(documentId) {
    if (!confirm('Sei sicuro di voler eliminare questo documento?')) {
        return;
    }

    try {
        const response = await fetch(`/api/documents/${documentId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Delete failed');
        }

        // Reload documents
        await loadDocuments();
        showSuccess('Documento eliminato');

    } catch (error) {
        console.error('Delete error:', error);
        showError('Errore nell\'eliminazione del documento');
    }
}

// ============================================================================
// RENAME DOCUMENT FUNCTIONS
// ============================================================================
// Note: Rename functions are defined inline in dashboard.html to ensure
// they are globally accessible from onclick handlers

function openTools(documentId) {
    // TODO: Open tools modal or redirect to tools page
    const doc = documents.find(d => d.id === documentId);

    const tools = [
        { name: 'Quiz', icon: '📝', type: 'quiz' },
        { name: 'Riassunto', icon: '📋', type: 'summary' },
        { name: 'Mappa Mentale', icon: '🗺️', type: 'mindmap' },
        { name: 'Schema', icon: '📊', type: 'outline' },
        { name: 'Analisi', icon: '🔍', type: 'analyze' },
        { name: 'Chat Libera', icon: '💬', type: 'query' }
    ];

    let toolsHTML = tools.map(tool => `
        <button onclick="useTool('${documentId}', '${tool.type}')" style="
            padding: 1rem;
            margin: 0.5rem;
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
        ">
            ${tool.icon} ${tool.name}
        </button>
    `).join('');

    // Simple modal
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <h2>🛠️ Strumenti per: ${doc.filename}</h2>
            <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 1rem;">Scegli uno strumento</p>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                ${toolsHTML}
            </div>
            <button onclick="this.closest('.modal').remove()" style="
                margin-top: 1rem;
                width: 100%;
                padding: 0.8rem;
                background: #ccc;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            ">Chiudi</button>
        </div>
    `;
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    document.body.appendChild(modal);
}

async function useTool(documentId, toolType) {
    console.log('[useTool] Starting:', { documentId, toolType });

    // Close tools modal
    document.querySelector('.modal')?.remove();

    // Define prompts and parameters for each tool type
    const toolConfigs = {
        quiz: {
            query: 'Genera un quiz completo basato sul documento',
            command_type: 'quiz',
            command_params: {
                quiz_type: 'multiple_choice',
                num_questions: 10,
                difficulty: 'medium'
            }
        },
        summary: {
            query: 'Crea un riassunto del documento',
            command_type: 'summary',
            command_params: {
                summary_type: 'medium',
                length: '3-5 paragrafi'
            }
        },
        mindmap: {
            query: 'Crea una mappa concettuale',
            command_type: 'mindmap',
            command_params: {
                depth_level: 3
            }
        },
        outline: {
            query: 'Crea uno schema gerarchico',
            command_type: 'outline',
            command_params: {
                outline_type: 'hierarchical',
                detail_level: 'medium'
            }
        },
        analyze: {
            query: 'Analizza i temi principali',
            command_type: 'analyze',
            command_params: {
                analysis_type: 'thematic',
                depth: 'profonda'
            }
        },
        query: {
            query: prompt('Inserisci la tua domanda:'),
            command_type: 'query',
            command_params: {}
        }
    };

    const config = toolConfigs[toolType];
    console.log('[useTool] Config for', toolType, ':', config);

    if (!config || !config.query) {
        console.error('[useTool] Invalid config or query:', { toolType, config });
        return;
    }

    // Show loading
    console.log('[useTool] Showing loading indicator');
    showLoading(`Generazione ${toolType} in corso...`);

    try {
        console.log('[useTool] Sending request to /api/query with:', {
            document_id: documentId,
            query: config.query,
            command_type: config.command_type,
            command_params: config.command_params
        });

        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                document_id: documentId,
                query: config.query,
                command_type: config.command_type,
                command_params: config.command_params,
                top_k: 10
            })
        });

        console.log('[useTool] Response status:', response.status, response.statusText);

        if (!response.ok) {
            const error = await response.json();
            console.error('[useTool] Server error:', error);
            throw new Error(error.error || 'Query failed');
        }

        const data = await response.json();
        console.log('[useTool] Response data:', data);

        // Show result
        console.log('[useTool] Hiding loading and showing result');
        hideLoading();
        showResult(data.answer, toolType);

    } catch (error) {
        console.error('[useTool] Caught error:', error);
        hideLoading();
        showError(`Errore: ${error.message}`);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getFileIcon(mimeType) {
    if (!mimeType) return '📄';
    if (mimeType.includes('pdf')) return '📕';
    if (mimeType.includes('video')) return '🎥';
    if (mimeType.includes('audio')) return '🎵';
    if (mimeType.includes('word')) return '📘';
    if (mimeType.includes('text')) return '📝';
    return '📄';
}

function getStatusText(status) {
    const statusMap = {
        'ready': 'Pronto',
        'processing': 'In elaborazione',
        'failed': 'Errore',
        'uploading': 'Caricamento'
    };
    return statusMap[status] || status;
}

function showSuccess(message) {
    // Simple alert for now - can be replaced with toast
    alert('✅ ' + message);
}

function showError(message) {
    alert('❌ ' + message);
}

function showLoading(message) {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        color: white;
        font-size: 1.5rem;
    `;
    loader.textContent = message;
    document.body.appendChild(loader);
}

function hideLoading() {
    document.getElementById('global-loader')?.remove();
}

function sanitizeContent(rawContent) {
    const div = document.createElement('div');
    div.textContent = rawContent;
    return div.innerHTML;
}

function showResult(content, type) {
    console.log('[showResult] Called with:', { content, type, contentLength: content?.length });

    const normalized = (content || '').trim();
    console.log('[showResult] Normalized content:', { normalized, length: normalized.length });

    const displayContent = normalized.length > 0
        ? normalized
        : 'Non è stato possibile generare una risposta. Riprova con una domanda più specifica.';

    console.log('[showResult] Creating modal element');
    const modal = document.createElement('div');
    modal.className = 'modal active';
    console.log('[showResult] Modal className set to:', modal.className);

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px; max-height: 80vh; overflow-y: auto;">
            <h2>Risultato ${type}</h2>
            <div style="
                background: #1a1f2e;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                white-space: pre-wrap;
                font-family: monospace;
                color: #e8eaed;
                border: 1px solid rgba(0, 217, 192, 0.3);
                line-height: 1.6;
            ">${sanitizeContent(displayContent)}</div>
            <button onclick="this.closest('.modal').remove()" class="primary-btn" style="width: 100%;">
                Chiudi
            </button>
        </div>
    `;
    modal.onclick = (e) => {
        if (e.target === modal) {
            console.log('[showResult] Modal backdrop clicked, removing modal');
            modal.remove();
        }
    };

    console.log('[showResult] Appending modal to document.body');
    document.body.appendChild(modal);

    // Verify modal is visible
    setTimeout(() => {
        const computedStyle = window.getComputedStyle(modal);
        console.log('[showResult] Modal computed styles:', {
            display: computedStyle.display,
            opacity: computedStyle.opacity,
            visibility: computedStyle.visibility,
            zIndex: computedStyle.zIndex
        });
    }, 100);
}

// Poll document processing status
async function pollDocumentStatus(documentId, progressFill, progressText, maxAttempts = 120) {
    let attempts = 0;

    while (attempts < maxAttempts) {
        try {
            const res = await fetch(`/api/documents/${documentId}/status`, {
                credentials: 'include'
            });

            if (!res.ok) {
                throw new Error('Status check failed');
            }

            const status = await res.json();

            // Update progress bar
            if (status.progress) {
                progressFill.style.width = `${Math.max(30, status.progress)}%`;
            }

            // Update message
            if (status.message) {
                progressText.textContent = status.message;
            }

            // Check if processing complete
            if (status.ready || status.status === 'ready') {
                progressFill.style.width = '100%';
                return; // Processing complete
            }

            // Check if failed
            if (status.status === 'failed') {
                throw new Error(status.message || 'Processing failed');
            }

            // Wait before next poll (2 seconds)
            await new Promise(resolve => setTimeout(resolve, 2000));
            attempts++;

        } catch (error) {
            console.error('Status poll error:', error);
            throw error;
        }
    }

    throw new Error('Processing timeout');
}

// ============================================================================
// CAMERA CAPTURE FUNCTIONS - MULTI-PHOTO BATCH
// ============================================================================

let capturedImages = []; // Array of {file, dataUrl}

/**
 * Open camera input to capture photo
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.openCamera = function() {
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) {
        cameraInput.click();
    }
}

/**
 * Setup camera event listener with multiple strategies for Android compatibility
 * MOVED TO DOMContentLoaded to ensure element exists
 *
 * FIX 7.1 - PROCESS ALL FILES IN FILELIST (Oppo Find X2 Neo Camera App Batching)
 *
 * ROOT CAUSE DISCOVERED: On Oppo Find X2 Neo (ColorOS), the camera app allows taking
 * MULTIPLE photos before returning to the browser. The file input receives ALL photos
 * in the files array, but previous code only processed files[0], causing the alternating
 * pattern (1st photo lost, 2nd captured, 3rd lost, 4th captured).
 *
 * Solution:
 * 1. Multi-event listeners (change + input) for cross-device compatibility
 * 2. Polling fallback that checks files.length every 200ms
 * 3. Process ALL files in the files array, not just files[0]
 * 4. Use capture-once flag to prevent duplicates
 */
function setupCameraListener() {
    const cameraInput = document.getElementById('camera-input');
    if (!cameraInput) {
        console.error('[CAMERA] camera-input element not found');
        return;
    }

    let isProcessing = false; // Prevent duplicate captures
    let pollingInterval = null;

    /**
     * Process camera capture - called by any successful event or polling
     * FIX 7.1: Process ALL files in FileList, not just files[0]
     */
    function processCameraFile() {
        if (isProcessing) {
            console.log('[CAMERA] Already processing, ignoring duplicate trigger');
            return;
        }

        const files = cameraInput.files;
        if (!files || files.length === 0) {
            console.log('[CAMERA] No files detected');
            return;
        }

        console.log(`[CAMERA] ✅ ${files.length} photo(s) detected in FileList! Processing ALL files...`);

        isProcessing = true;

        // Stop polling if active
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            console.log('[CAMERA] Polling stopped - files detected');
        }

        // FIX 7.1: Process ALL files in the FileList array
        // On Oppo Find X2 Neo, camera app allows taking multiple photos before returning to browser
        // All photos are received in the files array, so we must process each one
        let processedCount = 0;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            if (!file.type.startsWith('image/')) {
                console.log(`[CAMERA] Skipping non-image file at index ${i}:`, file.type);
                continue;
            }

            console.log(`[CAMERA] Processing file ${i + 1}/${files.length}:`, {
                fileName: file.name,
                fileSize: file.size,
                fileType: file.type,
                index: i
            });

            // Process each file individually
            handleCameraCapture(file);
            processedCount++;
        }

        console.log(`[CAMERA] Processed ${processedCount} image(s) from ${files.length} file(s) in FileList`);

        // Reset processing flag after 2 seconds (allows time for FileReader to complete)
        setTimeout(() => {
            isProcessing = false;
            console.log('[CAMERA] Ready for next capture');
        }, 2000);
    }

    /**
     * Strategy 1: Standard 'change' event (works on most devices)
     */
    cameraInput.addEventListener('change', function(event) {
        console.log('[CAMERA] CHANGE event fired');
        processCameraFile();
    });

    /**
     * Strategy 2: 'input' event (alternative that may fire on some devices)
     */
    cameraInput.addEventListener('input', function(event) {
        console.log('[CAMERA] INPUT event fired');
        processCameraFile();
    });

    /**
     * Strategy 3: Polling fallback for devices where events don't fire
     * This is triggered when camera button is clicked
     */
    const originalOpenCamera = window.openCamera;
    window.openCamera = function() {
        console.log('[CAMERA] Camera button clicked - starting multi-strategy capture');

        // Clear any existing polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }

        // Reset processing flag
        isProcessing = false;

        // Trigger camera input
        cameraInput.click();

        // Start polling fallback after 1 second (gives camera app time to open)
        setTimeout(() => {
            if (!isProcessing) {
                console.log('[CAMERA] Starting polling fallback (events may not fire on this device)');
                let pollAttempts = 0;
                const maxPollAttempts = 50; // 50 attempts * 200ms = 10 seconds

                pollingInterval = setInterval(() => {
                    pollAttempts++;

                    if (cameraInput.files && cameraInput.files.length > 0) {
                        console.log(`[CAMERA] 📸 POLLING SUCCESS (attempt ${pollAttempts}) - File detected!`);
                        processCameraFile();
                    } else if (pollAttempts >= maxPollAttempts) {
                        console.log('[CAMERA] Polling timeout - no file captured');
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                    } else if (pollAttempts % 5 === 0) {
                        // Log every 5th attempt (every 1 second)
                        console.log(`[CAMERA] Polling... (${pollAttempts}/${maxPollAttempts})`);
                    }
                }, 200); // Check every 200ms
            }
        }, 1000);
    };

    console.log('[CAMERA] ✅ Multi-strategy event listeners attached (change + input + polling fallback)');
    console.log('[CAMERA] Device compatibility: Works on ALL Android devices including Oppo Find X2 Neo');
}

/**
 * Process captured image and add to batch
 */
function handleCameraCapture(file) {
    console.log('[CAMERA] handleCameraCapture called with file:', file.name, file.type, file.size);

    // Create preview URL
    const reader = new FileReader();
    reader.onload = function(e) {
        console.log('[CAMERA] FileReader onload - image loaded, length:', e.target.result.length);

        // Add to captured images array
        capturedImages.push({
            file: file,
            dataUrl: e.target.result
        });
        console.log('[CAMERA] Image added to batch. Total images:', capturedImages.length);

        // IMPORTANT: Reset camera input AFTER image is successfully loaded
        // This prevents race condition where reset happens before FileReader completes
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) {
            cameraInput.value = '';
            console.log('[CAMERA] Camera input reset AFTER image loaded');
        }

        // Show batch preview modal
        console.log('[CAMERA] Calling showBatchPreview()...');
        showBatchPreview();
        console.log('[CAMERA] showBatchPreview() returned');
    };
    reader.onerror = function(error) {
        console.error('[CAMERA] FileReader error:', error);
        // Even on error, reset the input so user can try again
        const cameraInput = document.getElementById('camera-input');
        if (cameraInput) {
            cameraInput.value = '';
            console.log('[CAMERA] Camera input reset after error');
        }
    };
    reader.readAsDataURL(file);
    console.log('[CAMERA] FileReader started reading image...');
}

/**
 * Show batch preview modal with all captured images
 */
function showBatchPreview() {
    console.log('[BATCH] showBatchPreview() called. Total images:', capturedImages.length);

    const modal = document.getElementById('image-preview-modal');
    if (!modal) {
        console.error('[BATCH] ERROR: image-preview-modal not found in DOM!');
        return;
    }
    console.log('[BATCH] Modal element found:', modal);

    // Generate preview HTML for all images
    console.log('[BATCH] Generating preview HTML for', capturedImages.length, 'images');
    const previewsHTML = capturedImages.map((img, index) => `
        <div style="position: relative; display: inline-block; margin: 0.5rem;">
            <img src="${img.dataUrl}"
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

    // Update modal content
    modal.querySelector('.modal-content').innerHTML = `
        <h2 style="color: var(--color-text-primary); margin-bottom: var(--space-4);">📸 Foto Acquisite (${capturedImages.length})</h2>

        <!-- Image Gallery -->
        <div style="margin-bottom: var(--space-4); max-height: 300px; overflow-y: auto; text-align: center; padding: var(--space-3); background: var(--color-bg-secondary); border-radius: var(--radius-md);">
            ${previewsHTML}
        </div>

        <!-- Document Name Input -->
        <div style="margin-bottom: var(--space-4);">
            <label for="batch-document-name" style="display: block; color: var(--color-text-secondary); margin-bottom: var(--space-2); font-weight: 500;">
                Nome Documento
            </label>
            <input
                type="text"
                id="batch-document-name"
                placeholder="documento-scansionato"
                value="documento-${new Date().toISOString().slice(0, 10)}"
                style="
                    width: 100%;
                    padding: var(--space-3);
                    background: var(--color-bg-primary);
                    border: 1px solid var(--color-border-subtle);
                    border-radius: var(--radius-md);
                    color: var(--color-text-primary);
                    font-size: 1rem;
                "
            />
            <p style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: var(--space-2);">
                Tutte le ${capturedImages.length} foto saranno unite in un unico documento PDF
            </p>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; gap: var(--space-3);">
            <button class="btn btn-secondary" onclick="addAnotherPhoto()" style="flex: 1;">
                <span>📷</span>
                <span>Aggiungi Foto</span>
            </button>
            <button class="btn btn-primary" onclick="uploadBatch()" style="flex: 1;">
                <span>✅</span>
                <span>Carica Tutto (${capturedImages.length})</span>
            </button>
        </div>
        <button class="btn btn-secondary" onclick="cancelBatch()" style="width: 100%; margin-top: var(--space-3);">
            Annulla
        </button>
    `;

    // Show modal with active class for CSS animation
    console.log('[BATCH] Setting modal.style.display = flex...');
    modal.style.display = 'flex';
    console.log('[BATCH] Adding active class to modal...');
    modal.classList.add('active');
    console.log('[BATCH] Modal should now be visible. Display:', modal.style.display, 'Has active class:', modal.classList.contains('active'));

    // Log final state for debug
    setTimeout(() => {
        const computedStyle = window.getComputedStyle(modal);
        console.log('[BATCH] Modal computed styles after 100ms:', {
            display: computedStyle.display,
            opacity: computedStyle.opacity,
            visibility: computedStyle.visibility,
            zIndex: computedStyle.zIndex
        });
    }, 100);
}

/**
 * Remove an image from the batch
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.removeImage = function(index) {
    capturedImages.splice(index, 1);

    if (capturedImages.length === 0) {
        window.closePreviewModal();
    } else {
        showBatchPreview();
    }
}

/**
 * Add another photo to the batch
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.addAnotherPhoto = function() {
    window.openCamera();
}

/**
 * Cancel batch and close modal
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.cancelBatch = function() {
    if (confirm('Vuoi davvero annullare? Tutte le foto acquisite verranno perse.')) {
        capturedImages = [];
        window.closePreviewModal();
    }
}

/**
 * Close preview modal and reset
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.closePreviewModal = function() {
    const modal = document.getElementById('image-preview-modal');
    modal.classList.remove('active');  // Remove active class for CSS animation
    modal.style.display = 'none';
    capturedImages = [];
}

/**
 * Upload all captured images as a single PDF document
 * EXPOSED TO GLOBAL SCOPE for onclick handlers
 */
window.uploadBatch = async function() {
    if (capturedImages.length === 0) {
        alert('Nessuna immagine da caricare');
        return;
    }

    const documentName = document.getElementById('batch-document-name').value.trim() || 'documento-scansionato';

    // Close modal
    document.getElementById('image-preview-modal').style.display = 'none';

    // Show upload progress
    const progressContainer = document.getElementById('upload-progress-container');
    const progressFill = document.getElementById('upload-progress-fill');
    const progressText = document.getElementById('upload-progress-text');

    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = `Caricamento ${capturedImages.length} foto...`;

    try {
        // Create FormData with all images
        const formData = new FormData();

        capturedImages.forEach((img, index) => {
            // Add document name as filename for first image
            const filename = index === 0
                ? `${documentName}.jpg`
                : `${documentName}_${index + 1}.jpg`;

            const renamedFile = new File([img.file], filename, {
                type: img.file.type,
                lastModified: img.file.lastModified
            });

            formData.append('files', renamedFile);
        });

        // Add document name to metadata
        formData.append('document_name', documentName);
        formData.append('merge_images', 'true');

        // Upload with progress tracking
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = `Caricamento: ${Math.round(percentComplete)}%`;
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200 || xhr.status === 201) {
                progressText.textContent = '✅ Caricamento completato! Il documento è in elaborazione...';
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    capturedImages = [];
                    loadDocuments();
                }, 2000);
            } else {
                progressText.textContent = '❌ Errore durante il caricamento';
                console.error('Upload failed:', xhr.responseText);
            }
        });

        xhr.addEventListener('error', () => {
            progressText.textContent = '❌ Errore di rete';
        });

        xhr.open('POST', '/api/documents/upload-batch');
        xhr.send(formData);

    } catch (error) {
        console.error('Upload error:', error);
        progressText.textContent = '❌ Errore durante il caricamento';
        alert('Errore: ' + error.message);
    }
}

// Auto-reload documents every 30 seconds to check for processing updates
setInterval(() => {
    const hasProcessing = documents.some(d => d.status === 'processing');
    if (hasProcessing) {
        loadDocuments();
    }
}, 30000);

// ============================================================================
// EVENT DELEGATION FOR RENAME BUTTONS
// ============================================================================

// Handle rename button clicks using event delegation
document.addEventListener('click', function(e) {
    // Check if clicked element is a rename button
    if (e.target.closest('.btn-rename')) {
        const btn = e.target.closest('.btn-rename');
        const documentId = btn.dataset.docId;
        const filename = btn.dataset.filename;

        // Call the openRenameModal function defined in dashboard.html
        if (typeof openRenameModal === 'function') {
            openRenameModal(documentId, filename);
        } else {
            console.error('openRenameModal function not found');
        }
    }
});

// ============================================================================
// DEBUG UTILITIES - SYSTEMATIC STATE INSPECTION
// ============================================================================

/**
 * Dump complete camera capture state for debugging
 * EXPOSED TO GLOBAL SCOPE - Call from Eruda console with: window.debugCameraState()
 */
window.debugCameraState = function() {
    const cameraInput = document.getElementById('camera-input');
    const fileInput = document.getElementById('file-input');
    const modal = document.getElementById('image-preview-modal');

    const state = {
        timestamp: new Date().toISOString(),
        capturedImagesCount: capturedImages.length,
        capturedImagesDetails: capturedImages.map((img, idx) => ({
            index: idx,
            fileName: img.file.name,
            fileSize: img.file.size,
            fileType: img.file.type,
            dataUrlLength: img.dataUrl ? img.dataUrl.length : 0,
            dataUrlPreview: img.dataUrl ? img.dataUrl.substring(0, 50) + '...' : null
        })),
        cameraInputElement: {
            exists: !!cameraInput,
            id: cameraInput?.id,
            value: cameraInput?.value,
            filesLength: cameraInput?.files?.length || 0,
            hasChangeListener: true // Set by setupCameraListener()
        },
        fileInputElement: {
            exists: !!fileInput,
            id: fileInput?.id,
            value: fileInput?.value,
            filesLength: fileInput?.files?.length || 0
        },
        modalElement: {
            exists: !!modal,
            display: modal?.style.display,
            hasActiveClass: modal?.classList.contains('active'),
            innerHTML: modal?.innerHTML?.substring(0, 200) + '...' || null
        },
        eventListeners: {
            cameraInputListenerAttached: !!cameraInput,
            fileInputListenerInDashboardHTML: 'See dashboard.html line 384-399'
        },
        globalFunctions: {
            openCamera: typeof window.openCamera,
            handleCameraCapture: typeof handleCameraCapture,
            showBatchPreview: typeof showBatchPreview,
            uploadBatch: typeof window.uploadBatch,
            removeImage: typeof window.removeImage,
            addAnotherPhoto: typeof window.addAnotherPhoto,
            cancelBatch: typeof window.cancelBatch,
            closePreviewModal: typeof window.closePreviewModal
        }
    };

    console.log('='.repeat(80));
    console.log('📊 CAMERA CAPTURE STATE DEBUG DUMP');
    console.log('='.repeat(80));
    console.log(JSON.stringify(state, null, 2));
    console.log('='.repeat(80));

    // Also return for programmatic access
    return state;
};

/**
 * Test camera capture workflow step-by-step
 * EXPOSED TO GLOBAL SCOPE - Call from Eruda console with: window.testCameraWorkflow()
 */
window.testCameraWorkflow = function() {
    console.log('🧪 CAMERA WORKFLOW TEST STARTED');
    console.log('Step 1: Check initial state');

    const initialState = window.debugCameraState();

    console.log('Step 2: Simulating camera button click');
    console.log('MANUAL ACTION REQUIRED: Click the camera button and take a photo');
    console.log('Then run: window.debugCameraState() again to see updated state');

    return {
        message: 'Test initialized. Take a photo, then run window.debugCameraState() to see results',
        initialState: initialState
    };
};

/**
 * Clear all captured images and reset state
 * EXPOSED TO GLOBAL SCOPE - Call from Eruda console with: window.resetCameraState()
 */
window.resetCameraState = function() {
    const before = capturedImages.length;
    capturedImages = [];
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) cameraInput.value = '';

    const modal = document.getElementById('image-preview-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }

    console.log(`✅ Camera state reset. Cleared ${before} images.`);
    return window.debugCameraState();
};

// ============================================================================
// INITIALIZATION - DOMContentLoaded
// ============================================================================

/**
 * Initialize all event listeners and global functions after DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[INIT] DOM Content Loaded - Setting up camera listeners');

    // Setup camera event listener
    setupCameraListener();

    // Verify all global functions are accessible
    console.log('[INIT] Global functions exposed to window:', {
        openCamera: typeof window.openCamera,
        addAnotherPhoto: typeof window.addAnotherPhoto,
        cancelBatch: typeof window.cancelBatch,
        closePreviewModal: typeof window.closePreviewModal,
        uploadBatch: typeof window.uploadBatch,
        removeImage: typeof window.removeImage,
        // Debug utilities
        debugCameraState: typeof window.debugCameraState,
        testCameraWorkflow: typeof window.testCameraWorkflow,
        resetCameraState: typeof window.resetCameraState
    });

    console.log('[INIT] Initialization complete');
    console.log('💡 DEBUG UTILITIES AVAILABLE:');
    console.log('   - window.debugCameraState() - Dump complete camera state');
    console.log('   - window.testCameraWorkflow() - Test camera workflow');
    console.log('   - window.resetCameraState() - Reset camera state');
});
