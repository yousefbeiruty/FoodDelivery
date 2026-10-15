from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_current_user
from app.api.tracking import manager
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.crud.orders import create_order, get_order, list_user_orders
from app.models import DeliveryStatus, MenuItem, Order
from app.schemas.api import OrderCreate, OrderRead, OrderStatusUpdate, QuoteRead, QuoteRequest, TrackingUpdate

router = APIRouter(prefix="/api/orders", tags=["Orders & Tracking"])


async def calculate_quote(db: DbSession, payload: QuoteRequest) -> tuple[dict, list[tuple[MenuItem, int]]]:
    ids = {line.menu_item_id for line in payload.items}
    if len(ids) != len(payload.items):
        raise HTTPException(status_code=422, detail="Each menu item must appear only once")
    menu_items = list((await db.scalars(select(MenuItem).where(MenuItem.id.in_(ids)))).all())
    by_id = {item.id: item for item in menu_items}
    if len(by_id) != len(ids):
        raise HTTPException(status_code=404, detail="One or more menu items were not found")
    restaurant_ids = {item.restaurant_id for item in menu_items}
    if len(restaurant_ids) != 1:
        raise HTTPException(status_code=422, detail="All items in an order must come from the same restaurant")
    lines = [(by_id[line.menu_item_id], line.quantity) for line in payload.items]
    subtotal = round(sum(item.price * quantity for item, quantity in lines), 2)
    delivery_fee = 2.5
    discount = round(subtotal * 0.10, 2) if (payload.promo_code or "").strip().upper() == "FRESH10" else 0.0
    quote = {"subtotal": subtotal, "delivery_fee": delivery_fee, "driver_tip": payload.driver_tip,
             "discount": discount, "total_amount": round(subtotal + delivery_fee + payload.driver_tip - discount, 2)}
    return quote, lines


@router.post("/quote", response_model=QuoteRead, summary="Calculate an order estimate")
async def quote(payload: QuoteRequest, db: DbSession, user: CurrentUser):
    result, _ = await calculate_quote(db, payload)
    return result


@router.post("/", response_model=OrderRead, status_code=201, summary="Place an order")
async def place_order(payload: OrderCreate, db: DbSession, user: CurrentUser):
    result, lines = await calculate_quote(db, payload)
    return await create_order(db, user_id=user.id, address=payload.delivery_address, lines=lines, quote=result, promo_code=payload.promo_code)


@router.get("/", response_model=list[OrderRead], summary="Get your order history")
async def order_history(db: DbSession, user: CurrentUser):
    return await list_user_orders(db, user.id)


@router.get("/{order_id}", response_model=OrderRead, summary="Get an order")
async def order_details(order_id: int, db: DbSession, user: CurrentUser):
    order = await get_order(db, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderRead, summary="Update delivery status and driver location")
async def update_order_status(order_id: int, payload: OrderStatusUpdate, db: DbSession, user: CurrentUser):
    order = await get_order(db, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    order.delivery_status = payload.delivery_status
    if payload.driver_name is not None: order.driver_name = payload.driver_name
    if payload.estimated_time is not None: order.estimated_time = payload.estimated_time
    if payload.driver_latitude is not None: order.driver_latitude = payload.driver_latitude
    if payload.driver_longitude is not None: order.driver_longitude = payload.driver_longitude
    await db.commit()
    await db.refresh(order)
    await manager.publish(order.id, TrackingUpdate(order_id=order.id, delivery_status=order.delivery_status, driver_name=order.driver_name,
        estimated_time=order.estimated_time, driver_latitude=order.driver_latitude, driver_longitude=order.driver_longitude).model_dump(mode="json"))
    return order


@router.websocket("/{order_id}/ws")
async def order_tracking(websocket: WebSocket, order_id: int, token: str = Query(..., description="Bearer JWT from /api/auth/token")):
    try:
        claims = decode_access_token(token)
        email = claims.get("sub")
        if not email:
            raise ValueError("Missing subject")
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return
    async with SessionLocal() as db:
        from app.crud.users import get_user_by_email
        user = await get_user_by_email(db, email)
        order = await get_order(db, order_id)
        if not user or not user.is_active or not order or order.user_id != user.id:
            await websocket.close(code=1008, reason="Order not available")
            return
        initial = TrackingUpdate(order_id=order.id, delivery_status=order.delivery_status, driver_name=order.driver_name,
            estimated_time=order.estimated_time, driver_latitude=order.driver_latitude, driver_longitude=order.driver_longitude).model_dump(mode="json")
    await manager.connect(order_id, websocket)
    try:
        await websocket.send_json(initial)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(order_id, websocket)
