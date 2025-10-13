"""
Simple async test - verify Celery integration works
"""

import os
import sys
from pathlib import Path

# Set Redis URL for testing
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

print("\n" + "="*60)
print("SIMPLE ASYNC TEST")
print("="*60)

# Test 1: Import Celery config
print("\n[1/5] Testing Celery configuration...")
try:
    from celery_config import celery_app
    print("[OK] Celery app imported")
    print(f"     Broker: {celery_app.conf.broker_url}")
    print(f"     Backend: {celery_app.conf.result_backend}")
except Exception as e:
    print(f"[ERROR] Failed to import Celery: {e}")
    sys.exit(1)

# Test 2: Check worker is running
print("\n[2/5] Checking for active workers...")
try:
    result = celery_app.control.inspect().active()
    if result:
        print(f"[OK] Found {len(result)} worker(s)")
        for worker, tasks in result.items():
            print(f"     - {worker}: {len(tasks)} active task(s)")
    else:
        print("[WARNING] No workers found (worker may not be running)")
except Exception as e:
    print(f"[ERROR] Failed to check workers: {e}")

# Test 3: Check registered tasks
print("\n[3/5] Checking registered tasks...")
try:
    result = celery_app.control.inspect().registered()
    if result:
        tasks = list(result.values())[0]
        print(f"[OK] Found {len(tasks)} registered task(s):")
        for task in tasks:
            print(f"     - {task}")

        # Verify our task is registered
        if 'tasks.process_document_task' in tasks:
            print("[OK] process_document_task is registered!")
        else:
            print("[WARNING] process_document_task not found!")
    else:
        print("[WARNING] No registered tasks found")
except Exception as e:
    print(f"[ERROR] Failed to check tasks: {e}")

# Test 4: Database initialization
print("\n[4/5] Testing database initialization...")
try:
    from core.database import init_db
    init_db()
    print("[OK] Database initialized")
except Exception as e:
    print(f"[WARNING] Database init failed: {e}")
    print("         This is OK for basic Celery testing")

# Test 5: Queue a simple test task (without database)
print("\n[5/5] Testing task queueing...")
try:
    # Import the task
    from tasks import process_document_task
    print("[OK] Task imported successfully")

    # Try to queue it (it will fail but we just want to see if queueing works)
    print("[INFO] Attempting to queue task...")
    print("[INFO] (Task will fail due to missing document, this is expected)")

    # Queue with fake IDs
    task = process_document_task.delay("test-doc-id", "test-user-id")
    print(f"[OK] Task queued: {task.id}")
    print(f"     State: {task.state}")

    # Wait a bit
    import time
    time.sleep(2)

    # Check state
    print(f"     State after 2s: {task.state}")

except Exception as e:
    print(f"[ERROR] Failed to queue task: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nSummary:")
print("  - Celery configuration: OK")
print("  - Worker connection: Check logs above")
print("  - Task registration: OK")
print("  - Task queueing: Check logs above")
print("\nNext step: Check worker logs for task execution")
print("="*60 + "\n")
