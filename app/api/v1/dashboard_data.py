from fastapi import HTTPException
from sqlalchemy.connectors import asyncio
from app.models.interview_conclusion import InterviewConclusion
from app.models.resume_analysis import ProfileAnalysis
from sqlalchemy import join
from app.models.mock_interview import MockInterview
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.models.user_profile import UserProfile
from app.models.user import User
from fastapi import Depends
from app.auth.users import current_active_user
from app.db.database import SessionDep
from fastapi import APIRouter
from sqlalchemy import select


router = APIRouter(tags=['dashboard'])
@router.get("/api/dashboard/data")
async def get_dashboard_data(db: SessionDep, current_user: User = Depends(current_active_user)):
    try:

        # Query 1: Get profile_id
        profile_id_res = await db.execute(
            select(UserProfile.id).where(UserProfile.user_id == current_user.id)
        )
        profile_id = profile_id_res.scalar_one_or_none()
        if not profile_id:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Query 2: Total + completed counts in ONE query
        stmt_counts = select(
            func.count(MockInterview.id).label("total"),
            func.count(MockInterview.id).filter(MockInterview.status == "completed").label("completed"),
        ).where(MockInterview.profile_id == profile_id)

        # Query 3: Table data
        stmt_table = (
            select(
                MockInterview.id,
                MockInterview.thread_id,
                MockInterview.status,
                MockInterview.created_at,
                ProfileAnalysis.required_job_title,
                ProfileAnalysis.full_name,
                ProfileAnalysis.profile_match
            )
            .join(ProfileAnalysis, MockInterview.id == ProfileAnalysis.mock_interview_id)
            .where(MockInterview.profile_id == profile_id)
        )

        # Query 4: Hirability scores via subquery (no separate thread_id fetch)
        thread_id_subquery = (
            select(MockInterview.thread_id)
            .where(MockInterview.profile_id == profile_id)
            .scalar_subquery()
        )
        stmt_scores = select(InterviewConclusion.hirability_score).where(
            InterviewConclusion.session_id.in_(thread_id_subquery),
            InterviewConclusion.hirability_score.is_not(None),
        )

        # Execute sequentially (same session — this is correct)
        counts_res = await db.execute(stmt_counts)
        table_res = await db.execute(stmt_table)
        scores_res = await db.execute(stmt_scores)

        counts = counts_res.one()
        table_data = table_res.mappings().all()
        hirability_scores = scores_res.scalars().all()

        avg_score = (
            round(sum(hirability_scores) / len(hirability_scores), 2)
            if hirability_scores else None
        )

        return {
            "current_user_interviews": counts.total,
            "current_user_completed_interviews": counts.completed,
            "table_data": table_data,
            "hirability_score": avg_score,
        }
    except Exception as e:
        import traceback; traceback.print_exc()  
        return f"error {e}"
    