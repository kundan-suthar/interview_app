from pydantic import BaseModel, ConfigDict
from uuid import UUID

class OrderCreate(BaseModel):
    customer_name: str
    item: str

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    item: str
    status: str