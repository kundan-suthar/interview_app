from sqlalchemy import select
from app.db.database import SessionDep
from fastapi import APIRouter
from app.models.user import Order
from sqlalchemy.orm import Session
from app.tasks import process_order
from app.schemas.order import OrderResponse, OrderCreate

router = APIRouter()

@router.post("/place-order", response_model=OrderResponse)
async def place_order(order:OrderCreate,db:SessionDep):
    new_order = Order(customer_name=order.customer_name, item=order.item)
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    #start bg job
    process_order.delay(new_order.id)

    return new_order

@router.get("/order-status/{order_id}", response_model=OrderResponse)
async def get_order_status(order_id: int, db:SessionDep):
    result = await db.exec(select(Order).where(Order.id == order_id))
    order = result.one_or_none()
    if not order:
        return {"error": "Order not found"}
    return order