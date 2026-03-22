from fastapi import APIRouter
from app.services.interview_service import interview_agent
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/chat")
async def chat_with_interviewer(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id}}
    
    state = await interview_agent.aget_state(config)
    print(f"[DEBUG] thread={session_id}, messages so far={len(state.values.get('messages', []))}")
    

    async def event_generator():
        async for chunk, metadata in interview_agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},  # ← was ...
            config=config,
            stream_mode="messages",
        ):
            if hasattr(chunk, "content") and isinstance(chunk.content, str):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"  
    return StreamingResponse(event_generator(), media_type="text/event-stream")