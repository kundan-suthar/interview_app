from pydantic import BaseModel, ConfigDict
from uuid import UUID

class UserProfileCreate(BaseModel):
    headline: str
    bio: str
    skills: str | None = None 
    
class UserProfileResponse(BaseModel):
    id: int
    user_id: UUID
    headline: str | None = None   # Allow None and set default
    bio: str | None = None 
    skills: str | None = None 
    model_config = ConfigDict(from_attributes=True)
    