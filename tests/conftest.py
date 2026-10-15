from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import app
from app.models import MenuItem, Restaurant


@pytest_asyncio.fixture
async def client() -> AsyncIterator[tuple[AsyncClient, dict[str, int]]]:
    # One isolated in-memory database per test; the production database is untouched.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    ids: dict[str, int] = {}
    async with session_factory() as session:
        restaurant = Restaurant(
            name="FreshBite Test Kitchen",
            rating=4.8,
            delivery_time="20-30 min",
            image_url="/static/menu/burgers.svg",
            category_tags=["burgers", "popular"],
        )
        session.add(restaurant)
        await session.flush()
        menu_item = MenuItem(
            restaurant_id=restaurant.id,
            name="Garden Burger",
            description="A test burger with fresh greens.",
            price=6.0,
            calories=480,
            image_url="/static/menu/burgers.svg",
            category="burgers",
        )
        session.add(menu_item)
        await session.flush()
        ids.update(restaurant_id=restaurant.id, menu_item_id=menu_item.id)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client, ids
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()
