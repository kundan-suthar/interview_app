from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated
from fastapi import Depends
from app.models.user import Base
from app.models.user_profile import UserProfile
from app.models.mock_interview import MockInterview
from dotenv import load_dotenv
load_dotenv()
import os 

# Use asyncpg for PostgreSQL
# DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, pool_size=20,  # Adjust based on your needs
    max_overflow=10,
    pool_pre_ping=True,  # Critical: Check connection before using
    pool_recycle=3600,   # Recycle connections every hour
    echo=False,)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with async_session_maker() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]