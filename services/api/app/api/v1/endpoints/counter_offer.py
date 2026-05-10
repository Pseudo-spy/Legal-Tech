"""
Counter-Offer Endpoints — POST/GET /api/v1/counter-offer/{clauseId}
Implements STEP 7.6: Triggers counter-offer generation and polls result.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.clause import Clause
from app.models.contract import Contract
from app.models.counter_offer import CounterOffer
from sqlalchemy import select

from app.core.celery import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{clause_id}")
async def generate_counter_offer(
    clause_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers counter-offer generation for a HIGH-risk clause.

    - Verifies JWT and ownership
    - Checks if counter-offer already exists (returns it if so)
    - Otherwise queues the generate_counter_offer Celery task
    - Returns 202 Accepted with task status
    """
    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    # Fetch clause and verify ownership
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == current_user.id))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

    # Check if counter-offer already exists
    result = await db.execute(
        select(CounterOffer).where(CounterOffer.clause_id == clause_uuid)
    )
    existing = result.scalars().first()

    if existing:
        return JSONResponse(
            status_code=200,
            content={
                "clause_id": str(existing.clause_id),
                "aggressive": existing.aggressive_version,
                "balanced": existing.balanced_version,
                "conservative": existing.conservative_version,
                "negotiation_email": existing.negotiation_email,
            },
        )

    # Queue the Celery task
    try:
        task = celery_app.send_task(
            "generate_counter_offer",
            args=[clause_id],
        )
        logger.info("Queued counter-offer task %s for clause %s", task.id, clause_id)
    except Exception as e:
        logger.error("Failed to queue counter-offer task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue counter-offer generation",
        )

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "task_id": task.id,
            "clause_id": clause_id,
        },
    )


@router.get("/{clause_id}")
async def get_counter_offer(
    clause_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Polls for counter-offer result.

    - Returns 200 with data if ready
    - Returns 202 if still processing
    """
    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    # Fetch clause and verify ownership
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == current_user.id))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

    # Check if counter-offer exists
    result = await db.execute(
        select(CounterOffer).where(CounterOffer.clause_id == clause_uuid)
    )
    counter_offer = result.scalars().first()

    if not counter_offer:
        return JSONResponse(
            status_code=202,
            content={"status": "processing"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "clause_id": str(counter_offer.clause_id),
            "aggressive": counter_offer.aggressive_version,
            "balanced": counter_offer.balanced_version,
            "conservative": counter_offer.conservative_version,
            "negotiation_email": counter_offer.negotiation_email,
        },
    )
