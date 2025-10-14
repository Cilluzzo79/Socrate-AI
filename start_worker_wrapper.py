#!/usr/bin/env python
"""
Worker Wrapper - Starts both healthcheck server and Celery worker
For Railway deployment with healthcheck support
"""
import subprocess
import sys
import time
import os

def main():
    print("[Wrapper] Starting Celery worker with healthcheck server...")

    # Get port from environment
    port = os.getenv('PORT', '8080')

    # Start healthcheck server in background
    print(f"[Wrapper] Starting healthcheck server on port {port}...")
    healthcheck_process = subprocess.Popen(
        [sys.executable, 'worker_healthcheck.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait a moment for healthcheck to start
    time.sleep(2)
    print("[Wrapper] Healthcheck server started")

    # Start Celery worker (foreground - this blocks)
    print("[Wrapper] Starting Celery worker...")
    celery_cmd = [
        'celery',
        '-A', 'celery_config',
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=documents,maintenance,celery'
    ]

    try:
        subprocess.run(celery_cmd, check=True)
    except KeyboardInterrupt:
        print("\n[Wrapper] Shutting down...")
        healthcheck_process.terminate()
        healthcheck_process.wait()
    except Exception as e:
        print(f"[Wrapper] Error: {e}")
        healthcheck_process.terminate()
        sys.exit(1)

if __name__ == '__main__':
    main()
