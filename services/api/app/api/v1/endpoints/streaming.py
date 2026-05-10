# Streaming endpoint: serves the GET /scan/{jobId}/stream route.
# Validates the JWT, confirms job ownership, then opens a Redis pub/sub
# subscription and pushes each clause result to the browser as Server-Sent Events.

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.repositories.scan_job_repo import ScanJobRepository
from app.core.config import settings
from app.core.security import get_current_user_from_query
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 15  # seconds
REDIS_CHANNEL_PREFIX = "scan:"


# ---------------------------------------------------------------------------
# Helper: async SSE generator
# ---------------------------------------------------------------------------


async def _sse_generator(
    job_id: str,
    user_id: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Core generator that drives the SSE stream for one scan job.

    Flow:
      1. Re-verify job ownership (defence-in-depth after the route check).
      2. Subscribe to the Redis channel ``scan:job:<job_id>``.
      3. Yield messages as they arrive; also yield heartbeats every 15 s.
      4. When a message whose ``type`` == ``"complete"`` arrives (or the job
         is already complete in the DB), emit ``event: complete`` and return.
    """
    repo = ScanJobRepository(db)

    # ── 1. Confirm job is still owned by this user ──────────────────────────
    job = await repo.get_by_id(job_id)
    if not job or str(job.user_id) != user_id:
        yield 'event: error\ndata: {"detail": "Not found"}\n\n'
        return

    # ── 2. If the job is already complete, stream stored clauses + done ──────
    if job.status == "complete":
        clauses = await repo.get_clauses(job_id)
        for clause in clauses:
            payload = json.dumps({"type": "clause", "data": clause})
            yield f"data: {payload}\n\n"
        yield "event: complete\ndata: {}\n\n"
        return

    # ── 3. Subscribe to Redis pub/sub ────────────────────────────────────────
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    channel_name = f"{REDIS_CHANNEL_PREFIX}{job_id}"

    try:
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel_name)
            logger.info("SSE: subscribed to channel %s", channel_name)

            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()

                # ── heartbeat ────────────────────────────────────────────────
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield ": heartbeat\n\n"  # SSE comment — keeps TCP alive
                    last_heartbeat = now

                # ── poll Redis (non-blocking, 100 ms timeout) ────────────────
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=0.1,
                )

                if message is None:
                    await asyncio.sleep(0.05)
                    continue

                raw = message.get("data", "")
                if not isinstance(raw, str):
                    continue

                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning(
                        "SSE: invalid JSON on channel %s: %r", channel_name, raw
                    )
                    continue

                msg_type = payload.get("type", "")

                if msg_type == "clause":
                    yield f"data: {raw}\n\n"

                elif msg_type == "progress":
                    yield f"event: progress\ndata: {raw}\n\n"

                elif msg_type == "complete":
                    yield f"event: complete\ndata: {raw}\n\n"
                    logger.info("SSE: job %s complete — closing stream", job_id)
                    return

                elif msg_type == "error":
                    yield f"event: error\ndata: {raw}\n\n"
                    return

    except asyncio.CancelledError:
        logger.info("SSE: client disconnected for job %s", job_id)
    finally:
        await redis_client.aclose()


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "/scan/{job_id}/stream",
    summary="Stream clause results for a scan job via SSE",
    responses={
        200: {"description": "text/event-stream"},
        401: {"description": "Invalid or missing JWT"},
        404: {"description": "Job not found or does not belong to user"},
    },
)
async def stream_scan_results(
    job_id: str,
    request: Request,
    token: str = None,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    # Validate token from query param
    user_id = await get_current_user_from_query(token)
    current_user_id = user_id
    """
    Opens a persistent SSE connection for ``job_id``.

    Security:
    - ``get_current_user`` validates the JWT from the ``Authorization`` header.
    - Ownership of the job is verified inside ``_sse_generator`` against the DB.

    The client receives:
    - ``data: {...}``           — clause result events (default event type)
    - ``event: progress``       — progress_pct updates
    - ``event: complete``       — signals the scan is done; client should close
    - ``event: error``          — unrecoverable pipeline failure
    - ``: heartbeat``           — SSE comment every 15 s (no browser event fired)
    """
    # Verify job exists and belongs to the user before streaming anything
    repo = ScanJobRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if str(job.user_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    generator = _sse_generator(
        job_id=job_id,
        user_id=str(current_user_id),
        db=db,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
