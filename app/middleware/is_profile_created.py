from fastapi import Depends, HTTPException, status
from app.auth.users import current_active_user
from app.models.user import User
from app.db.database import SessionDep
from app.models.user_profile import UserProfile
from sqlalchemy import select

async def check_profile_completed(
    db: SessionDep,
    user: User = Depends(current_active_user)
):
    """
    Dependency to check if the current active user has completed their profile.
    If not, raises a 403 Forbidden error.
    """
    print("check profile completed", user.id)
    stmt = select(UserProfile.isProfileCreated).where(UserProfile.user_id == user.id)
    result = await db.execute(stmt)
    is_profile_created = result.scalar_one_or_none()
    
    if not is_profile_created:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "detail": "PROFILE_INCOMPLETE", 
                "message": "Please complete your profile first."
            }
        )
    
    return user
