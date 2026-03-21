from fastapi import APIRouter, Depends, status, HTTPException, Response
from app.db.database import SessionDep
from app.models.user_profile import UserProfile
from sqlalchemy import select
from app.auth.users import current_active_user
from app.models.user import User
from app.schemas.user_profile import UserProfileCreate, UserProfileResponse


router = APIRouter(tags=['profile'])

@router.get("/profile")
async def get_profile(db:SessionDep,current_user: User = Depends(current_active_user)):
    all_profiles =  await db.execute(select(UserProfile))
    return all_profiles.scalars().all()


@router.post("/profile", response_model=UserProfileResponse)
async def create_profile(
    db: SessionDep, 
    profile_in: UserProfileCreate, # Renamed to avoid conflict
    current_user: User = Depends(current_active_user)
):
    # 1. Check if it exists
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    existing_profile = result.scalar_one_or_none()

    if not existing_profile:
        # 2. Create new using the renamed 'profile_in'
        # Note: .model_dump() is the Pydantic v2 version of .dict()
        new_profile = UserProfile(**profile_in.model_dump(), user_id=current_user.id)
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile

    # 3. If it already exists, you can return it or update it
    return existing_profile

