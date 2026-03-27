# app/api/routes/interview.py

import json
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage
from app.services.interview_service import interview_agent, build_system_prompt
from app.services.session_store import start_session, get_time_state, end_session
# from app.services.evaluator_service import evaluate_interview
from app.auth.users import current_active_user
from app.models.user import User
from app.schemas.mock_interview import InterviewSessionCreate
import uuid
from app.utils.extract_pdf import extract_text_from_upload
from app.services.interview_analyze import analyze_resume_function

router = APIRouter()

@router.post("/api/v1/interview/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: User = Depends(current_active_user),
):
    """Call this once before the first message to register the timer."""
    texts = await extract_text_from_upload(resume)
    res = await analyze_resume_function({
        "text": texts,
        "job_description": job_description
    })  
    print("-----------------------")
    print("res",res)
    return res
    
@router.post("/interview/start")
async def start_interview(
    interview_type: str = Form(default="technical"),
    duration_minutes: int = Form(default=5),
    current_user: User = Depends(current_active_user),
):
    """Call this once before the first message to register the timer."""
    session_id = str(uuid.uuid4())
    session = start_session(session_id, duration_minutes)
    return {
        "session_id": session_id,
        "duration_minutes": duration_minutes,
        "started_at": session["start_time"],
    }

@router.post("/interview/chat")
async def chat_with_interviewer(
    session_id: str,
    user_message: str,
    interview_type: str = "technical",
):
    # ── Get time state — reject if session not started ─────────────────
    time_state = get_time_state(session_id)
    if time_state is None:
        raise HTTPException(
            status_code=400,
            detail="Session not found. Call /interview/start first."
        )

    config = {"configurable": {"thread_id": session_id}}
    system_prompt = build_system_prompt(interview_type, time_state)
    is_final = time_state["phase"] in ("hard_stop", "expired")

    async def event_generator():
        # ── Emit time state immediately so client can update UI ────────
        yield f"event: time\ndata: {json.dumps(time_state)}\n\n"

        # ── If already expired, skip agent entirely ────────────────────
        if time_state["phase"] == "expired":
            closing = json.dumps({"text": "Time's up — interview has ended."})
            yield f"event: token\ndata: {closing}\n\n"
            yield f"event: status\ndata: {json.dumps({'status': 'completed'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        # ── Stream agent response ──────────────────────────────────────
        full_response = []
        async for chunk, metadata in interview_agent.astream(
            {
                "messages": [
                    SystemMessage(content=system_prompt),
                    {"role": "user", "content": user_message},
                ]
            },
            config=config,
            stream_mode="messages",
        ):
            if hasattr(chunk, "content") and isinstance(chunk.content, str):
                if chunk.content:
                    full_response.append(chunk.content)
                    yield f"event: token\ndata: {chunk.content}\n\n"

        full_text = "".join(full_response)

        # ── Detect natural close ───────────────────────────────────────
        closing_phrases = ["that's all the time", "wraps up", "thank you for your time"]
        naturally_closed = any(p in full_text.lower() for p in closing_phrases)
        just_ended = is_final or naturally_closed

        status = "completed" if just_ended else "ongoing"
        yield f"event: status\ndata: {json.dumps({'status': status, **time_state})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

        # ── Auto eval when interview ends ──────────────────────────────
        if just_ended:
            try:
                final_state = await interview_agent.aget_state(config)
                messages = final_state.values.get("messages", [])
                print(messages)
                # evaluation = await evaluate_interview(messages, interview_type)
                # yield f"event: eval\ndata: {json.dumps(evaluation)}\n\n"
                end_session(session_id)
            except Exception as e:
                yield f"event: eval_error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/interview/time/{session_id}")
async def get_time(session_id: str):
    """Poll this endpoint to show a live countdown timer on the frontend."""
    time_state = get_time_state(session_id)
    if not time_state:
        raise HTTPException(status_code=404, detail="Session not found")
    return time_state