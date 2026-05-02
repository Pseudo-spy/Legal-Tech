from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.repositories import contract_repo, scan_job_repo
from app.schemas.contract import ContractCreate
from app.schemas.scan_job import ScanResponse, ScanStatus
from typing import Tuple

async def create_contract_and_job(
    db: AsyncSession, 
    user_id: str, 
    contract_data: ContractCreate
) -> Tuple[UUID, UUID, ScanStatus]:
    """
    Business logic for creating a contract and its initial scan job.
    """
    # 1. Create the contract record
    contract = await contract_repo.create_contract(
        session=db,
        user_id=user_id,
        file_ref=str(contract_data.file_url),
        original_filename=contract_data.original_filename,
        file_type=contract_data.file_type,
        detected_language="unknown"
    )
    
    # 2. Create the scan job record
    scan_job = await scan_job_repo.create_scan_job(
        session=db,
        contract_id=contract.id,
        status="queued",
        progress_pct=0
    )
    
    # 3. Queue the Celery task (will implement the import later or use a generic trigger)
    # For now, we'll just return the IDs. The actual triggering will happen in the endpoint.
    
    return scan_job.id, contract.id, ScanStatus.QUEUED
