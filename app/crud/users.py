from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def create_user(db: AsyncSession, *, email: str, password: str, full_name: str, phone_number: str | None) -> User:
    user = User(email=email.lower(), hashed_password=hash_password(password), full_name=full_name, phone_number=phone_number)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
