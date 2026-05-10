from pydantic import Field
from typing import Optional
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid

class Base(DeclarativeBase):
    pass

class User(Base, SQLAlchemyBaseUserTableUUID):
   full_name: Mapped[str] = mapped_column(nullable=True)

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    customer_name: Mapped[str]

    item: Mapped[str]

    status: Mapped[str] = mapped_column(default="Order Is Placed")
