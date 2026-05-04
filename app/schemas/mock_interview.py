from pydantic import BaseModel, ConfigDict
from uuid import UUID


class InterviewSessionCreate(BaseModel):
    # resume_text: str
    job_description: str
    # interview_type: str | None = None
    # duration_minutes: int | None = 5
    model_config = ConfigDict(from_attributes=True)
