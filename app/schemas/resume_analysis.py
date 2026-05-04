from pydantic import BaseModel, ConfigDict
from uuid import UUID


class ResumeAnalysisCreate(BaseModel):
    full_name: str
    experience: float
    current_job_title: str
    required_job_title: str
    experience_level: str
    skills: list[str]
    last_company: str | None = None
    education: str | None = None
    resume_summary: str | None = None
    profile_match: int
    match_reasoning: str | None = None
    matching_skills: list[str]
    missing_skills: list[str]
    recommendation: str
    job_description: str
    model_config = ConfigDict(from_attributes=True)
