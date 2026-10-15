from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MenuItem, Order, OrderItem


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    return await db.scalar(select(Order).where(Order.id == order_id))


async def list_user_orders(db: AsyncSession, user_id: int) -> list[Order]:
    return list((await db.scalars(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))).all())


async def create_order(db: AsyncSession, *, user_id: int, address: str, lines: list[tuple[MenuItem, int]], quote: dict, promo_code: str | None) -> Order:
    restaurant_ids = {item.restaurant_id for item, _ in lines}
    if len(restaurant_ids) != 1:
        raise ValueError("All items in an order must come from the same restaurant")
    order = Order(user_id=user_id, restaurant_id=restaurant_ids.pop(), delivery_address=address,
                  total_amount=quote["total_amount"], delivery_fee=quote["delivery_fee"], driver_tip=quote["driver_tip"],
                  discount=quote["discount"], promo_code=promo_code)
    order.items = [OrderItem(menu_item_id=item.id, name=item.name, quantity=quantity, unit_price=item.price) for item, quantity in lines]
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order
