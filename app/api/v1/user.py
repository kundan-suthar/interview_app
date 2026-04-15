from fastapi import APIRouter, Depends, status, HTTPException, Response
from app.db.database import SessionDep
from app.models.user import User
from sqlalchemy import select
from app.auth.users import current_active_user
from app.models.user import User
from app.schemas.user_profile import UserProfileCreate, UserProfileResponse


router = APIRouter(tags=['profile'])

@router.get("/api/v1/users/me")
async def get_user(db:SessionDep,current_user: User = Depends(current_active_user)):
    query = select(User.full_name, User.email).where(User.id == current_user.id)
    result = await db.execute(query)
    data = result.first()
    return {
        "full_name": data.full_name,
        "email": data.email
    }