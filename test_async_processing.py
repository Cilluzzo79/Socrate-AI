"""
Test script for async document processing
Tests Celery worker integration with document upload
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db, get_or_create_user, SessionLocal
from core.document_operations import create_document, get_document_by_id, update_document_status
from tasks import process_document_task

def test_async_processing():
    """Test async document processing with Celery"""

    print("="*80)
    print("ASYNC DOCUMENT PROCESSING TEST")
    print("="*80)

    # 1. Initialize database
    print("\n[1/6] Initializing database...")
    init_db()
    print("[OK] Database initialized")

    # 2. Create test user
    print("\n[2/6] Creating test user...")
    user = get_or_create_user(
        telegram_id=123456789,
        first_name="Test",
        last_name="User",
        username="testuser"
    )
    print(f"[OK] User created: {user.id} (telegram_id: {user.telegram_id})")

    # 3. Create test document
    print("\n[3/6] Creating test document record...")

    # Use a sample file (you should have a PDF in your test directory)
    test_file = Path(__file__).parent / "test_files" / "sample.pdf"

    if not test_file.exists():
        print(f"[WARNING] Test file not found: {test_file}")
        print("Creating dummy file for testing...")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_bytes(b"%PDF-1.4\nDummy PDF content")

    doc = create_document(
        user_id=str(user.id),
        filename="sample.pdf",
        original_filename="sample.pdf",
        file_path=str(test_file),
        file_size=test_file.stat().st_size,
        mime_type="application/pdf"
    )

    print(f"[OK] Document created: {doc.id}")
    print(f"     Filename: {doc.filename}")
    print(f"     Status: {doc.status}")

    # 4. Queue async task
    print("\n[4/6] Queueing Celery task...")

    try:
        task = process_document_task.delay(str(doc.id), str(user.id))
        print(f"[OK] Task queued: {task.id}")

        # Update document with task ID
        update_document_status(
            str(doc.id),
            str(user.id),
            status='processing',
            doc_metadata={'task_id': task.id}
        )

    except Exception as e:
        print(f"[ERROR] Failed to queue task: {e}")
        print("       Make sure Celery worker is running:")
        print("       > celery -A celery_config worker --loglevel=info")
        return False

    # 5. Poll task status
    print("\n[5/6] Monitoring task status...")
    print("     (This may take 30-60 seconds depending on file size)")

    max_wait = 120  # 2 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            # Get task status
            from celery.result import AsyncResult
            task_result = AsyncResult(task.id)

            # Get document status
            doc = get_document_by_id(str(doc.id), str(user.id))

            print(f"\r     Task: {task_result.state:12} | Document: {doc.status:12} | Progress: {doc.processing_progress or 0:3}%", end="")

            # Check if complete
            if doc.status == 'ready':
                print()
                print(f"\n[OK] Processing complete!")
                print(f"     Total chunks: {doc.total_chunks}")
                print(f"     Total tokens: {doc.total_tokens}")
                print(f"     Language: {doc.language}")

                if doc.doc_metadata:
                    print(f"     Metadata file: {doc.doc_metadata.get('metadata_file', 'N/A')}")

                break

            elif doc.status == 'failed':
                print()
                print(f"\n[ERROR] Processing failed!")
                print(f"     Error: {doc.error_message}")
                return False

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
            return False
        except Exception as e:
            print(f"\n[ERROR] Error checking status: {e}")
            time.sleep(2)

    else:
        print(f"\n[WARNING] Timeout after {max_wait} seconds")
        print("         Processing may still be running in background")
        return False

    # 6. Verify output files
    print("\n[6/6] Verifying output files...")

    if doc.doc_metadata and 'metadata_file' in doc.doc_metadata:
        metadata_file = Path(doc.doc_metadata['metadata_file'])

        if metadata_file.exists():
            print(f"[OK] Metadata file exists: {metadata_file.name}")

            # Check file size
            size_kb = metadata_file.stat().st_size / 1024
            print(f"     Size: {size_kb:.2f} KB")
        else:
            print(f"[WARNING] Metadata file not found: {metadata_file}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

    return True


def test_celery_connection():
    """Test if Celery worker is accessible"""

    print("\n" + "="*80)
    print("CELERY CONNECTION TEST")
    print("="*80)

    try:
        from celery_config import celery_app

        # Check Redis connection
        print("\n[1/2] Testing Redis connection...")
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        print(f"     Redis URL: {redis_url}")

        # Ping celery
        print("\n[2/2] Pinging Celery workers...")
        result = celery_app.control.inspect().active()

        if result:
            print(f"[OK] Connected to {len(result)} worker(s)")
            for worker, tasks in result.items():
                print(f"     - {worker}: {len(tasks)} active task(s)")
        else:
            print("[WARNING] No workers found")
            print("         Start a worker with:")
            print("         > celery -A celery_config worker --loglevel=info")
            return False

        print("\n[OK] Celery connection successful")
        return True

    except Exception as e:
        print(f"[ERROR] Celery connection failed: {e}")
        print("       Make sure Redis is running:")
        print("       > docker run -d -p 6379:6379 redis:7-alpine")
        return False


if __name__ == '__main__':
    print("\nSOCRATE AI - ASYNC PROCESSING TEST SUITE")
    print("=========================================\n")

    # Test 1: Celery connection
    if not test_celery_connection():
        print("\n[ABORT] Cannot proceed without Celery worker")
        sys.exit(1)

    # Test 2: Async processing
    if test_async_processing():
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAILED] Some tests failed")
        sys.exit(1)
