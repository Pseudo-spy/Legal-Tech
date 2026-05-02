from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class ContractBase(BaseModel):
    original_filename: str
    file_type: str  # pdf or docx
    file_size_bytes: int

class ContractCreate(ContractBase):
    file_url: HttpUrl

class ContractRead(ContractBase):
    id: UUID
    user_id: str
    file_url: str
    detected_language: str
    contract_type: Optional[str] = None
    overall_risk_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
