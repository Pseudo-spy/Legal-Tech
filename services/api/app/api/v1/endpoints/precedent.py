"""
Precedent Endpoint — GET /api/v1/precedent/{clauseId}
Implements STEP 7.5: Returns legal precedent match for a HIGH-risk clause.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.clause import Clause
from app.models.contract import Contract
from app.models.precedent_match import PrecedentMatch
from sqlalchemy import select

router = APIRouter()


@router.get("/{clause_id}")
async def get_precedent(
    clause_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the legal precedent match for a HIGH-risk clause.

    - Verifies JWT and ownership (clause must belong to user's contract)
    - Fetches precedent from precedent_matches table
    - Returns 404 if no precedent exists (e.g., for non-HIGH clauses)
    """
    try:
        clause_uuid = UUID(clause_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clause ID"
        )

    # Fetch clause and verify ownership via contract → user
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

    # Fetch precedent match
    result = await db.execute(
        select(PrecedentMatch).where(PrecedentMatch.clause_id == clause_uuid)
    )
    precedent = result.scalars().first()

    if not precedent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No precedent match found for this clause (HIGH-risk clauses only)",
        )

    # Return precedent data
    return JSONResponse(
        status_code=200,
        content={
            "clause_id": str(precedent.clause_id),
            "case_name": precedent.case_name,
            "year": precedent.case_year,
            "jurisdiction": precedent.jurisdiction,
            "outcome": precedent.outcome,
            "precedent_summary": precedent.enforcement_likelihood,  # Using this field to store summary
            "enforcement_likelihood": precedent.enforcement_likelihood,
            "confidence_score": precedent.confidence_score,
        },
    )
