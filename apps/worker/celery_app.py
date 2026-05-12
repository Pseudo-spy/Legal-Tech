from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
from dotenv import load_dotenv as _load_dotenv

_root = _Path(__file__).resolve().parents[2]
_api_path = str(_root / "services" / "api")
_ai_path = str(_root / "services" / "ai")
for _p in (str(_root), _api_path, _ai_path):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

_load_dotenv()

from celery import Celery
import os

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
            "schedule": 3600.0,
        },
    },
)

app.autodiscover_tasks(["apps.worker.tasks"], force=True)
