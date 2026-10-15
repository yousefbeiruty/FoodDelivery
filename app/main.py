from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, orders, restaurants, users
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 - register ORM tables before create_all


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="FreshBite food delivery API for restaurant discovery, ordering, and live delivery tracking. "
                "Register and sign in to access your profile and orders. Order updates are available over WebSockets.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "Register and sign in with email and password."},
        {"name": "Users", "description": "Manage your FreshBite profile."},
        {"name": "Restaurants & Menu", "description": "Discover restaurants and browse their menus."},
        {"name": "Orders & Tracking", "description": "Price, place, and track food orders."},
    ],
    lifespan=lifespan,
)

static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(restaurants.router)
app.include_router(orders.router)


@app.get("/", tags=["Health"], summary="API health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "FreshBite"}
