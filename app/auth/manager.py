from fastapi_users import BaseUserManager, UUIDIDMixin
from app.models.user import User
from app.core.config import settings
from app.auth.db import get_user_db
import uuid
from fastapi import Depends

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request=None):
        print(f"User {user.id} has registered.")

# Dependency to get the manager
async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)