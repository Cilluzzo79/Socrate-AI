"""
Celery Tasks for Async Document Processing
Handles document encoding, processing, and cleanup
"""

import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
import logging

from celery_config import celery_app
from core.database import SessionLocal
from core.document_operations import get_document_by_id, update_document_status

# Setup logging
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.process_document_task')
def process_document_task(self, document_id: str, user_id: str):
    """
    Process uploaded document with memvid encoder

    Args:
        document_id: Document UUID
        user_id: User UUID (for ownership verification)

    Returns:
        dict: Processing result with status and metadata
    """
    logger.info(f"Starting document processing: {document_id} for user {user_id}")

    # Update task state
    self.update_state(
        state='PROCESSING',
        meta={'status': 'Initializing', 'progress': 0}
    )

    try:
        # 1. Get document from database
        doc = get_document_by_id(document_id, user_id)
        if not doc:
            logger.error(f"Document {document_id} not found or unauthorized")
            return {
                'success': False,
                'error': 'Document not found or unauthorized'
            }

        logger.info(f"Processing document: {doc.filename} ({doc.file_path})")

        # Update document status to processing
        update_document_status(
            document_id,
            user_id,
            status='processing',
            processing_progress=5
        )

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Reading file', 'progress': 10}
        )

        # 2. Download file from R2
        from core.s3_storage import download_file

        logger.info(f"Downloading file from R2: {doc.file_path}")
        file_data = download_file(doc.file_path)  # file_path contains R2 key

        if not file_data:
            logger.error(f"File not found in R2: {doc.file_path}")
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message='File not found in cloud storage'
            )
            return {
                'success': False,
                'error': 'File not found in cloud storage'
            }

        # 3. Save temporarily for processing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, doc.filename)

        with open(temp_file_path, 'wb') as f:
            f.write(file_data)

        logger.info(f"File downloaded to temp: {temp_file_path}")

        # 4. Prepare output directory (use temp dir)
        output_dir = temp_dir
        base_name = os.path.splitext(doc.filename)[0]

        logger.info(f"Output directory: {output_dir}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Calculating optimal configuration', 'progress': 15}
        )

        # 4.5. Calculate optimal chunk configuration based on document size
        page_count = count_document_pages(temp_file_path)
        logger.info(f"Document has {page_count} pages")

        # Get user tier (default to 'free' for now - TODO: get from user model)
        user_tier = 'free'  # TODO: Retrieve from user.subscription_tier

        # Calculate optimal configuration
        optimal_config = calculate_optimal_config(page_count, user_tier)

        logger.info(f"Using optimal config: {optimal_config}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Running memvid encoder',
                'progress': 20,
                'page_count': page_count,
                'chunk_size': optimal_config['chunk_size'],
                'overlap': optimal_config['overlap']
            }
        )

        # 5. Run memvid encoder
        try:
            # Add memvidBeta to path
            memvid_beta_path = Path(__file__).parent / 'memvidBeta' / 'encoder_app'
            sys.path.insert(0, str(memvid_beta_path))

            from memvid_sections import process_file_in_sections

            logger.info("Starting memvid encoder...")

            # Process with memvid encoder using optimal configuration
            success = process_file_in_sections(
                file_path=temp_file_path,
                chunk_size=optimal_config['chunk_size'],
                overlap=optimal_config['overlap'],
                output_format='json',  # JSON only, no video
                max_pages=None,  # Process all pages
                max_chunks=optimal_config['max_chunks']
            )

            if not success:
                logger.error("Memvid encoder failed")
                update_document_status(
                    document_id,
                    user_id,
                    status='failed',
                    error_message='Memvid encoder failed'
                )
                return {
                    'success': False,
                    'error': 'Memvid encoder failed'
                }

            logger.info("Memvid encoder completed successfully")

        except Exception as e:
            logger.error(f"Error in memvid encoder: {e}")
            logger.error(traceback.format_exc())
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message=f'Encoding error: {str(e)}'
            )
            return {
                'success': False,
                'error': f'Encoding error: {str(e)}'
            }

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Saving metadata', 'progress': 80}
        )

        # 5. Verify output files exist
        metadata_file = os.path.join(output_dir, f"{base_name}_sections_metadata.json")

        if not os.path.exists(metadata_file):
            # Try alternative location (memvid encoder outputs/ directory)
            alt_metadata = Path(__file__).parent / 'memvidBeta' / 'encoder_app' / 'outputs' / f"{base_name}_sections_metadata.json"
            if alt_metadata.exists():
                # Move to correct location
                import shutil
                shutil.copy(str(alt_metadata), metadata_file)

                # Also copy index if exists
                alt_index = alt_metadata.parent / f"{base_name}_sections_index.json"
                if alt_index.exists():
                    index_file = os.path.join(output_dir, f"{base_name}_sections_index.json")
                    shutil.copy(str(alt_index), index_file)
            else:
                logger.error(f"Metadata file not found: {metadata_file}")
                update_document_status(
                    document_id,
                    user_id,
                    status='failed',
                    error_message='Output files not generated'
                )
                return {
                    'success': False,
                    'error': 'Output files not generated'
                }

        # 6. Load metadata to extract info
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            total_chunks = metadata.get('chunks_count', 0)
            total_tokens = sum(len(chunk['text'].split()) for chunk in metadata.get('chunks', []))

            # Detect language (simple heuristic)
            sample_text = ' '.join([
                chunk['text'][:100]
                for chunk in metadata.get('chunks', [])[:5]
            ])
            language = detect_language(sample_text)

        except Exception as e:
            logger.warning(f"Error loading metadata: {e}")
            total_chunks = 0
            total_tokens = 0
            language = 'unknown'

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Generating embeddings and index', 'progress': 80}
        )

        # 6.5. Generate embeddings and FAISS index for fast retrieval
        embeddings_r2_key = None
        faiss_r2_key = None

        # TEMPORARY: Skip embedding generation to avoid OOM
        # TODO: Re-enable when Railway memory is increased or processing is optimized further
        ENABLE_EMBEDDINGS = os.getenv('ENABLE_EMBEDDINGS', 'false').lower() == 'true'

        if ENABLE_EMBEDDINGS:
            try:
                from core.embedding_generator import generate_and_save_embeddings
                import time

                # Estimate processing time based on chunks
                # ~0.5 seconds per chunk for embedding generation
                estimated_time_minutes = int((total_chunks * 0.5) / 60)
                if estimated_time_minutes < 1:
                    estimated_time_minutes = 1

                logger.info(f"Generating embeddings for {total_chunks} chunks...")
                logger.info(f"Estimated time: {estimated_time_minutes} minutes")

                self.update_state(
                    state='PROCESSING',
                    meta={
                        'status': f'Generating embeddings ({estimated_time_minutes} min estimated)',
                        'progress': 80,
                        'total_chunks': total_chunks,
                        'estimated_minutes': estimated_time_minutes
                    }
                )

                start_time = time.time()

                embeddings_file, faiss_file = generate_and_save_embeddings(
                    metadata_file=metadata_file,
                    output_dir=output_dir,
                    document_id=document_id
                )

                elapsed_time = int((time.time() - start_time) / 60)
                logger.info(f"Embeddings generated in {elapsed_time} minutes (estimated: {estimated_time_minutes})")

                # Upload embeddings and FAISS index to R2
                from core.s3_storage import upload_file

                if embeddings_file and os.path.exists(embeddings_file):
                    embeddings_r2_key = f"users/{user_id}/documents/{document_id}/embeddings.npy"
                    with open(embeddings_file, 'rb') as f:
                        upload_file(f.read(), embeddings_r2_key, 'application/octet-stream')
                    logger.info(f"Embeddings uploaded to R2: {embeddings_r2_key}")

                if faiss_file and os.path.exists(faiss_file):
                    faiss_r2_key = f"users/{user_id}/documents/{document_id}/index.faiss"
                    with open(faiss_file, 'rb') as f:
                        upload_file(f.read(), faiss_r2_key, 'application/octet-stream')
                    logger.info(f"FAISS index uploaded to R2: {faiss_r2_key}")

            except Exception as e:
                logger.warning(f"Error generating embeddings/index: {e}")
                logger.warning("Continuing without pre-computed embeddings (will use on-demand)")
        else:
            logger.info("⚠️ Embedding generation DISABLED (set ENABLE_EMBEDDINGS=true to enable)")
            logger.info("Documents will use on-demand embedding generation during queries")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Uploading metadata to cloud', 'progress': 90}
        )

        # 6.6. Upload metadata JSON to R2 for persistence
        from core.s3_storage import upload_file

        metadata_r2_key = f"users/{user_id}/documents/{document_id}/metadata.json"

        try:
            with open(metadata_file, 'rb') as f:
                metadata_content = f.read()

            upload_success = upload_file(metadata_content, metadata_r2_key, 'application/json')

            if not upload_success:
                logger.warning("Failed to upload metadata to R2, but continuing...")
                metadata_r2_key = None
        except Exception as e:
            logger.warning(f"Error uploading metadata to R2: {e}")
            metadata_r2_key = None

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Finalizing', 'progress': 90}
        )

        # 7. Update document in database
        index_file = os.path.join(output_dir, f"{base_name}_sections_index.json")

        update_document_status(
            document_id,
            user_id,
            status='ready',
            processing_progress=100,
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            language=language,
            doc_metadata={
                'metadata_r2_key': metadata_r2_key,  # R2 key for metadata JSON
                'embeddings_r2_key': embeddings_r2_key,  # R2 key for embeddings
                'faiss_r2_key': faiss_r2_key,  # R2 key for FAISS index
                'metadata_file': metadata_file,  # Keep for backwards compatibility
                'index_file': index_file if os.path.exists(index_file) else None,
                'processed_at': datetime.utcnow().isoformat(),
                'encoder_version': 'memvid_sections_v2',  # Updated version
                'page_count': optimal_config['page_count'],
                'chunk_size': optimal_config['chunk_size'],
                'overlap': optimal_config['overlap'],
                'max_chunks': optimal_config['max_chunks'],
                'strategy': optimal_config['strategy'],
                'user_tier': optimal_config['tier'],
                'has_precomputed_embeddings': embeddings_r2_key is not None
            }
        )

        logger.info(f"Document processing completed: {document_id}")

        # 8. Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Temporary files cleaned up: {temp_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning temp files: {e}")

        return {
            'success': True,
            'document_id': document_id,
            'total_chunks': total_chunks,
            'total_tokens': total_tokens,
            'language': language
        }

    except Exception as e:
        logger.error(f"Unexpected error in document processing: {e}")
        logger.error(traceback.format_exc())

        # Update document status
        try:
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message=f'Processing error: {str(e)}'
            )
        except:
            pass

        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


@celery_app.task(name='tasks.cleanup_old_documents')
def cleanup_old_documents():
    """
    Periodic task to cleanup old temporary files
    Run daily via celery beat
    """
    logger.info("Starting cleanup of old documents")

    # TODO: Implement cleanup logic
    # - Delete documents marked for deletion
    # - Clean up orphaned files
    # - Archive old sessions

    return {'cleaned': 0}


def count_document_pages(file_path: str) -> int:
    """
    Count pages in a document

    Args:
        file_path: Path to document file

    Returns:
        int: Number of pages (for PDFs) or estimated pages (for text files)
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    # PDF files - count actual pages
    if file_extension == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return len(reader.pages)
        except Exception as e:
            logger.warning(f"Error counting PDF pages: {e}")
            # Fallback: estimate based on file size (rough estimate: 50KB per page)
            file_size = os.path.getsize(file_path)
            return max(1, file_size // 50000)

    # Text files - estimate pages based on file size
    # Assume ~3000 characters per page
    else:
        try:
            file_size = os.path.getsize(file_path)
            return max(1, file_size // 3000)
        except Exception as e:
            logger.warning(f"Error estimating pages: {e}")
            return 50  # Default fallback


def calculate_optimal_config(page_count: int, user_tier: str = 'free') -> dict:
    """
    Calculate optimal chunk_size and overlap based on document page count

    Strategy:
    - Small documents (≤50 pages): smaller chunks for precision
    - Medium documents (51-200 pages): balanced chunks
    - Large documents (>200 pages): larger chunks for efficiency

    Tier multipliers:
    - Free: 0.8x (reduced processing)
    - Pro: 1.0x (standard)
    - Enterprise: 1.2x (enhanced processing)

    Args:
        page_count: Number of pages in document
        user_tier: User subscription tier ('free', 'pro', 'enterprise')

    Returns:
        dict: Configuration with chunk_size, overlap, max_chunks
    """
    logger.info(f"Calculating optimal config for {page_count} pages, tier: {user_tier}")

    # Base configurations by page range
    if page_count <= 50:
        # Small documents: precision-focused
        base_chunk_size = 1000
        base_overlap = 200
        max_chunks = None  # No limit for small docs

    elif page_count <= 200:
        # Medium documents: balanced
        base_chunk_size = 1500
        base_overlap = 250
        max_chunks = None

    else:
        # Large documents: efficiency-focused
        base_chunk_size = 2000
        base_overlap = 300
        # For very large documents, consider a reasonable limit
        max_chunks = 10000 if page_count > 500 else None

    # Apply tier multipliers
    tier_multipliers = {
        'free': 0.8,      # Free tier: reduced chunk size
        'pro': 1.0,       # Pro tier: standard
        'enterprise': 1.2 # Enterprise: enhanced
    }

    multiplier = tier_multipliers.get(user_tier.lower(), 1.0)

    # Calculate final values
    chunk_size = int(base_chunk_size * multiplier)
    overlap = int(base_overlap * multiplier)

    # Ensure overlap is not too large (max 25% of chunk_size)
    overlap = min(overlap, chunk_size // 4)

    # Ensure minimum values
    chunk_size = max(800, chunk_size)
    overlap = max(150, overlap)

    config = {
        'chunk_size': chunk_size,
        'overlap': overlap,
        'max_chunks': max_chunks,
        'page_count': page_count,
        'tier': user_tier,
        'strategy': 'small' if page_count <= 50 else 'medium' if page_count <= 200 else 'large'
    }

    logger.info(f"Optimal config: chunk_size={chunk_size}, overlap={overlap}, max_chunks={max_chunks}, strategy={config['strategy']}")

    return config


def detect_language(text: str) -> str:
    """
    Simple language detection heuristic

    Args:
        text: Sample text

    Returns:
        str: Language code (it, en, es, etc.)
    """
    # Simple heuristic based on common words
    text_lower = text.lower()

    italian_words = ['il', 'la', 'di', 'che', 'è', 'per', 'una', 'del', 'alla']
    english_words = ['the', 'of', 'and', 'to', 'in', 'is', 'for', 'that', 'with']

    italian_count = sum(1 for word in italian_words if f' {word} ' in f' {text_lower} ')
    english_count = sum(1 for word in english_words if f' {word} ' in f' {text_lower} ')

    if italian_count > english_count:
        return 'it'
    elif english_count > 0:
        return 'en'
    else:
        return 'unknown'


# Task success/failure handlers
@celery_app.task(bind=True)
def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Called when a task fails"""
    logger.error(f"Task {task_id} failed: {exc}")
    logger.error(f"Args: {args}, Kwargs: {kwargs}")
    logger.error(f"Exception info: {einfo}")
