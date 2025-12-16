"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "transaction_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

if __name__ == "__main__":
    celery_app.start()
