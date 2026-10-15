from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.crud.restaurants import get_restaurant_menu, list_restaurants
from app.schemas.api import RestaurantMenu, RestaurantRead

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants & Menu"])


@router.get("/", response_model=list[RestaurantRead], summary="Browse restaurants")
async def restaurants(db: DbSession, search: str | None = Query(default=None, max_length=100), category: str | None = Query(default=None, max_length=80)):
    return await list_restaurants(db, search, category)


@router.get("/{restaurant_id}", response_model=RestaurantMenu, summary="Get a restaurant and its menu")
async def restaurant_menu(restaurant_id: int, db: DbSession):
    restaurant = await get_restaurant_menu(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant
