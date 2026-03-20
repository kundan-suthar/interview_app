import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    full_name: str 
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
