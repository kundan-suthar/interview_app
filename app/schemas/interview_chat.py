from pydantic import BaseModel, ConfigDict
from uuid import UUID


class InterviewSessionCreate(BaseModel):
    user_message: str
    model_config = ConfigDict(from_attributes=True)
