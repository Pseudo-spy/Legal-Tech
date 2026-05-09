"""Database models for LegalTech AI Contract Scanner."""

from services.api.app.models.user import User
from services.api.app.models.contract import Contract
from services.api.app.models.clause import Clause
from services.api.app.models.scan_job import ScanJob
from services.api.app.models.analysis_result import AnalysisResult
from services.api.app.models.counter_offer import CounterOffer
from services.api.app.models.precedent_match import PrecedentMatch
from services.api.app.models.report import Report
from services.api.app.models.embedding import Embedding

__all__ = [
    "User",
    "Contract",
    "Clause",
    "ScanJob",
    "AnalysisResult",
    "CounterOffer",
    "PrecedentMatch",
    "Report",
    "Embedding",
]
