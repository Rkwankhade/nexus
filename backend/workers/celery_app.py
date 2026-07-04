"""
Celery application configuration for NEXUS background jobs: scans, AI
analysis, and report generation run here rather than blocking API request
threads. Broker/backend URLs come from centralized settings.
"""

from __future__ import annotations

from celery import Celery
from celery.signals import worker_ready

from core.config import settings
from utils.logger import get_logger

log = get_logger(__name__)

celery_app = Celery(
    "nexus",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.scan_tasks",
        "workers.ai_tasks",
        "workers.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,  # hard kill after 1 hour
    task_soft_time_limit=55 * 60,
    worker_prefetch_multiplier=1,  # long-running scan tasks: don't over-fetch
    task_acks_late=True,
    result_expires=60 * 60 * 24 * 7,  # 7 days
    task_default_queue="nexus_default",
    task_routes={
        "workers.scan_tasks.*": {"queue": "nexus_scans"},
        "workers.ai_tasks.*": {"queue": "nexus_ai"},
        "workers.report_tasks.*": {"queue": "nexus_reports"},
    },
)


@worker_ready.connect
def _on_worker_ready(**kwargs) -> None:
    log.info("NEXUS Celery worker ready", extra={"extra_fields": {"queues": list(celery_app.conf.task_routes)}})
