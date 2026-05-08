from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

redis_url = os.getenv("REDIS_URL", "rediss://localhost:6379")

app = Celery(
    "legaltech_worker",
    broker=redis_url,
    backend=redis_url,
)

celery_app = app

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,
    task_soft_time_limit=1500,
    worker_pool="solo",
    worker_concurrency=1,
    beat_schedule={
        "cleanup-expired-reports-hourly": {
            "task": "cleanup_expired_reports",
            "schedule": 3600.0, # Hourly
        },
    },
)

app.autodiscover_tasks(["apps.worker.tasks"], force=True)
