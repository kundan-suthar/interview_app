from fastapi_users import BaseUserManager, UUIDIDMixin
from app.models.user import User
from app.core.config import settings
from app.auth.db import get_user_db
import uuid
from fastapi import Depends
from app.utils.tokens import create_refresh_token

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_login(self, user: User, request=None, response=None):
        if response is None:
            return

        refresh_token = create_refresh_token(str(user.id))  # ← just sign, no DB
        print(refresh_token)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            # path="/api/v1/auth",
        )

    async def on_after_register(self, user: User, request=None):
        print(f"User {user.id} has registered.")

# Dependency to get the manager
async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)