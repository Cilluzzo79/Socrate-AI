#!/bin/bash
# Start both healthcheck server and Celery worker

echo "[Worker] Starting healthcheck server in background..."
python worker_healthcheck.py &

echo "[Worker] Waiting 2 seconds for healthcheck to start..."
sleep 2

echo "[Worker] Starting Celery worker..."
celery -A celery_config worker --loglevel=info --concurrency=2 -Q documents,maintenance,celery
