"""Scan job repository — database query functions for scan jobs."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.scan_job import ScanJob
from app.models.contract import Contract


async def create_scan_job(
    session: AsyncSession,
    contract_id: UUID,
    status: str = "queued",
    progress_pct: int = 0,
) -> ScanJob:
    """Create a new scan job."""
    job = ScanJob(
        contract_id=contract_id,
        status=status,
        progress_pct=progress_pct,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_scan_job_by_id(
    session: AsyncSession, job_id: UUID, user_id: Optional[UUID] = None
) -> Optional[ScanJob]:
    """Get scan job by ID. If user_id provided, scope to that user for security."""
    query = select(ScanJob).where(ScanJob.id == job_id)
    if user_id:
        query = (
            query.select_from(ScanJob).join(Contract).where(Contract.user_id == user_id)
        )
    result = await session.execute(query)
    return result.scalars().first()


async def get_scan_jobs_by_contract_id(
    session: AsyncSession,
    contract_id: UUID,
    user_id: Optional[UUID] = None,
    limit: int = 100,
) -> List[ScanJob]:
    """Get all scan jobs for a contract. Scoped to user if provided."""
    query = select(ScanJob).where(ScanJob.contract_id == contract_id)
    if user_id:
        query = (
            query.select_from(ScanJob).join(Contract).where(Contract.user_id == user_id)
        )
    result = await session.execute(
        query.order_by(ScanJob.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def update_status(
    session: AsyncSession,
    job_id: UUID,
    user_id: UUID,
    status: str,
) -> Optional[ScanJob]:
    """Update scan job status. Scoped to user_id for security."""
    job = await get_scan_job_by_id(session, job_id, user_id)
    if not job:
        return None

    job.status = status
    if status == "complete":
        from datetime import datetime, timezone

        job.completed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(job)
    return job


async def update_progress(
    session: AsyncSession,
    job_id: UUID,
    user_id: UUID,
    progress_pct: int,
) -> Optional[ScanJob]:
    """Update scan job progress percentage. Scoped to user_id."""
    job = await get_scan_job_by_id(session, job_id, user_id)
    if not job:
        return None

    job.progress_pct = min(progress_pct, 100)  # Cap at 100
    await session.commit()
    await session.refresh(job)
    return job


async def update_error(
    session: AsyncSession,
    job_id: UUID,
    user_id: UUID,
    error_message: str,
) -> Optional[ScanJob]:
    """Update scan job with error message. Scoped to user_id."""
    job = await get_scan_job_by_id(session, job_id, user_id)
    if not job:
        return None

    job.status = "failed"
    job.error_message = error_message
    from datetime import datetime, timezone

    job.completed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(job)
    return job


async def delete_scan_job(session: AsyncSession, job_id: UUID, user_id: UUID) -> bool:
    """Delete a scan job. Scoped to user_id."""
    job = await get_scan_job_by_id(session, job_id, user_id)
    if not job:
        return False

    await session.delete(job)
    await session.commit()
    return True
