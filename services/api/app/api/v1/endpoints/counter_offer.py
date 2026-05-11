"""
Counter-Offer Endpoints — POST/GET /api/v1/counter-offer/{clauseId}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import httpx
import os

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.clause import Clause
from app.models.contract import Contract
from app.models.counter_offer import CounterOffer
from sqlalchemy import select

from app.core.celery import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


@router.post("/{clause_id}")
async def generate_counter_offer(
    clause_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers counter-offer generation for a HIGH-risk clause.
    For demo clause IDs, calls the AI service directly.
    """
    if clause_id.startswith("clause-"):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/counter-offer",
                    json={
                        "clause_text": "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices.",
                        "clause_type": "employment",
                        "contract_type": "employment",
                        "user_role": "employee",
                        "risk_category": clause_id.replace("clause-", "clause_"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ready",
                            "clause_id": clause_id,
                            "aggressive_clause": data.get("aggressive_clause", ""),
                            "explanation_aggressive": data.get("explanation_aggressive", ""),
                            "balanced_clause": data.get("balanced_clause", ""),
                            "explanation_balanced": data.get("explanation_balanced", ""),
                            "conservative_clause": data.get("conservative_clause", ""),
                            "explanation_conservative": data.get("explanation_conservative", ""),
                            "negotiation_email": data.get("negotiation_email", ""),
                        },
                    )
        except Exception as e:
            logger.warning("AI service call failed for counter-offer demo: %s", e)
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "clause_id": clause_id},
        )

    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == current_user))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

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
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Polls for counter-offer result.
    """
    if clause_id.startswith("clause-"):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/api/v1/counter-offer",
                    json={
                        "clause_text": "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices.",
                        "clause_type": "employment",
                        "contract_type": "employment",
                        "user_role": "employee",
                        "risk_category": clause_id.replace("clause-", "clause_"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "ready",
                            "clause_id": clause_id,
                            "aggressive_clause": data.get("aggressive_clause", ""),
                            "explanation_aggressive": data.get("explanation_aggressive", ""),
                            "balanced_clause": data.get("balanced_clause", ""),
                            "explanation_balanced": data.get("explanation_balanced", ""),
                            "conservative_clause": data.get("conservative_clause", ""),
                            "explanation_conservative": data.get("explanation_conservative", ""),
                            "negotiation_email": data.get("negotiation_email", ""),
                        },
                    )
        except Exception as e:
            logger.warning("AI service call failed for counter-offer GET demo: %s", e)
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "clause_id": clause_id},
        )

    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where((Clause.id == clause_uuid) & (Contract.user_id == current_user))
    )
    clause = result.scalars().first()

    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clause not found or access denied",
        )

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
