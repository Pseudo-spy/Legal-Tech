"""
Dashboard Endpoint — GET /api/v1/dashboard
Returns user's contracts and power trend data for dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.repositories import user_repo, contract_repo, scan_job_repo
from app.models.analysis_result import AnalysisResult
from sqlalchemy import select, func

router = APIRouter()


@router.get("/")
async def get_dashboard(
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns dashboard data: contracts list and power trend.
    """
    # Get or create user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        user = await user_repo.create_user(
            session=db,
            clerk_user_id=user_id,
            email=f"{user_id}@placeholder.local",
        )
        await db.commit()
        await db.refresh(user)

    # Get all contracts for user
    contracts = await contract_repo.get_all_contracts_by_user_id(db, user.id)
    
    # Get scan jobs for contracts
    contract_data = []
    for contract in contracts:
        jobs = await scan_job_repo.get_scan_jobs_by_contract_id(db, contract.id)
        latest_job = jobs[0] if jobs else None
        
        # Get analysis result
        result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.contract_id == contract.id)
        )
        analysis = result.scalars().first()
        
        contract_data.append({
            "id": str(contract.id),
            "file_name": contract.original_filename,
            "contract_type": contract.contract_type or "unknown",
            "overall_risk_score": analysis.overall_risk_score if analysis else None,
            "should_sign": analysis.should_sign if analysis else None,
            "created_at": contract.created_at.isoformat() if contract.created_at else None,
            "status": latest_job.status if latest_job else "not_started",
        })
    
    # Calculate power trend (average power score)
    result = await db.execute(
        select(func.avg(AnalysisResult.power_score))
        .where(AnalysisResult.contract_id.in_([c.id for c in contracts]))
    )
    avg_power = result.scalar()
    
    power_trend = None
    if avg_power is not None:
        if avg_power < -30:
            trend_desc = "Power is heavily skewed against you"
        elif avg_power < 0:
            trend_desc = "Slightly favors the counterparty"
        elif avg_power == 0:
            trend_desc = "Balanced power structure"
        elif avg_power <= 30:
            trend_desc = "Slightly favors you"
        else:
            trend_desc = "Power heavily favors you"
        
        power_trend = {
            "average_power_score": round(float(avg_power)),
            "trend_description": trend_desc
        }

    return {
        "contracts": contract_data,
        "power_trend": power_trend,
    }