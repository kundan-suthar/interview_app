from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import create_db_and_tables
from app.auth.users import fastapi_users, auth_backend
from app.auth.schemas import UserRead, UserCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    
    
app = FastAPI(lifespan=lifespan)

# Authentication routes (Login/Logout)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Registration route
# This router will automatically trigger UserManager.on_after_register
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)