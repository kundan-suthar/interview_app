from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.database import create_db_and_tables
from app.auth.users import fastapi_users, auth_backend
from app.auth.schemas import UserRead, UserCreate
from app.api.v1 import profile
from app.api.v1 import interview_chat
from app.auth import refresh

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    
    
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL
    allow_credentials=True,  # ← this must be True
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes (Login/Logout)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/v1/auth",
    tags=["auth"],
)

# Registration route
# This router will automatically trigger UserManager.on_after_register
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/v1/auth", 
    tags=["auth"],
)
app.include_router(refresh.router, tags=["auth"])

app.include_router(profile.router, tags=["profile"])
app.include_router(interview_chat.router, tags=["interview_chat"])