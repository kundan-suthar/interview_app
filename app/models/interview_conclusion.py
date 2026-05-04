from sqlalchemy.orm import relationship
from sqlalchemy import Float
from app.models.user import Base

from sqlalchemy import  String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import  Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from .interview_session import InterviewSession

class InterviewConclusion(Base):
    __tablename__ = "interview_conclusion"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
     # --- Foreign Keys ---
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.session_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    mock_interview_id: Mapped[int] = mapped_column(
        ForeignKey("mock_interview.id", ondelete="CASCADE"),
        nullable=False
    )
    # --- LLM-generated fields ---
    performance_summary: Mapped[str] = mapped_column(Text, nullable=True)

    # Ratings out of 5
    technical_depth: Mapped[float] = mapped_column(Float, nullable=True)
    communication: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Hirability out of 10
    hirability_score: Mapped[float] = mapped_column(Float, nullable=True)

    # Arrays
    key_strengths: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    areas_to_improve: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    actionable_items: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)

    analysis_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    session: Mapped["InterviewSession"] = relationship("InterviewSession", backref="conclusion")
