from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
from app.models.user import Base
from app.models.user_profile import UserProfile
from app.models.mock_interview import MockInterview

DATABASE_URL = f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    Base.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]