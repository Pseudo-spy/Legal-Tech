from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from services.api.app.db.session import get_async_session
from services.api.app.core.security import get_current_user_id
from services.api.app.repositories import (
    contract_repo,
    user_repo,
    clause_repo,
    scan_job_repo,
)

router = APIRouter()


@router.get("/")
async def get_contracts(
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Return a list of all contracts for the authenticated user.
    Includes overall risk score from analysis_results.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get all contracts for this user
    contracts = await contract_repo.get_all_contracts_by_user_id(db, user.id)

    return {
        "contracts": [
            {
                "contract_id": str(c.id),
                "original_filename": c.original_filename,
                "contract_type": c.contract_type,
                "detected_language": c.detected_language,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "overall_risk_score": c.analysis_result.overall_risk_score
                if c.analysis_result
                else None,
            }
            for c in contracts
        ]
    }


@router.get("/{contractId}")
async def get_contract_detail(
    contractId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Return the full contract detail including all clause results,
    analysis result, and scan job status.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get contract
    contract = await contract_repo.get_contract_by_id(db, contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 3. Verify ownership
    if contract.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to contract")

    # 3. Get clauses
    clauses = await clause_repo.get_all_clauses_by_contract_id(db, contract.id)

    # 4. Get latest scan job
    jobs = await scan_job_repo.get_scan_jobs_by_contract_id(db, contract.id, user.id)
    latest_job = jobs[0] if jobs else None

    # 5. Build response
    return {
        "contract_id": str(contract.id),
        "original_filename": contract.original_filename,
        "contract_type": contract.contract_type,
        "detected_language": contract.detected_language,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "analysis_result": {
            "overall_risk_score": contract.analysis_result.overall_risk_score
            if contract.analysis_result
            else None,
            "should_sign": contract.analysis_result.should_sign
            if contract.analysis_result
            else None,
            "top_concerns": contract.analysis_result.top_concerns
            if contract.analysis_result
            else [],
            "top_positives": contract.analysis_result.top_positives
            if contract.analysis_result
            else [],
        }
        if contract.analysis_result
        else None,
        "scan_status": {
            "status": latest_job.status if latest_job else "not_started",
            "progress_pct": latest_job.progress_pct if latest_job else 0,
            "error_message": latest_job.error_message if latest_job else None,
        },
        "clauses": [
            {
                "clause_id": str(cl.id),
                "text": cl.text,
                "position_index": cl.position_index,
                "risk_level": cl.risk_level,
                "risk_category": cl.risk_category,
                "plain_english": cl.plain_english,
                "worst_case_scenario": cl.worst_case_scenario,
                "confidence": cl.confidence,
            }
            for cl in clauses
        ],
    }


@router.delete("/{contractId}")
async def delete_contract(
    contractId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Hard-delete the contract and all associated data for the authenticated user.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get contract
    contract = await contract_repo.get_contract_by_id(db, contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 3. Verify ownership
    if contract.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to contract")

    # 4. Attempt deletion
    success = await contract_repo.delete_contract(db, contractId, user.id)

    return {"message": "Contract and associated data deleted successfully"}
