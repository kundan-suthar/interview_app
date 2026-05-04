from sqlalchemy import String, Integer, Float, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.user_profile import Base

class ProfileAnalysis(Base):
    __tablename__ = "profile_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # --- Candidate Info ---
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    experience: Mapped[float] = mapped_column(Float, nullable=False)
    current_job_title: Mapped[str] = mapped_column(String, nullable=False)
    required_job_title: Mapped[str] = mapped_column(String, nullable=False)
    experience_level: Mapped[str] = mapped_column(String, nullable=False)

    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    last_company: Mapped[str | None] = mapped_column(String, nullable=True)
    education: Mapped[str | None] = mapped_column(String, nullable=True)
    resume_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- JD Match Analysis ---
    profile_match: Mapped[int] = mapped_column(Integer, nullable=False)
    match_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    matching_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    recommendation: Mapped[str] = mapped_column(String, nullable=False)

    mock_interview_id: Mapped[int] = mapped_column(
        ForeignKey("mock_interview.id", ondelete="CASCADE"), 
        unique=True,
        nullable=False
    )

    interview: Mapped["MockInterview"] = relationship(
        "MockInterview",
        back_populates="resume_analysis"
    )
    created_at: Mapped[str] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )