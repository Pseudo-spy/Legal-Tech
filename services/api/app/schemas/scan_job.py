from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from enum import Enum

class ScanStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"

class ScanResponse(BaseModel):
    job_id: UUID
    contract_id: UUID
    status: ScanStatus
    progress_pct: float = 0.0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
