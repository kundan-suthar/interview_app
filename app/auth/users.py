from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy
)
from app.core.config import settings
from app.auth.manager import get_user_manager
from app.models.user import User
import uuid
from fastapi_users import FastAPIUsers

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy():
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

auth_backend= AuthenticationBackend(
    name="jwt", 
    transport=bearer_transport,
    get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, auth_backends=[auth_backend])