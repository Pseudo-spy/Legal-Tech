"""
Translate Endpoint — POST /api/v1/translate/{contractId}
Implements STEP 9.2: Queues post-scan language switching.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.contract import Contract
from sqlalchemy import select

from app.core.celery import celery_app

router = APIRouter()
logger = __import__("logging").getLogger(__name__)


@router.post("/{contract_id}")
async def translate_contract(
    contract_id: str,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Queues translation of contract results to a different language.

    - Verifies JWT and ownership
    - Queues the translate_results Celery task
    - Returns 202 Accepted with task status
    """
    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contract ID"
        )

    # Verify contract exists and belongs to user
    result = await db.execute(
        select(Contract).where(
            (Contract.id == contract_uuid) & (Contract.user_id == current_user.id)
        )
    )
    contract = result.scalars().first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or access denied",
        )

    target_language = request.get("target_language", "en")

    # Validate language
    supported = ["en", "es", "fr", "de", "pt", "hi"]
    if target_language not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Supported: {supported}",
        )

    # Queue the Celery task
    try:
        task = celery_app.send_task(
            "translate_results_task",
            args=[contract_id, target_language],
        )
        logger.info(
            "Queued translation task %s for contract %s to %s",
            task.id,
            contract_id,
            target_language,
        )
    except Exception as e:
        logger.error("Failed to queue translation task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue translation",
        )

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "task_id": task.id,
            "contract_id": contract_id,
            "target_language": target_language,
        },
    )
