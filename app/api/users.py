from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.api import UserRead, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserRead, summary="Get the signed-in profile")
async def profile(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead, summary="Update the signed-in profile")
async def update_profile(payload: UserUpdate, user: CurrentUser, db: DbSession):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
