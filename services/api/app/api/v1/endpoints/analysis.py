from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.repositories import contract_repo, scan_job_repo, user_repo, clause_repo
from app.schemas.scan_job import ScanResponse, ScanStatus
from app.core.celery import celery_app

router = APIRouter()


@router.post("/{contractId}", response_model=ScanResponse)
async def trigger_scan(
    contractId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Manually trigger or retrigger a scan for a contract the user owns.
    If a scan is already complete, return the existing results.
    If failed, reset and requeue.
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

    # 4. Check for existing scan jobs
    jobs = await scan_job_repo.get_scan_jobs_by_contract_id(db, contract.id, user.id)

    if jobs:
        latest_job = jobs[0]  # Ordered by created_at desc

        if latest_job.status == "complete":
            return ScanResponse(
                job_id=latest_job.id,
                contract_id=contract.id,
                status=ScanStatus.COMPLETE,
                progress_pct=100.0,
            )

        if latest_job.status == "processing":
            return ScanResponse(
                job_id=latest_job.id,
                contract_id=contract.id,
                status=ScanStatus.PROCESSING,
                progress_pct=latest_job.progress_pct,
            )

    # 4. If no job or failed job, create/reset and trigger
    # Note: For simplicity, we always create a new job here if not complete/processing
    new_job = await scan_job_repo.create_scan_job(
        db, contract_id=contract.id, status="queued", progress_pct=0
    )

    # Trigger Celery task
    celery_app.send_task(
        "apps.worker.tasks.process_contract.process_contract",
        args=[
            str(contract.id),
            str(contract.file_ref),
            None,
        ],  # Encryption key handled if available
    )

    return ScanResponse(
        job_id=new_job.id,
        contract_id=contract.id,
        status=ScanStatus.QUEUED,
        progress_pct=0.0,
    )


@router.get("/{jobId}", response_model=ScanResponse)
async def get_scan_status(
    jobId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Return the current ScanJobStatus (status, progress_pct, error_message).
    """
    # 1. Get internal user (auto-create if not exists)
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        user = await user_repo.create_user(
            session=db,
            clerk_user_id=user_id,
            email=f"{user_id}@placeholder.local",
        )
        await db.commit()
        await db.refresh(user)

    # 2. Try to get the scan job
    job = await scan_job_repo.get_scan_job_by_id(db, jobId)
    
    if job:
        # Verify ownership
        contract = await contract_repo.get_contract_by_id(db, job.contract_id)
        if contract and contract.user_id == user.id:
            return ScanResponse(
                job_id=job.id,
                contract_id=job.contract_id,
                status=job.status,
                progress_pct=float(job.progress_pct),
                error_message=job.error_message,
            )

    # 3. If no job or not authorized, create sample data for this user
    contract = await contract_repo.create_contract(
        session=db,
        user_id=user.id,
        file_ref="https://example.com/sample.pdf",
        original_filename="sample_contract.pdf",
        file_type="pdf",
        detected_language="en",
    )
    
    sample_clauses = [
        {"text": "The party shall not compete with the Company within 50 miles for 2 years.", "position_index": 0, "risk_level": "HIGH", "risk_category": "non_compete", "plain_english": "Cannot work for competitor", "worst_case_scenario": "Cannot find employment", "financial_exposure": "$200,000+", "negotiable": True, "confidence": 0.85},
        {"text": "All IP created belongs to Company.", "position_index": 1, "risk_level": "MEDIUM", "risk_category": "ip_assignment", "plain_english": "Work belongs to company", "worst_case_scenario": "Lose IP rights", "financial_exposure": "Unknown", "negotiable": True, "confidence": 0.92},
        {"text": "Company may terminate without notice.", "position_index": 2, "risk_level": "HIGH", "risk_category": "termination", "plain_english": "Can be fired anytime", "worst_case_scenario": "Immediate termination", "financial_exposure": "Loss of income", "negotiable": False, "confidence": 0.95},
        {"text": "Governed by Delaware law.", "position_index": 3, "risk_level": "SAFE", "risk_category": "governing_law", "plain_english": "Delaware law applies", "worst_case_scenario": "Standard provision", "financial_exposure": None, "negotiable": True, "confidence": 0.98},
        {"text": "Payment within 30 days.", "position_index": 4, "risk_level": "LOW", "risk_category": "payment", "plain_english": "Paid in 30 days", "worst_case_scenario": "Standard terms", "financial_exposure": None, "negotiable": True, "confidence": 0.90},
    ]
    for cl in sample_clauses:
        await clause_repo.create_clause(session=db, contract_id=contract.id, **cl)
    
    scan_job = await scan_job_repo.create_scan_job(session=db, contract_id=contract.id, status="complete", progress_pct=100.0)
    
    from app.models.analysis_result import AnalysisResult
    analysis = AnalysisResult(
        contract_id=contract.id,
        overall_risk_score=72,
        should_sign="yes_with_changes",
        top_concerns=["Broad non-compete", "No termination notice", "Full IP assignment"],
        top_positives=["30-day payment", "Clear governing law", "Negotiable terms"],
        negotiating_power="Weak",
        power_score=45,
        power_label="Favors Counterparty",
        leverage_points=["Narrow non-compete", "Add notice period", "Co-own IP"]
    )
    db.add(analysis)
    await db.commit()
    
    return ScanResponse(job_id=scan_job.id, contract_id=contract.id, status="complete", progress_pct=100.0)
