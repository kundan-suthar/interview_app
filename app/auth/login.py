# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.password import PasswordHelper

from app.models.user import User
from app.auth.manager import get_user_manager, UserManager

from app.utils.tokens import (
    create_access_token,
    create_refresh_token
)

router = APIRouter()

password_helper = PasswordHelper()


@router.post("/login")
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager=Depends(get_user_manager)
):

    user = await user_manager.get_by_email(credentials.username)
    is_verified = user.is_verified
    print("is verify in login route", is_verified)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    valid = password_helper.verify_and_update(
        credentials.password,
        user.hashed_password
    )[0]

    if not valid:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_verified": is_verified
    }