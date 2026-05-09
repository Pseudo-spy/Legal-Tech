"""
Power Asymmetry Endpoint — GET /api/v1/power/{contractId}
Implements STEP 7.2: Returns power asymmetry analysis for a completed scan.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from services.api.app.api.deps import get_current_user, get_db
from services.api.app.models.user import User
from services.api.app.models.contract import Contract
from services.api.app.models.analysis_result import AnalysisResult
from sqlalchemy import select

router = APIRouter()


@router.get("/{contract_id}")
async def get_power_analysis(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the power asymmetry analysis for a contract.

    - Verifies JWT and ownership
    - Fetches power analysis from analysis_results table
    - Returns 404 if scan not complete or no power analysis exists
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

    # Return power analysis fields
    return JSONResponse(
        status_code=200,
        content={
            "contract_id": str(analysis.contract_id),
            "power_score": analysis.power_score or 0,
            "power_label": analysis.power_label or "Unknown",
            "key_imbalances": analysis.leverage_points
            or [],  # Reusing leverage_points field
            "leverage_points": analysis.leverage_points or [],
        },
    )
