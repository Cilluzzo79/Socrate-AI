/**
 * Socrate AI - Dashboard JavaScript
 * Handles document management, upload, and interactions
 */

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
                    <button class="btn-rename" onclick="openRenameModal('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')">✏️</button>
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
    document.getElementById('upload-modal').classList.remove('active');
    document.getElementById('upload-form').reset();
    document.getElementById('upload-progress').style.display = 'none';
    document.getElementById('progress-fill').style.width = '0%';
}

document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) {
        alert('Seleziona un file');
        return;
    }

    // Show progress
    const progressDiv = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Caricamento...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        const data = await response.json();
        const documentId = data.document_id;

        progressFill.style.width = '30%';
        progressText.textContent = 'Elaborazione in corso...';

        // Start polling for processing status
        await pollDocumentStatus(documentId, progressFill, progressText);

        // Processing complete
        progressText.textContent = '✅ Documento pronto!';

        setTimeout(() => {
            closeUploadModal();
            loadDocuments(); // Reload documents
        }, 1500);

    } catch (error) {
        console.error('Upload error:', error);
        progressText.textContent = `❌ Errore: ${error.message}`;
        progressFill.style.width = '0%';
    }
});

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
// CAMERA CAPTURE FUNCTIONS
// ============================================================================

let capturedImageFile = null;

/**
 * Open camera input to capture photo
 */
function openCamera() {
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) {
        cameraInput.click();
    }
}

/**
 * Handle camera capture - set up event listener
 */
document.getElementById('camera-input')?.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
        handleCameraCapture(file);
    }
});

/**
 * Process captured image and show preview
 */
function handleCameraCapture(file) {
    capturedImageFile = file;

    // Create preview URL
    const reader = new FileReader();
    reader.onload = function(e) {
        showImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);
}

/**
 * Show image preview modal with rename option
 */
function showImagePreview(imageDataUrl) {
    const modal = document.getElementById('image-preview-modal');
    const previewImage = document.getElementById('preview-image');
    const filenameInput = document.getElementById('preview-filename');

    // Set preview image
    previewImage.src = imageDataUrl;

    // Generate default filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    filenameInput.value = `foto-${timestamp}`;

    // Show modal
    modal.style.display = 'flex';
}

/**
 * Close preview modal and reset camera input
 */
function closePreviewModal() {
    const modal = document.getElementById('image-preview-modal');
    const cameraInput = document.getElementById('camera-input');

    // Hide modal
    modal.style.display = 'none';

    // Reset camera input to allow retaking
    cameraInput.value = '';
    capturedImageFile = null;

    // User controls when to take another photo - no auto-reopen
}

/**
 * Confirm upload with custom filename
 */
function confirmUpload() {
    if (!capturedImageFile) {
        alert('Nessuna immagine da caricare');
        return;
    }

    const filenameInput = document.getElementById('preview-filename');
    let customName = filenameInput.value.trim();

    // Add .jpg extension if not present
    if (!customName.match(/\.(jpg|jpeg|png)$/i)) {
        customName += '.jpg';
    }

    // Create renamed file
    const renamedFile = new File([capturedImageFile], customName, {
        type: capturedImageFile.type,
        lastModified: capturedImageFile.lastModified
    });

    // Close modal
    document.getElementById('image-preview-modal').style.display = 'none';

    // Upload file using existing handler
    handleFileUpload(renamedFile);

    // Reset
    document.getElementById('camera-input').value = '';
    capturedImageFile = null;
}

// Auto-reload documents every 30 seconds to check for processing updates
setInterval(() => {
    const hasProcessing = documents.some(d => d.status === 'processing');
    if (hasProcessing) {
        loadDocuments();
    }
}, 30000);
