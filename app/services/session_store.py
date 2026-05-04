# app/services/session_store.py
import time
from typing import Optional
from app.models.resume_analysis import ProfileAnalysis
from app.models.mock_interview import MockInterview
from sqlalchemy import select
from app.db.database import SessionDep
# ── swap this with Redis in production ────────────────────────────────
_store: dict[str, dict] = {}

async def start_session( db:SessionDep,mock_interview_id:int, session_id: str, duration_minutes: int = 5, ) -> dict:
    """Create a new timed session. Idempotent — won't reset if already started."""
    result = await db.execute(
        select(ProfileAnalysis).where(ProfileAnalysis.mock_interview_id == mock_interview_id)
    )
    result2 = await db.execute(
        select(MockInterview).where(MockInterview.id == mock_interview_id)
    )
    profile = result.scalar_one_or_none()
    mock_interview = result2.scalar_one_or_none()
    if not profile and not mock_interview:
        raise ValueError(f"No profile analysis and mock interview found for mock_interview_id={mock_interview_id}")

    # ✅ serialize to plain dict at storage time
    profile_data = {
        "name": profile.full_name,
        "required_job_title": profile.required_job_title,
        "years_of_experience": profile.experience,
        "skills": profile.skills,
        "last_company": profile.last_company,
        "education": profile.education,
        "resume_summary": profile.resume_summary,
        "job_description": mock_interview.job_description,
    }
    

    if session_id not in _store:
        _store[session_id] = {
            "start_time": time.time(),
            "duration_seconds": duration_minutes * 60,
            "profile_data": profile_data
        }
    return _store[session_id]

def get_time_state(session_id: str) -> Optional[dict]:
    """Returns elapsed, remaining, percent, and phase for this session."""
    session = _store.get(session_id)
    if not session:
        return None

    elapsed = time.time() - session["start_time"]
    total = session["duration_seconds"]
    remaining = max(0.0, total - elapsed)
    percent = min(100.0, (elapsed / total) * 100)

    if percent >= 100:
        phase = "expired"
    elif percent >= 90:
        phase = "hard_stop"    # force close, no new questions
    elif percent >= 75:
        phase = "wrap_up"      # signal to finish up
    else:
        phase = "normal"

    return {
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "remaining_minutes": round(remaining / 60, 1),
        "percent_used": round(percent, 1),
        "phase": phase,
    }
def get_profile_data(session_id: str) -> Optional[dict]:
    """Returns profile data for this session."""
    session = _store.get(session_id)
    if not session:
        return None
    return session["profile_data"]
def end_session(session_id: str):
    _store.pop(session_id, None)


# ── Redis version (production) ────────────────────────────────────────
# import redis.asyncio as redis
# r = redis.from_url(settings.REDIS_URL)
#
# async def start_session(session_id: str, duration_minutes: int = 45):
#     key = f"interview:{session_id}"
#     exists = await r.exists(key)
#     if not exists:
#         await r.hset(key, mapping={
#             "start_time": time.time(),
#             "duration_seconds": duration_minutes * 60
#         })
#         await r.expire(key, duration_minutes * 60 + 300)  # auto-cleanup