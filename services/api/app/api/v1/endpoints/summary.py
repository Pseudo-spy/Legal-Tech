"""
Summary Card Endpoint — GET /api/v1/summary/{contractId}
Implements STEP 7.3: Returns summary card and pros/cons for a completed scan.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.contract import Contract
from app.models.analysis_result import AnalysisResult
from sqlalchemy import select

router = APIRouter()


@router.get("/{contract_id}")
async def get_summary(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the summary card and pros/cons for a contract.

    - Verifies JWT and ownership
    - Fetches summary from analysis_results table
    - Returns 404 if scan not complete or no summary exists
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

    # Fetch analysis result
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.contract_id == contract_uuid)
    )
    analysis = result.scalars().first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Analysis not yet available",
        )

    # Return combined summary + pros/cons response
    return JSONResponse(
        status_code=200,
        content={
            "contract_id": str(analysis.contract_id),
            "summary": {
                "one_liner": analysis.top_concerns[0]
                if analysis.top_concerns
                else ""
                if analysis.top_concerns
                else "",
                "should_you_sign": analysis.should_sign or "Unknown",
                "top_3_concerns": analysis.top_concerns or [],
                "top_2_positives": analysis.top_positives or [],
                "overall_risk_score": analysis.overall_risk_score or 0,
                "negotiating_power": analysis.negotiating_power or "Unknown",
            },
        },
    )
