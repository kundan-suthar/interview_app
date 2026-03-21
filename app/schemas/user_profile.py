from pydantic import BaseModel, ConfigDict
from uuid import UUID

class UserProfileCreate(BaseModel):
    full_name: str
    headline: str
    bio: str
    
class UserProfileResponse(BaseModel):
    id: int
    user_id: UUID
    full_name: str | None = None  # Allow None and set default
    headline: str | None = None   # Allow None and set default
    bio: str | None = None        # Allow None and set default

    model_config = ConfigDict(from_attributes=True)
    