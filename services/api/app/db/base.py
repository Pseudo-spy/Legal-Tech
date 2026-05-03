"""SQLAlchemy declarative base and model discovery."""

from sqlalchemy.orm import declarative_base

# This is the base class for all ORM models
# Alembic uses this to auto-discover all models during migrations
Base = declarative_base()

# Import all models here so Alembic can find them during `alembic revision --autogenerate`
# This prevents the "Target database is not up to date" error
from app.models.user import User  # noqa: F401, E402
from app.models.contract import Contract  # noqa: F401, E402
from app.models.clause import Clause  # noqa: F401, E402
from app.models.scan_job import ScanJob  # noqa: F401, E402
from app.models.analysis_result import AnalysisResult  # noqa: F401, E402
from app.models.counter_offer import CounterOffer  # noqa: F401, E402
from app.models.precedent_match import PrecedentMatch  # noqa: F401, E402
from app.models.report import Report  # noqa: F401, E402
from app.models.embedding import Embedding  # noqa: F401, E402
