from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.auth.manager import get_user_manager, UserManager
from app.auth.users import get_jwt_strategy
from app.utils.tokens import decode_refresh_token, create_refresh_token
import uuid

router = APIRouter()

@router.post("/api/v1/auth/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    user_manager: UserManager = Depends(get_user_manager),
):
    refresh_token = request.cookies.get("refresh_token")
    print("refresh token referehhhh filee----", refresh_token) 
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = decode_refresh_token(refresh_token)
    user_id = payload.get("sub")

    user = await user_manager.get(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    jwt_strategy = get_jwt_strategy()
    access_token = await jwt_strategy.write_token(user)

    new_refresh_token = create_refresh_token(user_id)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        # path="/api/v1/auth",
    )

    return {"access_token": access_token, "token_type": "bearer"}