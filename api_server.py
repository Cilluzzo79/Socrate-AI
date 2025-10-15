"""
Socrate AI - Multi-tenant REST API Server
Flask API with Telegram Login Widget Authentication
"""

from flask import Flask, request, redirect, session, jsonify, render_template, send_file
from flask_cors import CORS
import hashlib
import hmac
import os
import sys
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
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
CORS(app, supports_credentials=True)

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
        'task_info': task_info
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
        try:
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


@app.route('/api/documents/<document_id>', methods=['DELETE'])
@require_auth
def delete_document_endpoint(document_id: str):
    """Delete document"""
    user_id = get_current_user_id()

    success = delete_document(document_id, user_id)

    if not success:
        return jsonify({'error': 'Document not found'}), 404

    # TODO: Also delete physical files

    logger.info(f"Document deleted: {document_id} by user {user_id}")

    return jsonify({'success': True})


# ============================================================================
# CONTENT GENERATION API (simplified for now)
# ============================================================================

@app.route('/api/query', methods=['POST'])
@require_auth
def custom_query():
    """
    Custom query endpoint with RAG pipeline
    Body: { "document_id": "...", "query": "...", "top_k": 3 }
    """
    user_id = get_current_user_id()
    data = request.json

    document_id = data.get('document_id')
    query = data.get('query')
    top_k = data.get('top_k', 3)

    if not document_id or not query:
        return jsonify({'error': 'document_id and query required'}), 400

    # Verify document ownership
    doc = get_document_by_id(document_id, user_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    if doc.status != 'ready':
        return jsonify({'error': f'Document not ready (status: {doc.status})'}), 400

    # Get user for tier info
    user = get_user_by_id(user_id)
    user_tier = user.subscription_tier if user else 'free'

    # Create chat session
    chat_session = create_chat_session(
        user_id=user_id,
        document_id=document_id,
        command_type='query',
        request_data={'query': query, 'top_k': top_k},
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
            user_tier=user_tier
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
