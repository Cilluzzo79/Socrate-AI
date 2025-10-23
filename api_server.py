"""
Socrate AI - Multi-tenant REST API Server
Flask API with Telegram Login Widget Authentication
"""

from flask import Flask, request, redirect, session, jsonify, render_template, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import escape as html_escape
import hashlib
import hmac
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.database import get_or_create_user, get_user_by_id, init_db
from core.document_operations import (
    get_user_documents,
    get_document_by_id,
    create_document,
    update_document_status,
    delete_document,
    create_chat_session,
    update_chat_session,
    get_user_stats
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# SECURITY: SECRET_KEY validation
secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
if os.getenv('FLASK_ENV') == 'production' and (not secret_key or secret_key == 'dev-secret-key-CHANGE-IN-PRODUCTION'):
    raise ValueError("SECRET_KEY must be set to a strong random value in production!")
app.secret_key = secret_key

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max request size (for PDF uploads)
CORS(app, supports_credentials=True)

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Use Redis in production: os.getenv('REDIS_URL')
    strategy="fixed-window"
)

# ============================================================================
# SECURITY HELPERS
# ============================================================================

def sanitize_for_html(text: str) -> str:
    """
    Sanitize text for safe HTML embedding (XSS prevention).
    Uses MarkupSafe's escape function for comprehensive protection.
    """
    if not text:
        return ""
    return str(html_escape(text))

def validate_integer_param(value: any, param_name: str, min_val: int = None, max_val: int = None, default: int = None) -> int:
    """
    Validate and safely convert integer parameters from request.

    Args:
        value: Input value to validate
        param_name: Parameter name for error messages
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        default: Default value if conversion fails (optional)

    Returns:
        Validated integer value

    Raises:
        ValueError: If validation fails and no default provided
    """
    try:
        result = int(value) if value is not None else default
        if result is None:
            raise ValueError(f"{param_name} is required")

        if min_val is not None and result < min_val:
            result = min_val
        if max_val is not None and result > max_val:
            result = max_val

        return result
    except (TypeError, ValueError) as e:
        if default is not None:
            logger.warning(f"Invalid {param_name}: {value}, using default {default}")
            return default
        raise ValueError(f"{param_name} must be a valid integer")

# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'SocrateAIBot')

# Storage path
STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')


# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def verify_telegram_auth(auth_data: dict) -> bool:
    """
    Verify Telegram Login Widget authentication
    https://core.telegram.org/widgets/login#checking-authorization
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return False

    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    # Create verification string
    data_check_string = '\n'.join([
        f"{k}={v}" for k, v in sorted(auth_data.items())
    ])

    # Calculate hash with bot token
    try:
        secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return calculated_hash == check_hash
    except Exception as e:
        logger.error(f"Error verifying Telegram auth: {e}")
        return False


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)

    return decorated_function


def get_current_user_id() -> Optional[str]:
    """Get current user ID from session"""
    return session.get('user_id')


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page with Telegram Login Widget"""
    if 'user_id' in session:
        return redirect('/dashboard')

    return render_template('index.html', bot_username=BOT_USERNAME)


@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard (after login)"""
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)

    if not user:
        session.clear()
        return redirect('/')

    stats = get_user_stats(user_id)

    return render_template('dashboard.html', user=user, stats=stats)


@app.route('/auth/telegram/callback')
def telegram_auth_callback():
    """
    Telegram Login Widget callback
    Receives: id, first_name, last_name, username, photo_url, auth_date, hash
    """
    auth_data = request.args.to_dict()

    # 1. Verify authenticity
    if not verify_telegram_auth(auth_data.copy()):
        logger.warning(f"Failed authentication attempt: {auth_data.get('id')}")
        return "❌ Authentication failed - Invalid signature", 403

    # 2. Get or create user
    try:
        user = get_or_create_user(
            telegram_id=int(auth_data['id']),
            first_name=auth_data['first_name'],
            last_name=auth_data.get('last_name'),
            username=auth_data.get('username'),
            photo_url=auth_data.get('photo_url')
        )

        # 3. Create session
        session['user_id'] = str(user.id)
        session['telegram_id'] = user.telegram_id
        session['first_name'] = user.first_name

        logger.info(f"User logged in: {user.telegram_id} ({user.first_name})")

        # 4. Redirect to dashboard
        return redirect('/dashboard')

    except Exception as e:
        logger.error(f"Error in auth callback: {e}")
        return f"❌ Authentication error: {str(e)}", 500


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')


# ============================================================================
# USER API
# ============================================================================

@app.route('/api/user/profile')
@require_auth
def get_user_profile():
    """Get current user profile"""
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': str(user.id),
        'telegram_id': user.telegram_id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'photo_url': user.photo_url,
        'subscription_tier': user.subscription_tier,
        'storage_used_mb': round(user.storage_used_mb, 2),
        'storage_quota_mb': user.storage_quota_mb,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    })


@app.route('/api/user/stats')
@require_auth
def get_stats():
    """Get user statistics"""
    user_id = get_current_user_id()
    stats = get_user_stats(user_id)
    return jsonify(stats)


# ============================================================================
# DOCUMENT API
# ============================================================================

@app.route('/api/documents', methods=['GET'])
@require_auth
def list_documents():
    """List user's documents"""
    user_id = get_current_user_id()
    status_filter = request.args.get('status')

    documents = get_user_documents(user_id, status=status_filter)

    return jsonify({
        'documents': [
            {
                'id': str(doc.id),
                'filename': doc.filename,
                'mime_type': doc.mime_type,
                'file_size': doc.file_size,
                'status': doc.status,
                'processing_progress': doc.processing_progress,
                'total_chunks': doc.total_chunks,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            }
            for doc in documents
        ]
    })


@app.route('/api/documents/<document_id>', methods=['GET'])
@require_auth
def get_document(document_id: str):
    """Get specific document with processing status"""
    user_id = get_current_user_id()
    doc = get_document_by_id(document_id, user_id)

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # Get task status if available
    task_status = None
    task_info = None

    if doc.doc_metadata and 'task_id' in doc.doc_metadata:
        try:
            from celery.result import AsyncResult
            task = AsyncResult(doc.doc_metadata['task_id'])

            task_status = task.state
            if task.info:
                task_info = task.info if isinstance(task.info, dict) else {'message': str(task.info)}
        except:
            pass

    # Debug info for metadata availability
    has_r2_metadata = bool(doc.doc_metadata and doc.doc_metadata.get('metadata_r2_key'))
    has_local_metadata = bool(doc.doc_metadata and doc.doc_metadata.get('metadata_file'))

    return jsonify({
        'id': str(doc.id),
        'filename': doc.filename,
        'original_filename': doc.original_filename,
        'mime_type': doc.mime_type,
        'file_size': doc.file_size,
        'status': doc.status,
        'processing_progress': doc.processing_progress,
        'error_message': doc.error_message,
        'language': doc.language,
        'total_chunks': doc.total_chunks,
        'total_tokens': doc.total_tokens,
        'duration_seconds': doc.duration_seconds,
        'page_count': doc.page_count,
        'created_at': doc.created_at.isoformat() if doc.created_at else None,
        'processing_completed_at': doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
        'doc_metadata': doc.doc_metadata,
        'task_status': task_status,
        'task_info': task_info,
        'debug': {
            'has_r2_metadata': has_r2_metadata,
            'has_local_metadata': has_local_metadata,
            'query_ready': has_r2_metadata or has_local_metadata
        }
    })


@app.route('/api/documents/<document_id>/status', methods=['GET'])
@require_auth
def get_document_status(document_id: str):
    """
    Get processing status for a document
    Lightweight endpoint for polling
    """
    user_id = get_current_user_id()
    doc = get_document_by_id(document_id, user_id)

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # Get task status
    task_state = 'UNKNOWN'
    task_progress = doc.processing_progress or 0
    task_message = ''

    if doc.doc_metadata and 'task_id' in doc.doc_metadata:
        try:
            from celery.result import AsyncResult
            task = AsyncResult(doc.doc_metadata['task_id'])

            task_state = task.state

            if task.info and isinstance(task.info, dict):
                task_progress = task.info.get('progress', task_progress)
                task_message = task.info.get('status', '')
        except:
            pass

    return jsonify({
        'document_id': str(doc.id),
        'status': doc.status,
        'progress': task_progress,
        'task_state': task_state,
        'message': task_message or doc.error_message or '',
        'total_chunks': doc.total_chunks,
        'ready': doc.status == 'ready'
    })


@app.route('/api/documents/upload', methods=['POST'])
@require_auth
def upload_document():
    """Upload new document"""
    user_id = get_current_user_id()

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        # Read file
        file_content = file.read()
        file_size = len(file_content)
        filename = file.filename
        mime_type = file.mimetype

        # Generate unique document ID
        import uuid
        doc_id = str(uuid.uuid4())

        # Upload to R2
        from core.s3_storage import upload_file, generate_file_key

        file_key = generate_file_key(user_id, doc_id, filename)
        upload_success = upload_file(file_content, file_key, mime_type)

        if not upload_success:
            logger.error(f"Failed to upload file to R2: {filename}")
            return jsonify({'error': 'Upload to cloud storage failed'}), 500

        logger.info(f"File uploaded to R2: {file_key}")

        # Create document record
        doc = create_document(
            user_id=user_id,
            filename=filename,
            original_filename=filename,
            file_path=file_key,  # Store R2 key instead of local path
            file_size=file_size,
            mime_type=mime_type
        )

        logger.info(f"Document uploaded: {doc.id} by user {user_id}")

        # Trigger async processing with Celery
        # Check if this is an image that requires OCR
        try:
            from core.ocr_processor import is_image_file

            if is_image_file(mime_type):
                # Route to OCR task
                logger.info(f"Image detected: {filename} ({mime_type}) - routing to OCR task")
                from tasks import process_image_ocr_task
                task = process_image_ocr_task.delay(str(doc.id), user_id)
                logger.info(f"OCR task queued: {task.id} for document {doc.id}")
            else:
                # Route to normal document processing
                from tasks import process_document_task
                task = process_document_task.delay(str(doc.id), user_id)
                logger.info(f"Processing task queued: {task.id} for document {doc.id}")

            # Store task ID in document metadata (optional, for tracking)
            from core.document_operations import update_document_status
            update_document_status(
                str(doc.id),
                user_id,
                status='processing',
                doc_metadata={'task_id': task.id}
            )

        except Exception as e:
            logger.error(f"Failed to queue processing task: {e}")
            # Document will remain in 'processing' status
            # User can retry or admin can check

        return jsonify({
            'success': True,
            'document_id': str(doc.id),
            'filename': doc.filename,
            'status': 'processing',
            'message': 'Document uploaded and queued for processing'
        }), 201

    except ValueError as e:
        # Storage quota exceeded
        return jsonify({'error': str(e)}), 413
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({'error': 'Upload failed'}), 500


@app.route('/api/documents/upload-batch', methods=['POST'])
@require_auth
def upload_batch_documents():
    """Upload multiple images and merge them into a single PDF document"""
    user_id = get_current_user_id()

    files = request.files.getlist('files')
    document_name = request.form.get('document_name', f'documento-{datetime.now().strftime("%Y%m%d%H%M%S")}')

    if not files:
        return jsonify({'error': 'No files provided'}), 400

    # ALTERNATIVE A: Limit batch size to 10 images (cost control + performance)
    MAX_BATCH_IMAGES = 10

    if len(files) > MAX_BATCH_IMAGES:
        logger.warning(f"User {user_id} tried to upload {len(files)} images (max {MAX_BATCH_IMAGES})")
        return jsonify({
            'error': f'Puoi caricare massimo {MAX_BATCH_IMAGES} foto per volta. Hai selezionato {len(files)} foto.',
            'max_allowed': MAX_BATCH_IMAGES,
            'images_selected': len(files)
        }), 400

    logger.info(f"Batch upload: {len(files)} images by user {user_id}, document_name: {document_name}")

    try:
        from PIL import Image
        import io
        import uuid
        import tempfile
        from datetime import timedelta

        # FIX 1: IDEMPOTENCY CHECK - Calculate content hash to detect duplicates
        content_hash = hashlib.sha256()
        for file in files:
            file.seek(0)
            content_hash.update(file.read())
            file.seek(0)  # Reset for later reading

        content_fingerprint = content_hash.hexdigest()
        logger.info(f"Content fingerprint: {content_fingerprint[:16]}...")

        # Check for recent duplicate uploads (within 5 minutes)
        from core.database import SessionLocal, Document
        from sqlalchemy import cast, String

        db = SessionLocal()

        try:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

            # Query for duplicate - use proper JSON extraction
            # For PostgreSQL: doc_metadata->>'content_hash'
            # For SQLite: json_extract(doc_metadata, '$.content_hash')
            existing_doc = db.query(Document).filter(
                Document.user_id == user_id,
                cast(Document.doc_metadata['content_hash'], String) == content_fingerprint,
                Document.created_at > five_minutes_ago
            ).first()

            if existing_doc:
                logger.warning(f"Duplicate upload detected for user {user_id}, returning existing document {existing_doc.id}")
                db.close()
                return jsonify({
                    'success': True,
                    'document_id': str(existing_doc.id),
                    'filename': existing_doc.filename,
                    'images_merged': len(files),
                    'status': existing_doc.status,
                    'duplicate': True,
                    'message': 'Documento già in elaborazione'
                }), 200
        finally:
            db.close()

        # Generate unique document ID
        doc_id = str(uuid.uuid4())

        # FIX 2: MEMORY-EFFICIENT PDF GENERATION
        # Process images one at a time, save to temp disk, then create PDF
        logger.info(f"Processing {len(files)} images with memory-efficient method...")

        total_size = 0
        max_size_mb = 50
        max_dimension = 2000  # Max pixels on longest side

        with tempfile.TemporaryDirectory() as temp_dir:
            processed_paths = []

            for idx, file in enumerate(files):
                try:
                    # Read image
                    image_content = file.read()
                    image_size = len(image_content)
                    total_size += image_size

                    # Check cumulative size limit (50MB)
                    if total_size > max_size_mb * 1024 * 1024:
                        logger.error(f"Batch upload exceeds {max_size_mb}MB limit")
                        return jsonify({'error': f'Batch supera il limite di {max_size_mb}MB'}), 413

                    logger.info(f"  Processing image {idx + 1}/{len(files)}: {file.filename} ({image_size} bytes)")

                    # Open with PIL
                    img = Image.open(io.BytesIO(image_content))
                    original_size = img.size

                    # Resize if too large (saves memory and reduces PDF size)
                    if max(img.size) > max_dimension:
                        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                        logger.info(f"    Resized from {original_size} to {img.size}")

                    # Convert to RGB if needed (required for PDF)
                    if img.mode != 'RGB':
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            rgb_img.paste(img, mask=img.split()[3])
                        else:
                            rgb_img.paste(img)
                        img = rgb_img

                    # Save to temp disk (frees memory immediately)
                    temp_path = Path(temp_dir) / f"page_{idx:03d}.jpg"
                    img.save(temp_path, 'JPEG', quality=85, optimize=True)
                    processed_paths.append(str(temp_path))

                    # Free memory immediately
                    del image_content
                    del img

                except Exception as e:
                    logger.error(f"Error processing image {idx + 1} ({file.filename}): {e}")
                    return jsonify({'error': f'Errore elaborazione immagine {idx + 1}: {str(e)}'}), 400

            if not processed_paths:
                return jsonify({'error': 'Nessuna immagine valida da processare'}), 400

            logger.info(f"All images processed, creating PDF from {len(processed_paths)} pages...")

            # ALTERNATIVE A: Apply OCR to images BEFORE creating PDF
            # This allows memvid encoder to use pre-extracted text instead of PyPDF2
            logger.info(f"[ALT-A] Applying OCR to {len(processed_paths)} images in parallel...")

            ocr_texts = []
            ocr_success = True

            try:
                from concurrent.futures import ThreadPoolExecutor
                from core.ocr_processor import extract_text_from_image

                # OCR in parallel (3x faster than sequential)
                with ThreadPoolExecutor(max_workers=min(3, len(processed_paths))) as executor:
                    futures = []

                    for idx, img_path in enumerate(processed_paths):
                        # Read image bytes for OCR
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()

                        # Submit OCR task
                        future = executor.submit(
                            extract_text_from_image,
                            img_bytes,
                            f"page_{idx+1}.jpg"
                        )
                        futures.append(future)

                    # Collect results
                    for idx, future in enumerate(futures):
                        try:
                            ocr_result = future.result(timeout=30)  # 30s timeout per page

                            if ocr_result.get('success') and ocr_result.get('text'):
                                page_text = ocr_result['text']
                                ocr_texts.append(page_text)
                                logger.info(f"[ALT-A] Page {idx+1} OCR: {len(page_text)} chars extracted")
                            else:
                                ocr_texts.append("")
                                logger.warning(f"[ALT-A] Page {idx+1} OCR failed: {ocr_result.get('error', 'Unknown')}")
                        except Exception as e:
                            ocr_texts.append("")
                            logger.error(f"[ALT-A] Page {idx+1} OCR exception: {e}")

                logger.info(f"[ALT-A] OCR complete: {len([t for t in ocr_texts if t])} of {len(ocr_texts)} pages successful")

            except Exception as e:
                logger.error(f"[ALT-A] OCR process failed: {e}")
                logger.info(f"[ALT-A] Falling back to PDF without pre-extracted text")
                ocr_success = False

            # Create PDF from processed images on disk (memory-efficient)
            pdf_buffer = io.BytesIO()

            # Open first image for PDF creation
            first_img = Image.open(processed_paths[0])

            # Load remaining images
            remaining_imgs = [Image.open(path) for path in processed_paths[1:]] if len(processed_paths) > 1 else []

            # Save as PDF
            first_img.save(
                pdf_buffer,
                format='PDF',
                save_all=True,
                append_images=remaining_imgs,
                resolution=100.0,
                quality=85
            )

            # Close images to free memory
            first_img.close()
            for img in remaining_imgs:
                img.close()

            pdf_content = pdf_buffer.getvalue()
            pdf_size = len(pdf_content)

        logger.info(f"Created PDF: {len(processed_paths)} pages, {pdf_size} bytes")

        # Upload PDF to R2
        from core.s3_storage import upload_file, generate_file_key

        pdf_filename = f"{document_name}.pdf"
        file_key = generate_file_key(user_id, doc_id, pdf_filename)
        upload_success = upload_file(pdf_content, file_key, 'application/pdf')

        if not upload_success:
            logger.error(f"Failed to upload merged PDF to R2: {pdf_filename}")
            return jsonify({'error': 'Upload to cloud storage failed'}), 500

        logger.info(f"Merged PDF uploaded to R2: {file_key}")

        # Create document record
        doc = create_document(
            user_id=user_id,
            filename=pdf_filename,
            original_filename=pdf_filename,
            file_path=file_key,
            file_size=pdf_size,
            mime_type='application/pdf'
        )

        logger.info(f"Batch document created: {doc.id} ({len(files)} images merged)")

        # Trigger async processing
        try:
            from tasks import process_document_task
            task = process_document_task.delay(str(doc.id), user_id)
            logger.info(f"Processing task queued: {task.id} for merged document {doc.id}")

            # Store task ID, content hash, and OCR text for idempotency
            from core.document_operations import update_document_status
            update_document_status(
                str(doc.id),
                user_id,
                status='processing',
                doc_metadata={
                    'task_id': task.id,
                    'source_images_count': len(files),
                    'content_hash': content_fingerprint,
                    'ocr_preextracted': ocr_success,  # ALTERNATIVE A: Flag that OCR was done
                    'ocr_texts': ocr_texts if ocr_success else None  # ALTERNATIVE A: Pre-extracted text per page
                }
            )

        except Exception as e:
            logger.error(f"Failed to queue processing task: {e}")

        return jsonify({
            'success': True,
            'document_id': str(doc.id),
            'filename': doc.filename,
            'images_merged': len(files),
            'status': 'processing',
            'message': f'{len(files)} immagini unite in un PDF. Elaborazione in corso...'
        }), 201

    except ValueError as e:
        # Storage quota exceeded
        return jsonify({'error': str(e)}), 413
    except Exception as e:
        logger.error(f"Error in batch upload: {e}", exc_info=True)
        return jsonify({'error': f'Batch upload failed: {str(e)}'}), 500


@app.route('/api/documents/<document_id>', methods=['DELETE'])
@require_auth
def delete_document_endpoint(document_id: str):
    """Delete document and all associated files from R2"""
    user_id = get_current_user_id()

    success = delete_document(document_id, user_id)

    if not success:
        return jsonify({'error': 'Document not found'}), 404

    logger.info(f"Document deleted: {document_id} by user {user_id}")

    return jsonify({'success': True})


@app.route('/api/documents/<document_id>/rename', methods=['PUT'])
@require_auth
def rename_document_endpoint(document_id: str):
    """Rename document in database"""
    user_id = get_current_user_id()
    data = request.json

    if not data or 'new_filename' not in data:
        return jsonify({'error': 'new_filename required'}), 400

    new_name = data['new_filename'].strip()

    if not new_name:
        return jsonify({'error': 'Filename cannot be empty'}), 400

    # Get document to verify ownership and extract extension
    doc = get_document_by_id(document_id, user_id)

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # Extract original file extension
    original_filename = doc.filename
    last_dot_index = original_filename.rfind('.')

    if last_dot_index > 0:
        extension = original_filename[last_dot_index:]  # includes the dot
        new_filename = new_name + extension
    else:
        # No extension in original file
        new_filename = new_name

    try:
        # Update document filename in database
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            doc.filename = new_filename
            doc.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Document renamed: {document_id} from '{original_filename}' to '{new_filename}' by user {user_id}")

            return jsonify({
                'success': True,
                'filename': new_filename
            })

        except Exception as e:
            db.rollback()
            logger.error(f"Error renaming document: {e}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error renaming document {document_id}: {e}")
        return jsonify({'error': 'Rename failed'}), 500


@app.route('/api/admin/cleanup-duplicates', methods=['POST'])
@require_auth
def cleanup_duplicate_documents():
    """
    Admin endpoint to delete all duplicate documents except the most recent one
    Keeps only the latest document for the current user
    """
    user_id = get_current_user_id()

    try:
        from core.database import SessionLocal, Document
        from sqlalchemy import desc

        db = SessionLocal()

        try:
            # Get all documents for user, sorted by created_at descending
            all_docs = db.query(Document).filter_by(
                user_id=user_id
            ).order_by(desc(Document.created_at)).all()

            logger.info(f"Cleanup request: Found {len(all_docs)} documents for user {user_id}")

            if len(all_docs) <= 1:
                db.close()
                return jsonify({
                    'success': True,
                    'message': f'Only {len(all_docs)} document(s) found, nothing to delete',
                    'deleted_count': 0,
                    'remaining_count': len(all_docs)
                })

            # Keep latest, delete the rest
            doc_to_keep = all_docs[0]
            docs_to_delete = all_docs[1:]

            logger.info(f"Keeping latest document: {doc_to_keep.id} ({doc_to_keep.filename})")
            logger.info(f"Deleting {len(docs_to_delete)} old document(s)")

            # Delete old documents (including R2 files)
            deleted_ids = []
            for doc in docs_to_delete:
                try:
                    doc_id = str(doc.id)
                    logger.info(f"Deleting: {doc_id} ({doc.filename}) - created: {doc.created_at}")
                    # Use delete_document to also delete R2 files
                    success = delete_document(doc_id, user_id)
                    if success:
                        deleted_ids.append(doc_id)
                    else:
                        logger.error(f"Failed to delete document {doc_id}")
                except Exception as e:
                    logger.error(f"Error deleting {doc.id}: {e}")

            logger.info(f"Successfully deleted {len(deleted_ids)} document(s)")

            return jsonify({
                'success': True,
                'message': f'Deleted {len(deleted_ids)} old document(s)',
                'deleted_count': len(deleted_ids),
                'deleted_ids': deleted_ids,
                'remaining_count': 1,
                'kept_document': {
                    'id': str(doc_to_keep.id),
                    'filename': doc_to_keep.filename,
                    'created_at': doc_to_keep.created_at.isoformat() if doc_to_keep.created_at else None
                }
            })

        except Exception as e:
            db.rollback()
            logger.error(f"Error during cleanup: {e}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CONTENT GENERATION API (simplified for now)
# ============================================================================

@app.route('/api/query', methods=['POST'])
@require_auth
def custom_query():
    """
    Custom query endpoint with RAG pipeline and specialized commands
    Body: {
        "document_id": "...",
        "query": "...",
        "command_type": "query|quiz|summary|outline|mindmap|analyze",
        "command_params": {...},
        "top_k": 3
    }
    """
    user_id = get_current_user_id()
    data = request.json

    document_id = data.get('document_id')
    query = data.get('query')
    command_type = data.get('command_type', 'query')
    command_params = data.get('command_params', {})
    top_k = data.get('top_k', 5)

    if not document_id or not query:
        return jsonify({'error': 'document_id and query required'}), 400

    # Verify document ownership
    logger.info(f"🔍 Query request for document: {document_id}")
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        logger.error(f"❌ Document not found: {document_id} for user {user_id}")
        return jsonify({'error': 'Document not found'}), 404

    if doc.status != 'ready':
        logger.warning(f"⚠️  Document not ready: {document_id} (status: {doc.status})")
        return jsonify({'error': f'Document not ready (status: {doc.status})'}), 400

    logger.info(f"✅ Document found: {doc.filename} ({doc.id}) - metadata_r2_key: {bool(doc.doc_metadata.get('metadata_r2_key') if doc.doc_metadata else False)}")

    # Get user for tier info
    user = get_user_by_id(user_id)
    user_tier = user.subscription_tier if user else 'free'

    # Create chat session
    chat_session = create_chat_session(
        user_id=user_id,
        document_id=document_id,
        command_type=command_type,
        request_data={'query': query, 'top_k': top_k, 'command_params': command_params},
        channel='web_app'
    )

    try:
        # Get metadata source from document (prefer R2, fallback to local path)
        metadata_r2_key = doc.doc_metadata.get('metadata_r2_key') if doc.doc_metadata else None
        metadata_file = doc.doc_metadata.get('metadata_file') if doc.doc_metadata else None

        if not metadata_r2_key and not metadata_file:
            logger.error(f"No metadata source in document {document_id}")
            return jsonify({
                'error': 'Document metadata not found',
                'help': 'Document may need to be reprocessed'
            }), 500

        # Process query using RAG pipeline
        from core.query_engine import query_document

        result = query_document(
            query=query,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=top_k,
            user_tier=user_tier,
            query_type=command_type,
            command_params=command_params
        )

        # Update session with response
        update_chat_session(
            session_id=str(chat_session.id),
            response_data={'answer': result['answer'], 'sources': result.get('sources', [])},
            success=result['success'],
            input_tokens=result.get('metadata', {}).get('input_tokens'),
            output_tokens=result.get('metadata', {}).get('output_tokens'),
            cost_usd=calculate_cost(
                result.get('metadata', {}).get('input_tokens', 0),
                result.get('metadata', {}).get('output_tokens', 0),
                'gpt-5-nano'
            ),
            model_used=result.get('metadata', {}).get('model', 'gpt-5-nano')
        )

        return jsonify({
            'success': result['success'],
            'session_id': str(chat_session.id),
            'answer': result['answer'],
            'sources': result.get('sources', []),
            'metadata': result.get('metadata', {})
        })

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)

        # Update session with error
        update_chat_session(
            session_id=str(chat_session.id),
            response_data={'error': str(e)},
            success=False
        )

        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': str(chat_session.id)
        }), 500


@app.route('/api/documents/<document_id>/chat', methods=['POST'])
@require_auth
def document_chat(document_id):
    """
    Persistent chat interface with conversation history

    Body: {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": "..."}  // Latest query
        ],
        "top_k": 5  // Optional
    }

    Returns:
        {
            "success": true,
            "messages": [...],  // Full conversation history
            "session_id": "...",
            "metadata": {...}
        }
    """
    user_id = get_current_user_id()
    data = request.json

    messages = data.get('messages', [])
    top_k = data.get('top_k', 5)

    if not messages or len(messages) == 0:
        return jsonify({'error': 'messages array required'}), 400

    # SECURITY FIX: Validate and sanitize all messages
    VALID_ROLES = {'user', 'assistant'}
    MAX_MESSAGE_LENGTH = 10000  # 10K chars per message
    MAX_MESSAGES = 100  # Limit conversation length
    MAX_TOTAL_SIZE = 100000  # 100KB total conversation size

    if len(messages) > MAX_MESSAGES:
        return jsonify({'error': f'Too many messages (max {MAX_MESSAGES})'}), 413

    # Calculate total size and validate messages
    import sys
    total_size = sys.getsizeof(json.dumps(messages))
    if total_size > MAX_TOTAL_SIZE:
        return jsonify({'error': 'Conversation size too large'}), 413

    # Sanitize and validate each message
    sanitized_messages = []
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')

        # Validate role
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid message role: {role}'}), 400

        # Validate content length
        if len(content) > MAX_MESSAGE_LENGTH:
            return jsonify({'error': f'Message too long (max {MAX_MESSAGE_LENGTH} chars)'}), 400

        # Sanitize content (strip HTML tags, prevent XSS)
        # Use simple text escaping - we want plain text only
        sanitized_content = content.replace('<', '&lt;').replace('>', '&gt;').strip()

        sanitized_messages.append({
            'role': role,
            'content': sanitized_content
        })

    # Replace messages with sanitized version
    messages = sanitized_messages

    # Extract latest user query
    latest_message = messages[-1]
    if latest_message.get('role') != 'user':
        return jsonify({'error': 'Last message must be from user'}), 400

    query = latest_message.get('content', '')
    if not query.strip():
        return jsonify({'error': 'Query cannot be empty'}), 400

    # Verify document ownership
    logger.info(f"💬 Chat request for document: {document_id}")
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        logger.error(f"❌ Document not found: {document_id} for user {user_id}")
        return jsonify({'error': 'Document not found'}), 404

    if doc.status != 'ready':
        logger.warning(f"⚠️  Document not ready: {document_id} (status: {doc.status})")
        return jsonify({'error': f'Document not ready (status: {doc.status})'}), 400

    logger.info(f"✅ Document found: {doc.filename} ({doc.id})")

    # Get user for tier info
    user = get_user_by_id(user_id)
    user_tier = user.subscription_tier if user else 'free'

    # Build conversation context from history (exclude latest query)
    # PERFORMANCE FIX: Use list comprehension and join instead of string concatenation
    conversation_context = ""
    if len(messages) > 1:
        context_messages = messages[:-1]  # All except latest
        context_parts = []
        for msg in context_messages[-6:]:  # Last 3 turns (6 messages: 3 user + 3 assistant)
            role_label = "Utente" if msg['role'] == 'user' else "Assistente"
            context_parts.append(f"{role_label}: {msg['content']}")
        conversation_context = "\n".join(context_parts)

    # Create chat session
    chat_session = create_chat_session(
        user_id=user_id,
        document_id=document_id,
        command_type='chat',
        request_data={
            'query': query,
            'conversation_history': messages[:-1],  # Store previous messages
            'top_k': top_k
        },
        channel='web_app'
    )

    try:
        # Get metadata source from document
        metadata_r2_key = doc.doc_metadata.get('metadata_r2_key') if doc.doc_metadata else None
        metadata_file = doc.doc_metadata.get('metadata_file') if doc.doc_metadata else None

        if not metadata_r2_key and not metadata_file:
            logger.error(f"No metadata source in document {document_id}")
            return jsonify({
                'error': 'Document metadata not found',
                'help': 'Document may need to be reprocessed'
            }), 500

        # Build enhanced query with conversation context
        enhanced_query = query
        if conversation_context:
            enhanced_query = f"""Conversazione precedente:
{conversation_context}

Nuova domanda dell'utente: {query}

Rispondi alla nuova domanda tenendo conto del contesto della conversazione."""

        # Process query using RAG pipeline
        from core.query_engine import query_document

        result = query_document(
            query=enhanced_query,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=top_k,
            user_tier=user_tier,
            query_type='chat',
            command_params={}
        )

        # Build updated messages array
        updated_messages = messages + [{
            'role': 'assistant',
            'content': result['answer']
        }]

        # Update session with response
        update_chat_session(
            session_id=str(chat_session.id),
            response_data={
                'answer': result['answer'],
                'sources': result.get('sources', []),
                'messages': updated_messages
            },
            success=result['success'],
            input_tokens=result.get('metadata', {}).get('input_tokens'),
            output_tokens=result.get('metadata', {}).get('output_tokens'),
            cost_usd=calculate_cost(
                result.get('metadata', {}).get('input_tokens', 0),
                result.get('metadata', {}).get('output_tokens', 0),
                'gpt-5-nano'
            ),
            model_used=result.get('metadata', {}).get('model', 'gpt-5-nano')
        )

        return jsonify({
            'success': result['success'],
            'session_id': str(chat_session.id),
            'messages': updated_messages,  # Full conversation history
            'sources': result.get('sources', []),
            'metadata': result.get('metadata', {})
        })

    except Exception as e:
        logger.error(f"Error processing chat for session {chat_session.id}: {e}", exc_info=True)

        # SECURITY FIX: Don't expose internal errors to client
        error_message = "An error occurred processing your request. Please try again."
        if isinstance(e, (ValueError, KeyError, TypeError)):
            error_message = "Invalid request format"
        elif isinstance(e, FileNotFoundError):
            error_message = "Document metadata not found"

        # Update session with error (store full error internally)
        update_chat_session(
            session_id=str(chat_session.id),
            response_data={'error': str(e)},  # Full error for logging
            success=False
        )

        return jsonify({
            'success': False,
            'error': error_message,  # Sanitized error for client
            'session_id': str(chat_session.id)
        }), 500


# ============================================================================
# ADVANCED DOCUMENT TOOLS ENDPOINTS
# ============================================================================

@app.route('/api/tools/<document_id>/mindmap', methods=['POST'])
@limiter.limit("5 per minute")  # SECURITY: Rate limit expensive LLM operations
@require_auth
def generate_mindmap_tool(document_id):
    """
    Generate interactive mindmap visualization using Mermaid.js

    Body:
        {
            "topic": "Specific topic" (optional - if empty, creates general overview),
            "depth": 3 (2-4, optional, default 3)
        }

    Returns:
        HTML page with Mermaid mindmap visualization
    """
    user_id = get_current_user_id()

    try:
        from core.visualizers import get_mermaid_mindmap_prompt, parse_simple_mindmap, generate_mermaid_mindmap_html

        # Get document
        document = get_document_by_id(document_id, user_id)
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # SECURITY: Validate and sanitize inputs
        data = request.json or {}
        topic_raw = data.get('topic', '').strip()
        topic = sanitize_for_html(topic_raw)[:200]  # Limit length + sanitize

        # SECURITY: Robust integer validation
        try:
            depth = validate_integer_param(data.get('depth'), 'depth', min_val=2, max_val=4, default=3)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        # SECURITY: Sanitize document filename for HTML embedding
        safe_filename = sanitize_for_html(document.filename)

        # Get mindmap prompt
        mindmap_prompt = get_mermaid_mindmap_prompt(depth_level=depth, central_concept=topic if topic else None)

        # Query document using RAG
        metadata_file = document.file_path
        metadata_r2_key = document.r2_key

        user_tier = 'premium'  # TODO: Get from user settings

        result = query_document(
            query=mindmap_prompt,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=15,  # More context for mind maps
            user_tier=user_tier,
            query_type='mindmap',
            command_params={'depth': depth, 'topic': topic}
        )

        if not result.get('success'):
            error_msg = result.get('error', 'Failed to generate mindmap')
            logger.warning(f"Mindmap generation failed: {error_msg}")
            return jsonify({'error': 'Failed to generate mindmap'}), 500

        # Parse LLM response
        mindmap_data = parse_simple_mindmap(result['answer'])

        # Generate HTML with sanitized filename
        html = generate_mermaid_mindmap_html(mindmap_data, safe_filename)

        # Return HTML directly
        from flask import Response
        return Response(html, mimetype='text/html')

    except ValueError as e:
        logger.warning(f"Validation error in mindmap: {e}")
        return jsonify({'error': str(e)}), 400
    except KeyError as e:
        logger.error(f"Missing required data in mindmap: {e}")
        return jsonify({'error': 'Invalid request format'}), 400
    except Exception as e:
        logger.error(f"Unexpected error generating mindmap: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/tools/<document_id>/outline', methods=['POST'])
@require_auth
def generate_outline_tool(document_id):
    """
    Generate interactive outline visualization with accordion layout

    Body:
        {
            "type": "hierarchical|chronological|thematic" (default: hierarchical),
            "detail_level": "brief|medium|detailed" (default: medium),
            "topic": "Specific topic" (optional)
        }

    Returns:
        HTML page with interactive outline
    """
    user_id = get_current_user_id()

    try:
        from core.visualizers import generate_outline_html, parse_outline_text, get_outline_visualizer_prompt
        from core.content_generators import generate_outline_prompt

        # Get document
        document = get_document_by_id(document_id, user_id)
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Get request parameters
        data = request.json or {}
        outline_type = data.get('type', 'hierarchical')
        detail_level = data.get('detail_level', 'medium')
        topic = data.get('topic', '').strip()

        # Build outline prompt
        outline_params = {
            'outline_type': outline_type,
            'detail_level': detail_level,
            'focus_area': topic if topic else 'L\'intero documento'
        }

        outline_prompt = generate_outline_prompt(**outline_params)

        # Query document using RAG
        metadata_file = document.file_path
        metadata_r2_key = document.r2_key
        user_tier = 'premium'

        result = query_document(
            query=outline_prompt,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=20,  # More context for outlines
            user_tier=user_tier,
            query_type='outline',
            command_params=outline_params
        )

        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to generate outline')}), 500

        # Parse LLM response
        outline_data = parse_outline_text(result['answer'])

        # Generate HTML
        html = generate_outline_html(outline_data, document.filename, outline_type, detail_level)

        # Return HTML directly
        from flask import Response
        return Response(html, mimetype='text/html')

    except Exception as e:
        logger.error(f"Error generating outline: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate outline'}), 500


@app.route('/api/tools/<document_id>/quiz', methods=['POST'])
@require_auth
def generate_quiz_tool(document_id):
    """
    Generate interactive quiz with flip cards

    Body:
        {
            "type": "multiple_choice|true_false|short_answer|mixed" (default: mixed),
            "num_questions": 10 (default),
            "difficulty": "easy|medium|hard" (default: medium),
            "topic": "Specific topic" (optional)
        }

    Returns:
        HTML page with interactive quiz cards
    """
    user_id = get_current_user_id()

    try:
        from core.visualizers import generate_quiz_cards_html
        from core.content_generators import generate_quiz_prompt

        # Get document
        document = get_document_by_id(document_id, user_id)
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Get request parameters
        data = request.json or {}
        quiz_type = data.get('type', 'mixed')
        num_questions = int(data.get('num_questions', 10))
        difficulty = data.get('difficulty', 'medium')
        topic = data.get('topic', '').strip()

        # Build quiz config
        quiz_config = {
            'quiz_type': quiz_type,
            'num_questions': num_questions,
            'difficulty': difficulty,
            'focus_area': topic if topic else 'L\'intero documento',
            'type': quiz_type
        }

        quiz_prompt = generate_quiz_prompt(**quiz_config)

        # Query document using RAG
        metadata_file = document.file_path
        metadata_r2_key = document.r2_key
        user_tier = 'premium'

        result = query_document(
            query=quiz_prompt,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=15,
            user_tier=user_tier,
            query_type='quiz',
            command_params=quiz_config
        )

        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to generate quiz')}), 500

        # Generate HTML with quiz cards
        html = generate_quiz_cards_html(result['answer'], document.filename, quiz_config)

        # Return HTML directly
        from flask import Response
        return Response(html, mimetype='text/html')

    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate quiz'}), 500


@app.route('/api/tools/<document_id>/summary', methods=['POST'])
@require_auth
def generate_summary_tool(document_id):
    """
    Generate document summary

    Body:
        {
            "length": "brief|medium|detailed" (default: medium),
            "topic": "Specific topic" (optional - for focused summaries)
        }

    Returns:
        JSON with summary text
    """
    user_id = get_current_user_id()

    try:
        from core.content_generators import generate_summary_prompt

        # Get document
        document = get_document_by_id(document_id, user_id)
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Get request parameters
        data = request.json or {}
        length = data.get('length', 'medium')
        topic = data.get('topic', '').strip()

        # Build summary prompt
        summary_params = {
            'summary_length': length,
            'focus_area': topic if topic else 'L\'intero documento'
        }

        summary_prompt = generate_summary_prompt(**summary_params)

        # Query document using RAG
        metadata_file = document.file_path
        metadata_r2_key = document.r2_key
        user_tier = 'premium'

        result = query_document(
            query=summary_prompt,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=15,
            user_tier=user_tier,
            query_type='summary',
            command_params=summary_params
        )

        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to generate summary')}), 500

        return jsonify({
            'success': True,
            'summary': result['answer'],
            'metadata': result.get('metadata', {})
        })

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate summary'}), 500


@app.route('/api/tools/<document_id>/analyze', methods=['POST'])
@require_auth
def generate_analysis_tool(document_id):
    """
    Generate custom analysis based on user-specified theme/question

    Body:
        {
            "theme": "Analysis theme/question",
            "focus": "specific|comprehensive" (default: comprehensive)
        }

    Returns:
        JSON with analysis text
    """
    user_id = get_current_user_id()

    try:
        from core.content_generators import generate_analysis_prompt

        # Get document
        document = get_document_by_id(document_id, user_id)
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Get request parameters
        data = request.json or {}
        theme = data.get('theme', '').strip()

        if not theme:
            return jsonify({'error': 'Analysis theme is required'}), 400

        focus = data.get('focus', 'comprehensive')

        # Build analysis prompt
        analysis_params = {
            'analysis_theme': theme,
            'focus_type': focus
        }

        analysis_prompt = generate_analysis_prompt(**analysis_params)

        # Query document using RAG
        metadata_file = document.file_path
        metadata_r2_key = document.r2_key
        user_tier = 'premium'

        result = query_document(
            query=analysis_prompt,
            metadata_file=metadata_file,
            metadata_r2_key=metadata_r2_key,
            top_k=20,  # More context for analysis
            user_tier=user_tier,
            query_type='analyze',
            command_params=analysis_params
        )

        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to generate analysis')}), 500

        return jsonify({
            'success': True,
            'analysis': result['answer'],
            'theme': theme,
            'metadata': result.get('metadata', {})
        })

    except Exception as e:
        logger.error(f"Error generating analysis: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate analysis'}), 500


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate cost for a query based on token usage

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name

    Returns:
        Cost in USD
    """
    # Pricing per million tokens (update as needed)
    pricing = {
        'gpt-5-nano': {'input': 0.10, 'output': 0.30},  # Placeholder - update with real pricing
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 2.50, 'output': 10.00}
    }

    model_pricing = pricing.get(model, pricing['gpt-4o-mini'])

    cost_input = (input_tokens / 1_000_000) * model_pricing['input']
    cost_output = (output_tokens / 1_000_000) * model_pricing['output']

    return cost_input + cost_output


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/admin/cleanup-orphaned-r2', methods=['POST'])
@require_auth
def cleanup_orphaned_r2():
    """
    Admin endpoint to cleanup orphaned R2 files
    Body: {
        "dry_run": true  # Set to false to actually delete files
    }
    """
    user_id = get_current_user_id()
    data = request.json or {}
    dry_run = data.get('dry_run', True)

    try:
        from core.database import SessionLocal, Document
        from core.s3_storage import list_r2_files, delete_file
        from typing import Set, List

        logger.info(f"🧹 Cleanup orphaned R2 files - dry_run={dry_run}")

        # Step 1: Get valid R2 keys from database
        db = SessionLocal()
        valid_keys = set()

        try:
            documents = db.query(Document).all()
            logger.info(f"Found {len(documents)} documents in database")

            for doc in documents:
                # Collect all R2 keys from document records
                if doc.file_path and '/' in doc.file_path:
                    valid_keys.add(doc.file_path)

                if doc.doc_metadata:
                    metadata_r2_key = doc.doc_metadata.get('metadata_r2_key')
                    if metadata_r2_key and metadata_r2_key != 'inline' and '/' in metadata_r2_key:
                        valid_keys.add(metadata_r2_key)

                    video_r2_key = doc.doc_metadata.get('video_r2_key')
                    if video_r2_key and '/' in video_r2_key:
                        valid_keys.add(video_r2_key)

                    embeddings_r2_key = doc.doc_metadata.get('embeddings_r2_key')
                    if embeddings_r2_key and embeddings_r2_key != 'inline' and '/' in embeddings_r2_key:
                        valid_keys.add(embeddings_r2_key)

            logger.info(f"Found {len(valid_keys)} valid R2 keys in database")
        finally:
            db.close()

        # Step 2: Get all files from R2
        logger.info("Listing all files on R2...")
        all_files = list_r2_files()
        logger.info(f"Found {len(all_files)} files on R2")

        if not all_files:
            return jsonify({
                'success': True,
                'message': 'No files found on R2',
                'orphaned_count': 0
            })

        # Step 3: Find orphaned files
        orphaned = []
        for r2_key in all_files:
            if r2_key not in valid_keys:
                orphaned.append(r2_key)

        logger.info(f"Found {len(orphaned)} orphaned files")

        if not orphaned:
            return jsonify({
                'success': True,
                'message': 'No orphaned files found',
                'orphaned_count': 0,
                'total_files': len(all_files),
                'valid_files': len(valid_keys)
            })

        # Step 4: Delete or report
        if dry_run:
            return jsonify({
                'success': True,
                'message': f'DRY RUN: Would delete {len(orphaned)} orphaned files',
                'orphaned_count': len(orphaned),
                'orphaned_files': orphaned[:50],  # Limit to first 50 for response
                'total_orphaned': len(orphaned),
                'help': 'Set dry_run=false to actually delete these files'
            })
        else:
            # Actually delete
            deleted_count = 0
            failed_count = 0

            for r2_key in orphaned:
                try:
                    success = delete_file(r2_key)
                    if success:
                        logger.info(f"✅ Deleted: {r2_key}")
                        deleted_count += 1
                    else:
                        logger.warning(f"⚠️  Failed to delete: {r2_key}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"❌ Error deleting {r2_key}: {e}")
                    failed_count += 1

            return jsonify({
                'success': True,
                'message': f'Cleanup complete: deleted {deleted_count} files, {failed_count} failures',
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'total_orphaned': len(orphaned)
            })

    except Exception as e:
        logger.error(f"Error during orphaned R2 cleanup: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/check-r2-storage', methods=['GET'])
@require_auth
def check_r2_storage():
    """
    Admin endpoint to diagnose R2 storage usage
    Checks for object versions, delete markers, and incomplete multipart uploads
    """
    user_id = get_current_user_id()

    try:
        from core.s3_storage import get_s3_client, R2_BUCKET_NAME
        from botocore.exceptions import ClientError

        client = get_s3_client()

        logger.info(f"🔍 Checking R2 storage for bucket: {R2_BUCKET_NAME}")

        # Check 1: List all object versions (current + old versions)
        logger.info("Step 1: Listing all object versions...")

        current_objects = []
        old_versions = []
        delete_markers = []
        total_size = 0

        try:
            paginator = client.get_paginator('list_object_versions')

            for page in paginator.paginate(Bucket=R2_BUCKET_NAME):
                # Current and old versions
                if 'Versions' in page:
                    for version in page['Versions']:
                        size_mb = version['Size'] / (1024 * 1024)
                        total_size += version['Size']

                        obj_info = {
                            'key': version['Key'],
                            'version_id': version['VersionId'],
                            'is_latest': version['IsLatest'],
                            'size': version['Size'],
                            'size_mb': round(size_mb, 2),
                            'last_modified': version['LastModified'].isoformat()
                        }

                        if version['IsLatest']:
                            current_objects.append(obj_info)
                        else:
                            old_versions.append(obj_info)

                # Delete markers
                if 'DeleteMarkers' in page:
                    for marker in page['DeleteMarkers']:
                        delete_markers.append({
                            'key': marker['Key'],
                            'version_id': marker['VersionId'],
                            'is_latest': marker['IsLatest'],
                            'last_modified': marker['LastModified'].isoformat()
                        })

            logger.info(f"✅ Found {len(current_objects)} current objects, {len(old_versions)} old versions, {len(delete_markers)} delete markers")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                return jsonify({
                    'success': False,
                    'error': 'Bucket not found',
                    'bucket_name': R2_BUCKET_NAME
                }), 404
            elif error_code == 'NotImplemented':
                logger.warning("Object versioning API not available - checking simple listing")
                # Fallback: versioning not enabled, use simple listing
                old_versions = []
                delete_markers = []
                # Will be populated from simple list below

        # Check 2: List incomplete multipart uploads
        logger.info("Step 2: Checking incomplete multipart uploads...")

        incomplete_uploads = []
        try:
            multipart_paginator = client.get_paginator('list_multipart_uploads')

            for page in multipart_paginator.paginate(Bucket=R2_BUCKET_NAME):
                if 'Uploads' in page:
                    for upload in page['Uploads']:
                        incomplete_uploads.append({
                            'key': upload['Key'],
                            'upload_id': upload['UploadId'],
                            'initiated': upload['Initiated'].isoformat() if 'Initiated' in upload else None
                        })

            logger.info(f"✅ Found {len(incomplete_uploads)} incomplete multipart uploads")

        except ClientError as e:
            logger.warning(f"Could not list multipart uploads: {e}")

        # Check 3: Simple object listing (for comparison)
        if not current_objects:  # If versioning check failed, use simple listing
            logger.info("Step 3: Using simple object listing...")

            simple_paginator = client.get_paginator('list_objects_v2')
            for page in simple_paginator.paginate(Bucket=R2_BUCKET_NAME):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        size_mb = obj['Size'] / (1024 * 1024)
                        total_size += obj['Size']

                        current_objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'size_mb': round(size_mb, 2),
                            'last_modified': obj['LastModified'].isoformat()
                        })

        # Calculate totals
        total_size_mb = total_size / (1024 * 1024)
        current_size = sum(obj['size'] for obj in current_objects)
        current_size_mb = current_size / (1024 * 1024)
        old_versions_size = sum(obj['size'] for obj in old_versions)
        old_versions_size_mb = old_versions_size / (1024 * 1024)

        # Summary
        summary = {
            'total_objects': len(current_objects),
            'total_old_versions': len(old_versions),
            'total_delete_markers': len(delete_markers),
            'total_incomplete_uploads': len(incomplete_uploads),
            'current_size_mb': round(current_size_mb, 2),
            'old_versions_size_mb': round(old_versions_size_mb, 2),
            'total_size_mb': round(total_size_mb, 2)
        }

        # Recommendations
        recommendations = []

        if old_versions:
            recommendations.append({
                'issue': 'Old object versions detected',
                'count': len(old_versions),
                'size_mb': round(old_versions_size_mb, 2),
                'solution': 'Object versioning is enabled. Old versions are kept after deletion.',
                'action': 'Run cleanup script to delete old versions or disable versioning in Cloudflare dashboard'
            })

        if delete_markers:
            recommendations.append({
                'issue': 'Delete markers found',
                'count': len(delete_markers),
                'solution': 'These are versioning markers that indicate deleted files (but old versions remain)',
                'action': 'Delete these markers and their associated old versions'
            })

        if incomplete_uploads:
            recommendations.append({
                'issue': 'Incomplete multipart uploads',
                'count': len(incomplete_uploads),
                'solution': 'These are failed/incomplete uploads that consume storage',
                'action': 'Run abort_incomplete_multipart_uploads to clean them up'
            })

        return jsonify({
            'success': True,
            'bucket_name': R2_BUCKET_NAME,
            'summary': summary,
            'recommendations': recommendations,
            'current_objects': current_objects[:20],  # Limit to first 20
            'old_versions': old_versions[:20],
            'delete_markers': delete_markers[:20],
            'incomplete_uploads': incomplete_uploads,
            'help': {
                'current_objects_shown': min(20, len(current_objects)),
                'old_versions_shown': min(20, len(old_versions)),
                'delete_markers_shown': min(20, len(delete_markers))
            }
        })

    except Exception as e:
        logger.error(f"Error checking R2 storage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Socrate AI Multi-tenant API',
        'version': '1.0.0'
    })


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize():
    """Initialize database and app resources"""
    logger.info("Initializing Socrate AI API...")
    try:
        init_db()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Application will continue but database operations may fail")

# Initialize at module load time (for gunicorn workers)
try:
    initialize()
except Exception as e:
    logger.error(f"Initialization error: {e}")


if __name__ == '__main__':
    # Get port from environment (Railway provides this)
    port = int(os.getenv('PORT', 5000))

    logger.info(f"🚀 Starting Socrate AI API server on port {port}")
    logger.info(f"   Bot Username: {BOT_USERNAME}")
    logger.info(f"   Storage Path: {STORAGE_PATH}")

    # Run server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
