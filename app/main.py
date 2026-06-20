from app.api.v1 import dashboard_data
from app.api.v1 import interview_conclusion
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.database import create_db_and_tables
from app.auth.users import fastapi_users, auth_backend
from app.auth.schemas import UserRead, UserCreate
from app.api.v1 import profile
from app.api.v1 import interview_chat
from app.api.v1 import user
from app.api.v1 import is_verified
from app.auth import refresh,logout,login
from app.middleware.is_profile_created import check_profile_completed
from fastapi import Depends

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    
    
app = FastAPI(lifespan=lifespan)

@app.api_route(
    "/health",
    methods=["GET", "HEAD"],
    tags=["health"]
)
async def health_check():
    return {
        "status": "ok",
        "message": "server is running"
    }

origins = [
    "http://localhost:3000",
    "https://interview-app-frontend-ten.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://interview-app-frontend-ten.vercel.app"],  # your frontend URL
    allow_credentials=True,  # ← this must be True
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes (Login/Logout)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(logout.router, tags=["auth"])
# Registration route
# This router will automatically trigger UserManager.on_after_register
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/v1/auth", 
    tags=["auth"],
)
app.include_router(refresh.router, tags=["auth"])
app.include_router(user.router, dependencies=[Depends(check_profile_completed)])
app.include_router(profile.router, tags=["profile"])
# app.include_router(interview_chat.router, tags=["interview_chat"], dependencies=[Depends(check_profile_completed)])
app.include_router(interview_chat.router, tags=["interview_chat"])
app.include_router(interview_conclusion.router, tags=["interview_conclusion"])
app.include_router(dashboard_data.router, tags=["dashboard"])
app.include_router(is_verified.router, tags=["is_verified"])
app.include_router(login.router, tags=["custom_login"])