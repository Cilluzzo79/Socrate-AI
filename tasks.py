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

        # ALTERNATIVE A: Check if OCR text was pre-extracted (batch upload from gallery)
        ocr_preextracted = doc.doc_metadata.get('ocr_preextracted', False) if doc.doc_metadata else False
        ocr_texts = doc.doc_metadata.get('ocr_texts', None) if doc.doc_metadata else None

        # Save original base_name for metadata file lookup (before we change temp_file_path)
        original_base_name = base_name

        if ocr_preextracted and ocr_texts:
            logger.info(f"[ALT-A] Using pre-extracted OCR text from {len(ocr_texts)} pages")

            # Create temporary text file with pre-extracted OCR text
            # This bypasses PyPDF2 entirely - much faster and no Poppler dependency!
            # IMPORTANT: Use same base_name (without _ocr suffix) so metadata lookup works
            text_file_path = os.path.join(temp_dir, f"{base_name}.txt")

            with open(text_file_path, 'w', encoding='utf-8') as f:
                for page_num, page_text in enumerate(ocr_texts, start=1):
                    f.write(f"\n## Pagina {page_num}\n\n")
                    f.write(page_text)
                    f.write("\n\n")

            logger.info(f"[ALT-A] Created text file with OCR content: {text_file_path}")

            # Use text file instead of PDF for processing
            temp_file_path = text_file_path
            page_count = len(ocr_texts)
        else:
            # Standard flow: calculate pages from actual file
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

        # Generate embeddings INLINE in metadata.json
        # This solves the OOM problem during queries by pre-calculating embeddings
        ENABLE_EMBEDDINGS = os.getenv('ENABLE_EMBEDDINGS', 'false').lower() == 'true'

        if ENABLE_EMBEDDINGS:
            try:
                from core.embedding_generator import generate_and_save_embeddings_inline
                import time

                # Estimate processing time (~0.5 seconds per chunk)
                estimated_time_minutes = max(1, int((total_chunks * 0.5) / 60))

                logger.info(f"Generating INLINE embeddings for {total_chunks} chunks...")
                logger.info(f"Estimated time: {estimated_time_minutes} minutes")

                self.update_state(
                    state='PROCESSING',
                    meta={
                        'status': f'Generating inline embeddings (~{estimated_time_minutes} min)',
                        'progress': 85,
                        'total_chunks': total_chunks,
                        'estimated_minutes': estimated_time_minutes
                    }
                )

                start_time = time.time()

                # Generate embeddings and save INLINE to metadata.json
                success = generate_and_save_embeddings_inline(
                    metadata_file=metadata_file
                )

                elapsed_time = int((time.time() - start_time) / 60)

                if success:
                    logger.info(f"✅ Inline embeddings generated in {elapsed_time} min (estimated: {estimated_time_minutes})")
                    # Mark that embeddings are available (inline in metadata)
                    embeddings_r2_key = "inline"
                else:
                    logger.warning("Failed to generate inline embeddings")

            except Exception as e:
                logger.warning(f"Error generating inline embeddings: {e}")
                logger.warning("Continuing without pre-computed embeddings (queries will be slower)")
        else:
            logger.info("⚠️ Embedding generation DISABLED (set ENABLE_EMBEDDINGS=true to enable)")
            logger.info("Queries will recalculate embeddings on-demand (slower for large documents)")

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


@celery_app.task(bind=True, name='tasks.process_image_ocr_task')
def process_image_ocr_task(self, document_id: str, user_id: str):
    """
    Process uploaded image with Google Cloud Vision OCR
    BYPASSES MEMVID ENCODER - creates chunks directly from OCR text

    Flow:
    1. Download image from R2
    2. Extract text with Google Cloud Vision OCR
    3. Create chunks directly from text (simple character-based splitting)
    4. Generate embeddings inline
    5. Save metadata JSON to R2
    6. Mark document as 'ready'

    Args:
        document_id: Document UUID
        user_id: User UUID (for ownership verification)

    Returns:
        dict: OCR result with status and metadata
    """
    logger.info(f"[OCR NEW] Starting OCR processing: {document_id} for user {user_id}")

    # Update task state
    self.update_state(
        state='PROCESSING',
        meta={'status': 'Initializing OCR', 'progress': 0}
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

        logger.info(f"[OCR NEW] Processing image: {doc.filename} ({doc.file_path})")

        # Update document status to processing
        update_document_status(
            document_id,
            user_id,
            status='processing',
            processing_progress=10
        )

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Downloading image from R2', 'progress': 10}
        )

        # 2. Download image from R2
        from core.s3_storage import download_file, upload_file

        logger.info(f"[OCR NEW] Downloading image from R2: {doc.file_path}")
        image_data = download_file(doc.file_path)

        if not image_data:
            logger.error(f"[OCR NEW] Image not found in R2: {doc.file_path}")
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message='Image not found in cloud storage'
            )
            return {
                'success': False,
                'error': 'Image not found in cloud storage'
            }

        logger.info(f"[OCR NEW] Image downloaded: {len(image_data)} bytes")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Extracting text with Google Cloud Vision OCR', 'progress': 30}
        )

        # 3. Extract text with Google Cloud Vision OCR
        from core.ocr_processor import extract_text_from_image

        logger.info("[OCR NEW] Calling Google Cloud Vision OCR API...")
        ocr_result = extract_text_from_image(image_data, doc.filename)

        if not ocr_result['success']:
            logger.error(f"[OCR NEW] OCR failed: {ocr_result.get('error', 'Unknown error')}")
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message=f"OCR failed: {ocr_result.get('error', 'Unknown error')}"
            )
            return {
                'success': False,
                'error': ocr_result.get('error', 'OCR processing failed')
            }

        extracted_text = ocr_result['text']
        language = ocr_result.get('language', 'unknown')
        char_count = len(extracted_text)
        word_count = len(extracted_text.split())

        logger.info(f"[OCR NEW] ✅ OCR successful: {char_count} characters, {word_count} words, language: {language}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Creating text chunks directly (bypassing encoder)', 'progress': 50}
        )

        # 4. Create chunks directly from OCR text (BYPASS ENCODER)
        CHUNK_SIZE = 1500  # characters
        OVERLAP = 300      # characters

        chunks = []
        chunk_id = 0

        logger.info(f"[OCR NEW] Creating chunks with size={CHUNK_SIZE}, overlap={OVERLAP}")

        for i in range(0, len(extracted_text), CHUNK_SIZE - OVERLAP):
            chunk_text = extracted_text[i:i + CHUNK_SIZE]
            if len(chunk_text.strip()) > 0:
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "start_char": i,
                    "end_char": i + len(chunk_text),
                    "metadata": {
                        "source": "ocr",
                        "language": language,
                        "chunk_method": "character_based",
                        "original_filename": doc.filename
                    }
                })
                chunk_id += 1

        total_chunks = len(chunks)
        logger.info(f"[OCR NEW] Created {total_chunks} chunks from OCR text")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': f'Generating embeddings for {total_chunks} chunks', 'progress': 60}
        )

        # 5. Generate embeddings inline (if enabled)
        ENABLE_EMBEDDINGS = os.getenv('ENABLE_EMBEDDINGS', 'false').lower() == 'true'
        embeddings_generated = False

        if ENABLE_EMBEDDINGS:
            try:
                logger.info(f"[OCR NEW] Generating inline embeddings for {total_chunks} chunks...")

                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')

                # Generate embeddings for all chunks
                chunk_texts = [chunk['text'] for chunk in chunks]
                embeddings = model.encode(chunk_texts, show_progress_bar=False)

                # Add embeddings to chunks
                for i, chunk in enumerate(chunks):
                    chunk['embedding'] = embeddings[i].tolist()

                embeddings_generated = True
                logger.info(f"[OCR NEW] ✅ Generated embeddings for {total_chunks} chunks")

            except Exception as e:
                logger.warning(f"[OCR NEW] Failed to generate embeddings: {e}")
                logger.warning("[OCR NEW] Continuing without embeddings (queries will be slower)")
        else:
            logger.info("[OCR NEW] ⚠️ Embedding generation DISABLED (set ENABLE_EMBEDDINGS=true)")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Creating metadata JSON', 'progress': 80}
        )

        # 6. Create metadata JSON compatible with query engine
        metadata = {
            "document_id": document_id,
            "filename": doc.filename,
            "processing_method": "ocr_direct_chunking",
            "ocr_provider": "google_cloud_vision",
            "language": language,
            "chunks_count": total_chunks,
            "total_characters": char_count,
            "total_words": word_count,
            "chunk_size": CHUNK_SIZE,
            "overlap": OVERLAP,
            "has_embeddings": embeddings_generated,
            "processed_at": datetime.utcnow().isoformat(),
            "chunks": chunks,
            "ocr_metadata": {
                "char_count": char_count,
                "word_count": word_count,
                "confidence": ocr_result.get('confidence', 1.0),
                "language": language
            }
        }

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Uploading metadata to R2', 'progress': 90}
        )

        # 7. Save metadata JSON to R2
        metadata_r2_key = f"users/{user_id}/documents/{document_id}/metadata.json"

        logger.info(f"[OCR NEW] Uploading metadata to R2: {metadata_r2_key}")

        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        upload_success = upload_file(metadata_json.encode('utf-8'), metadata_r2_key, 'application/json')

        if not upload_success:
            logger.error("[OCR NEW] Failed to upload metadata to R2")
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message='Failed to upload metadata'
            )
            return {
                'success': False,
                'error': 'Failed to upload metadata'
            }

        logger.info(f"[OCR NEW] ✅ Metadata uploaded successfully")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Finalizing document', 'progress': 95}
        )

        # 8. Update document status to 'ready'
        update_document_status(
            document_id,
            user_id,
            status='ready',
            processing_progress=100,
            total_chunks=total_chunks,
            total_tokens=word_count,
            language=language,
            doc_metadata={
                'metadata_r2_key': metadata_r2_key,
                'embeddings_r2_key': 'inline' if embeddings_generated else None,
                'original_image_r2_key': doc.file_path,
                'processed_at': datetime.utcnow().isoformat(),
                'processing_method': 'ocr_direct_chunking',
                'ocr_provider': 'google_cloud_vision',
                'chunk_size': CHUNK_SIZE,
                'overlap': OVERLAP,
                'has_precomputed_embeddings': embeddings_generated,
                'ocr_metadata': {
                    'char_count': char_count,
                    'word_count': word_count,
                    'confidence': ocr_result.get('confidence', 1.0),
                    'language': language
                }
            }
        )

        logger.info(f"[OCR NEW] ✅ OCR processing completed: {document_id} - {total_chunks} chunks, ready for queries")

        return {
            'success': True,
            'document_id': document_id,
            'total_chunks': total_chunks,
            'total_tokens': word_count,
            'language': language,
            'processing_method': 'ocr_direct_chunking',
            'has_embeddings': embeddings_generated
        }

    except Exception as e:
        logger.error(f"[OCR NEW] Unexpected error in OCR processing: {e}")
        logger.error(traceback.format_exc())

        # Update document status
        try:
            update_document_status(
                document_id,
                user_id,
                status='failed',
                error_message=f'OCR error: {str(e)}'
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
        base_overlap = 300  # Increased from 250 to 300 (20% of 1500)
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
