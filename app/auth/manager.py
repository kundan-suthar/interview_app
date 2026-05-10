from fastapi_users import BaseUserManager, UUIDIDMixin
from app.models.user import User
from app.core.config import settings
from app.auth.db import get_user_db
import uuid
from fastapi import Depends, Request
from app.utils.tokens import create_refresh_token
from app.utils.emails import send_verification_email

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_login(self, user: User, request=None, response=None):
        if response is None:
            return
        is_verified = user.is_verified
        response.set_cookie(
            key="is_verified",
            value=is_verified,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/",
        )
        refresh_token = create_refresh_token(str(user.id))  # ← just sign, no DB
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60 * 60 * 24 * 7,
            path="/",
        )
    async def on_after_request_verify(
        self,
        user: User,
        token: str, 
        request: Request = None,
    ):
        verification_link = f"http://localhost:3000/verifyEmail?token={token}"
        
        # Send email here
        await send_verification_email(user.email, verification_link)

    async def on_after_register(self, user: User, request: Request = None,):
        await self.request_verify(user)
        # verification_link = f"http://localhost:8000/auth/verify?token={token}"
        # print(request)
        # await send_verification_email(user.email, verification_link)

    async def on_after_logout(self, user: User, request=None, response=None):
        if response is None:
            return
        print("user logged out")
        response.delete_cookie(
            key="refresh_token",
            path="/",
        )

# Dependency to get the manager
async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)