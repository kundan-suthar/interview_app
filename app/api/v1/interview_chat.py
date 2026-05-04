# app/api/routes/interview.py

from sqlalchemy import update
from sqlalchemy.orm import selectinload
from app.db.database import async_session_maker
from app.services.interview_conclude import InterviewConclusionService
from app.models.interview_session import InterviewSession
import json
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage
from app.services.interview_service import interview_agent, build_system_prompt
from app.services.session_store import start_session, get_time_state, end_session, get_profile_data
# from app.services.evaluator_service import evaluate_interview
from app.auth.users import current_active_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.mock_interview import MockInterview
from app.models.resume_analysis import ProfileAnalysis
from app.schemas.resume_analysis import ResumeAnalysisCreate
import uuid
from datetime import datetime
from app.utils.extract_pdf import extract_text_from_upload
from app.services.interview_analyze import analyze_resume_function
from app.db.database import SessionDep
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from groq import Groq
import os
from openai import OpenAI
import asyncio, base64, json, re
from langchain_core.messages import HumanMessage, AIMessage
from app.utils.serialize import serialize_messages
from fastapi import BackgroundTasks

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
    return res
    
@router.post("/api/v1/interview/start")
async def start_interview(
    # interview_type: str = Form(default="technical"),
    # duration_minutes: int = Form(default=5),
    db:SessionDep, 
    request_body: ResumeAnalysisCreate,
    current_user: User = Depends(current_active_user),
):
    """Call this once before the first message to register the timer."""
    # print("-----------------------")
    # print(request_body)
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )

    interview_type = "technical"
    duration_minutes = 5
    session_id = str(uuid.uuid4())
    profile = result.scalar_one_or_none()

    profile_id = profile.id if profile else None
    if not profile_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    mock_interview = MockInterview(
        profile_id=profile_id,
        status="pending",
        job_description=request_body.job_description,
        created_at=datetime.utcnow(),
        thread_id=session_id
    )
    db.add(mock_interview)
    await db.commit()
    await db.refresh(mock_interview)
    if mock_interview.id:
        resume_analysis = ProfileAnalysis(
            mock_interview_id=mock_interview.id,
            full_name=request_body.full_name,
            experience=request_body.experience,
            current_job_title=request_body.current_job_title,
            required_job_title=request_body.required_job_title,
            experience_level=request_body.experience_level,
            skills=request_body.skills,
            last_company=request_body.last_company,
            education=request_body.education,
            resume_summary=request_body.resume_summary,
            profile_match=request_body.profile_match,
            match_reasoning=request_body.match_reasoning,
            matching_skills=request_body.matching_skills,
            missing_skills=request_body.missing_skills,
            recommendation=request_body.recommendation,
        )
        db.add(resume_analysis)
        await db.commit()
        await db.refresh(resume_analysis)
    session = await start_session(db,mock_interview.id, session_id, duration_minutes)
    return {
        "session_id": session_id,
        "duration_minutes": duration_minutes,
        "started_at": session["start_time"],
    }
# from groq import Groq
# from fastapi.responses import StreamingResponse

# ── Semantic flush config ────────────────────────────────────────────────────
FLUSH_PATTERN = re.compile(r'(?<=[.?!;])\s+|(?<=,)\s+(?=\w{4,})')
MIN_CHUNK_CHARS = 30        # don't TTS tiny fragments
MAX_CHUNK_CHARS = 200       # force-flush if buffer gets too long


async def _tts_chunk_to_b64(client: OpenAI, text: str) -> str:
    """Run Groq TTS synchronously in a thread, return base64 WAV string."""
    def _call():
        # resp = client.audio.speech.create(
        #     model="canopylabs/orpheus-v1-english",
        #     voice="troy",
        #     input=text.strip(),
        #     response_format="wav",
        # )
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="onyx",
            input=text.strip(),
            instructions=(
                "Speak in a deep, calm, and authoritative tone like a senior engineer or engineering manager. "
                "Be measured and precise but speak at a natural conversational pace — not slow, not rushed. "
                "Think of the rhythm of a confident person in a meeting who speaks clearly without dragging words. "
                "Pause briefly only at question marks and full stops, not between every clause. "
                "Sound evaluative but not cold — professional throughout."
            ),
            speed=1.25,
            response_format="wav",
        ) as resp:
            # iter_bytes() is on resp, not on the context manager
            return b"".join(resp.iter_bytes(chunk_size=4096))

    wav_bytes = await asyncio.get_event_loop().run_in_executor(None, _call)
    return base64.b64encode(wav_bytes).decode()


def _should_flush(buffer: str) -> tuple[bool, str, str]:
    """
    Check if buffer has a complete semantic chunk to flush.
    Returns (should_flush, chunk_to_send, remainder).
    """
    if len(buffer) < MIN_CHUNK_CHARS:
        return False, "", buffer

    # Force-flush if too long regardless of punctuation
    if len(buffer) >= MAX_CHUNK_CHARS:
        # Try to cut at last word boundary
        cut = buffer[:MAX_CHUNK_CHARS].rfind(' ')
        cut = cut if cut > MIN_CHUNK_CHARS else MAX_CHUNK_CHARS
        return True, buffer[:cut], buffer[cut:].lstrip()

    # Find the last semantic boundary
    for m in reversed(list(FLUSH_PATTERN.finditer(buffer))):
        chunk = buffer[:m.start() + 1].strip()
        remainder = buffer[m.end():]
        if len(chunk) >= MIN_CHUNK_CHARS:
            return True, chunk, remainder

    return False, "", buffer


@router.post("/api/v1/interview/chat")
async def chat_with_interviewer(
    session_id: str,
    user_message: str,
    db: SessionDep,
    background_tasks: BackgroundTasks,
    interview_type: str = "technical",
    current_user: User = Depends(current_active_user),
):
    time_state = get_time_state(session_id)
    profile_data = get_profile_data(session_id)

    if not profile_data or not time_state:
        raise HTTPException(status_code=400, detail="Session not found. Call /start first.")

    config = {"configurable": {"thread_id": session_id}}
    system_prompt = build_system_prompt(profile_data, interview_type, time_state)
    is_final = time_state["phase"] in ("hard_stop", "expired")
    groq_client = Groq()                     # uses GROQ_API_KEY from env
    open_client = OpenAI()
    async def event_generator():
        # 1. Emit time state immediately
        yield f"event: time\ndata: {json.dumps(time_state)}\n\n"

        if time_state["phase"] == "expired" or time_state["phase"] == "hard_stop":
            yield f"event: token\ndata: {json.dumps({'text': 'Time is up — interview has ended.'})}\n\n"
            yield f"event: status\ndata: {json.dumps({'status': 'completed'})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            # try:
            #     final_state = await interview_agent.aget_state(config)
            #     messages = final_state.values.get("messages", [])
            #     print("messages------------------------")
            #     print(messages)
            #     end_session(session_id)
            # except Exception as e:
            #     yield f"event: eval_error\ndata: {json.dumps({'error': str(e)})}\n\n"
            # return
            try:
                print("control reached here 1")
                import traceback; traceback.print_exc()  
                session = await persist_interview_session(session_id, config, db, current_user, interview_type)
                print(f"session type: {type(session)}")
                print(f"session id: {session.session_id if session else 'None'}")
                
                # Query mock interview
                result = await db.execute(
                    select(MockInterview)
                    .where(MockInterview.thread_id == session_id)
                    .options(selectinload(MockInterview.resume_analysis))  # ✅ eager load
                )
                mock_interview = result.scalar_one_or_none()
                print("session------------------------")
                print(session)
                
                if session:
                    print("adding to background job")
                    asyncio.create_task(generate_conclusion_safe(session, mock_interview))
                    # background_tasks.add_task(generate_conclusion_safe, session, mock_interview)
            except Exception as e:
                yield f"event: eval_error\ndata: {json.dumps({'error': str(e)})}\n\n"
            finally:
                end_session(session_id)
            return

        # 2. Stream LLM + semantic TTS in parallel
        full_response: list[str] = []
        tts_buffer = ""
        pending_tts: asyncio.Task | None = None

        # async def flush_tts(text: str):
        #     """Kick off a TTS call; yield the audio event when done."""
        #     # b64 = await _tts_chunk_to_b64(groq_client, text)
        #     b64 = await _tts_chunk_to_b64(open_client, text)
        #     return b64

        # tts_queue: asyncio.Queue[str] = asyncio.Queue()   # queued b64 chunks

        # async def tts_worker():
        #     """Worker that serialises TTS calls so audio arrives in order."""
        #     while True:
        #         text = await tts_queue.get()
        #         if text is None:           # sentinel
        #             break
        #         b64 = await flush_tts(text)
        #         # We yield via a shared list; see collector below
        #         audio_chunks.append(b64)
        #         tts_queue.task_done()

        # audio_chunks: list[str] = []       # filled by worker, drained below
        # worker = asyncio.create_task(tts_worker())

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
            if hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                token = chunk.content
                full_response.append(token)
                tts_buffer += token

                # Always stream the text token immediately
                yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"

                # Check semantic boundary
                # should, chunk_text, tts_buffer = _should_flush(tts_buffer)
                # if should:
                #     await tts_queue.put(chunk_text)

                # Drain any ready audio chunks
                # while audio_chunks:
                #     b64 = audio_chunks.pop(0)
                #     yield f"event: audio\ndata: {json.dumps({'audio': b64, 'format': 'wav'})}\n\n"

        # Flush remaining buffer
        # if tts_buffer.strip():
        #     await tts_queue.put(tts_buffer.strip())

        # # Signal worker to stop and wait
        # await tts_queue.put(None)
        # await worker

        # # Drain remaining audio
        # while audio_chunks:
        #     b64 = audio_chunks.pop(0)
        #     yield f"event: audio\ndata: {json.dumps({'audio': b64, 'format': 'wav'})}\n\n"

        # 3. Status + done
        full_text = "".join(full_response)
        closing_phrases = ["that's all the time", "wraps up", "thank you for your time"]
        naturally_closed = any(p in full_text.lower() for p in closing_phrases)
        just_ended = is_final or naturally_closed
        status = "completed" if just_ended else "ongoing"

        yield f"event: status\ndata: {json.dumps({'status': status, **time_state})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

        if just_ended:
            # try:
            #     final_state = await interview_agent.aget_state(config)
            #     messages = final_state.values.get("messages", [])
            #     print("messages------------------------")
            #     print(messages)
            #     end_session(session_id)
            # except Exception as e:
            #     yield f"event: eval_error\ndata: {json.dumps({'error': str(e)})}\n\n"
            try:
                print("control reached here 2")
                session = await persist_interview_session(session_id, config, db, current_user, interview_type)
                print(f"session type: {type(session)}")
                print(f"session id: {session.session_id if session else 'None'}")
                
                # Query mock interview
                result = await db.execute(select(MockInterview).where(MockInterview.thread_id == session_id))
                mock_interview = result.scalar_one_or_none()
                print("session------------------------")
                print(session)
                
                if session:
                    print(f"Creating async task for session {session.session_id}")
                    asyncio.create_task(generate_conclusion_safe(session, mock_interview))
                    # background_tasks.add_task(generate_conclusion_safe, session, mock_interview)
            except Exception as e:
                import traceback; traceback.print_exc()  
                yield f"event: eval_error\ndata: {json.dumps({'error': str(e)})}\n\n"
            finally:
                end_session(session_id)

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



async def persist_interview_session(
    session_id: str,
    config: dict,
    db: SessionDep,
    current_user: User,
    interview_type: str,
    status: str = "completed",
):
    """Extract final state from LangGraph and write to SQL DB."""
   
    final_state = await interview_agent.aget_state(config)
    messages = final_state.values.get("messages", [])
    serialized = serialize_messages(messages)
    try:
        stmt = (
            insert(InterviewSession)
            .values(
                session_id=session_id,
                user_id=current_user.id,
                interview_type=interview_type,
                messages=serialized,
                status=status,
            )
            .on_conflict_do_update(
                index_elements=["session_id"],
                set_={
                    "messages": serialized,
                    "status": status,
                    "completed_at": func.now(),
                },
            )
            .returning(InterviewSession) 
        )
        stmt2 = (
                update(MockInterview)
                .where(MockInterview.thread_id == session_id)
                .values(status="completed")
            )
        res = await db.execute(stmt)
        await db.execute(stmt2)
        await db.commit()
        # Fetch the session separately
        result = await db.execute(
            select(InterviewSession).where(InterviewSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        print("session", session)
        
        if session is None:
            raise ValueError(f"Failed to retrieve session after upsert: {session_id}")
        
        # No need to refresh since we just fetched it
        return session
    except Exception as e:
        import traceback; traceback.print_exc()
        raise e
        
async def generate_conclusion_safe(session: InterviewSession, mock_interview: MockInterview):
    """
    Wrapper that creates its own DB session.
    Never raises — logs errors silently so it never crashes the main flow.
    """
    try:
        async with async_session_maker() as db:  # fresh session
            conclusion_service = InterviewConclusionService()
            print("conclusion_service",conclusion_service)
            await conclusion_service.generate_and_save(
                session=session,
                mock_interview=mock_interview,
                db=db
            )
    except Exception as e:
        # Log but never propagate — this is fire-and-forget
        print(f"[ConclusionService] Failed for session {session.session_id}: {e}")
        import traceback; traceback.print_exc()