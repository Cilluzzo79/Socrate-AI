"""
Celery Configuration for Async Document Processing
Uses Redis as message broker
"""

import os
from celery import Celery

# Redis URL from environment (Railway provides this)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'socrate_ai',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']  # Import tasks module
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Rome',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_backend_transport_options={
        'master_name': 'mymaster'
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # Logging
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Task routes (optional - for task prioritization)
celery_app.conf.task_routes = {
    'tasks.process_document_task': {'queue': 'documents'},
    'tasks.cleanup_old_documents': {'queue': 'maintenance'},
}

if __name__ == '__main__':
    celery_app.start()
