from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from .user_profile import UserProfile

class MockInterview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="userprofile.id")
    
    # Interview Data
    resume_text: str  # Store the extracted text from the PDF here
    job_description: str
    
    # Metadata
    status: str = Field(default="pending") # e.g., "active", "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # LLM Context
    # If using OpenAI/LangChain, store the thread_id to resume chats
    thread_id: Optional[str] = None 

    profile: UserProfile = Relationship(back_populates="interviews")