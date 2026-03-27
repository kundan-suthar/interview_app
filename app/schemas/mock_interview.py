from pydantic import BaseModel, ConfigDict
from uuid import UUID


class InterviewSessionCreate(BaseModel):
    interview_type: str
    duration_minutes: int | None = 5
    model_config = ConfigDict(from_attributes=True)
