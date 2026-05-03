"""Precedent match model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PrecedentMatch(Base):
    """Precedent match table — stores legal precedent matches for HIGH-risk clauses."""
    
    __tablename__ = "precedent_matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    case_name: Mapped[str] = mapped_column(String, nullable=False)
    case_year: Mapped[int] = mapped_column(Integer, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_likelihood: Mapped[str] = mapped_column(String, nullable=False)  # "Very Likely", "Likely", "Uncertain", "Unlikely"
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    clause = relationship("Clause", back_populates="precedent_matches")

    def __repr__(self) -> str:
        return f"<PrecedentMatch(id={self.id}, clause_id={self.clause_id}, case_name={self.case_name})>"
