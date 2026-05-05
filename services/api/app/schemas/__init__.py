"""services/api/app/schemas package."""

from .response import (
    RiskLevel,
    ContractType,
    ImpactSeverity,
    Likelihood,
    NegotiationPriority,
    AcceptanceLikelihood,
    AsymmetryCategory,
    Enforceability,
    PrecedentType,
    ClauseType,
    ErrorDetail,
    APIError,
    HealthResponse,
    PaginationParams,
    PaginatedResponse,
)

from .clause import (
    ClauseRecommendation,
    ClauseResult,
    ClauseTypeDetection,
    ClauseConsequence,
    ClauseSummary,
    ClausePowerAsymmetry,
    ClauseCounterOffer,
    ClausePrecedent,
    FullClauseAnalysis,
)

from .contract import (
    ContractCreate,
    ContractUpdate,
    ContractRead,
    ContractListItem,
    ContractListResponse,
    ContractAnalysisSummary,
)

from .scan_job import (
    ScanStatus,
    ScanFeatures,
    ScanRequest,
    ScanProgress,
    ScanJobStatus,
    ScanResponse,
    ScanResultSummary,
    ScanResult,
)

__all__ = [
    # Enums
    "RiskLevel",
    "ContractType",
    "ImpactSeverity",
    "Likelihood",
    "NegotiationPriority",
    "AcceptanceLikelihood",
    "AsymmetryCategory",
    "Enforceability",
    "PrecedentType",
    "ClauseType",
    "ScanStatus",
    # Response
    "ErrorDetail",
    "APIError",
    "HealthResponse",
    "PaginationParams",
    "PaginatedResponse",
    # Clause
    "ClauseRecommendation",
    "ClauseResult",
    "ClauseTypeDetection",
    "ClauseConsequence",
    "ClauseSummary",
    "ClausePowerAsymmetry",
    "ClauseCounterOffer",
    "ClausePrecedent",
    "FullClauseAnalysis",
    # Contract
    "ContractCreate",
    "ContractUpdate",
    "ContractRead",
    "ContractListItem",
    "ContractListResponse",
    "ContractAnalysisSummary",
    # Scan Job
    "ScanFeatures",
    "ScanRequest",
    "ScanProgress",
    "ScanJobStatus",
    "ScanResponse",
    "ScanResultSummary",
    "ScanResult",
]