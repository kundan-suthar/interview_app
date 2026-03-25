# app/services/session_store.py
import time
from typing import Optional

# ── swap this with Redis in production ────────────────────────────────
_store: dict[str, dict] = {}

def start_session(session_id: str, duration_minutes: int = 45) -> dict:
    """Create a new timed session. Idempotent — won't reset if already started."""
    if session_id not in _store:
        _store[session_id] = {
            "start_time": time.time(),
            "duration_seconds": duration_minutes * 60,
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