from fastapi import APIRouter, Depends, Response
from app.models.user import User
from app.auth.users import current_active_user




router = APIRouter(tags=['is_verified'])


@router.get("/api/v1/users/is_verified")
async def get_user(response: Response,current_user: User = Depends(current_active_user)):
    is_verified = current_user.is_verified
    if is_verified:
        response.set_cookie(
                key="is_verified",
                value=is_verified,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=60 * 60 * 24 * 7,
                path="/",
            )    
    return {
        "is_verified":current_user.is_verified
    }

