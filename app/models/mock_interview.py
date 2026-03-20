import datetime as dt
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.models.user import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile

class MockInterview(Base):
    __tablename__ = "mock_interview"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profile.id"))
    
    # Interview Data
    resume_text: Mapped[str] = mapped_column(String)  # Store the extracted text from the PDF here
    job_description: Mapped[str] = mapped_column(String)
    
    # Metadata
    status: Mapped[str] = mapped_column(String(50), default="pending") # e.g., "active", "completed"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    
    # LLM Context
    # If using OpenAI/LangChain, store the thread_id to resume chats
    thread_id: Mapped[str | None] = mapped_column(String(255))

    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="interviews")