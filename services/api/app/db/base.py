"""SQLAlchemy declarative base and model discovery."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _register_models():
    """Register all models with Base. Called lazily to avoid circular imports."""
    from services.api.app.models.user import User  # noqa: F401
    from services.api.app.models.contract import Contract  # noqa: F401
    from services.api.app.models.clause import Clause  # noqa: F401
    from services.api.app.models.scan_job import ScanJob  # noqa: F401
    from services.api.app.models.analysis_result import AnalysisResult  # noqa: F401
    from services.api.app.models.counter_offer import CounterOffer  # noqa: F401
    from services.api.app.models.precedent_match import PrecedentMatch  # noqa: F401
    from services.api.app.models.report import Report  # noqa: F401
    from services.api.app.models.embedding import Embedding  # noqa: F401
