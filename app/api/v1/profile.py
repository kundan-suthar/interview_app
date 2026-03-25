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


@router.post("/api/v1/profile", response_model=UserProfileResponse)
async def create_or_update_profile(
    db: SessionDep, 
    profile_in: UserProfileCreate,
    current_user: User = Depends(current_active_user)
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        # UPDATE
        for key, value in profile_in.model_dump().items():
            setattr(profile, key, value)
    else:
        # CREATE
        profile = UserProfile(
            **profile_in.model_dump(),
            user_id=current_user.id
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return profile