from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Restaurant


async def list_restaurants(db: AsyncSession, search: str | None, category: str | None) -> list[Restaurant]:
    stmt = select(Restaurant)
    if search:
        stmt = stmt.where(func.lower(Restaurant.name).contains(search.lower()))
    results = list((await db.scalars(stmt.order_by(Restaurant.name))).all())
    if category:
        results = [restaurant for restaurant in results if category.lower() in [tag.lower() for tag in restaurant.category_tags]]
    return results


async def get_restaurant_menu(db: AsyncSession, restaurant_id: int) -> Restaurant | None:
    restaurant = await db.scalar(
        select(Restaurant)
        .options(selectinload(Restaurant.menu_items))
        .where(Restaurant.id == restaurant_id)
    )
    if restaurant:
        restaurant.menu_items.sort(key=lambda item: (item.category, item.name))
    return restaurant
