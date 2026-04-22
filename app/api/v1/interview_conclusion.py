from fastapi import APIRouter
from app.models.interview_conclusion import InterviewConclusion
from app.models.interview_session import InterviewSession
from app.models.mock_interview import MockInterview
from app.models.resume_analysis import ProfileAnalysis
from sqlalchemy import select
from fastapi import HTTPException
from app.db.database import SessionDep

router = APIRouter(tags=['conclusion'])
@router.get("/interview/{session_id}/conclusion")
async def get_conclusion(session_id: str, db: SessionDep):

    # Single join query to get everything
    result = await db.execute(
        select(InterviewConclusion, InterviewSession, ProfileAnalysis)
        .join(InterviewSession, InterviewSession.session_id == InterviewConclusion.session_id)
        .join(MockInterview, MockInterview.id == InterviewConclusion.mock_interview_id)
        .join(ProfileAnalysis, ProfileAnalysis.mock_interview_id == MockInterview.id)
        .where(InterviewConclusion.session_id == session_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404)

    conclusion, session, profile = row

    return {
        # From ProfileAnalysis
        "required_job_title": profile.required_job_title,
        "candidate_experince":profile.experience,
        # From InterviewSession
        "date": session.created_at,
        "transcript": session.messages,
        # From InterviewConclusion
        "analysis_status":      conclusion.analysis_status,  # show loader if "processing"
        "performance_summary":  conclusion.performance_summary,
        "ratings": {
            "technical_depth":  conclusion.technical_depth,
            "communication":    conclusion.communication,
            "confidence":       conclusion.confidence,
        },
        "hirability_score":     conclusion.hirability_score,
        "key_strengths":        conclusion.key_strengths,
        "areas_to_improve":     conclusion.areas_to_improve,
        "actionable_items":     conclusion.actionable_items,
       
    }