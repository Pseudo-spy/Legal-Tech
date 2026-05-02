from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.schemas.contract import ContractCreate
from app.schemas.scan_job import ScanResponse
from app.services import contract_service
from app.core.celery import celery_app

router = APIRouter()

@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a contract and trigger a scan job.
    """
    job_id, contract_id, scan_status = await contract_service.create_contract_and_job(
        db, user_id, contract_data
    )
    
    # Trigger Celery task
    # Note: We use send_task by name to avoid direct dependency on worker code
    celery_app.send_task(
        "apps.worker.tasks.process_contract.process_contract", 
        args=[str(contract_id), str(contract_data.file_url)]
    )
    
    return ScanResponse(
        job_id=job_id,
        contract_id=contract_id,
        status=scan_status,
        progress_pct=0.0
    )
