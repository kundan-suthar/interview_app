from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import UUID

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Link this to the ID from fastapi-users (usually a UUID)
    user_id: UUID = Field(index=True, unique=True) 
    
    full_name: str
    headline: Optional[str] = None  # e.g., "Frontend Developer"
    bio: Optional[str] = None
    
    # Relationships (Optional but helpful for SQLModel)
    interviews: List["MockInterview"] = Relationship(back_populates="profile")