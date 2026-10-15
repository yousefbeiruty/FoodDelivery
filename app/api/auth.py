from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession
from app.core.security import create_access_token, verify_password
from app.crud.users import create_user, get_user_by_email
from app.schemas.api import Token, UserCreate, UserRead

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create an account")
async def register(payload: UserCreate, db: DbSession):
    if await get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return await create_user(db, email=payload.email, password=payload.password, full_name=payload.full_name, phone_number=payload.phone_number)


@router.post("/token", response_model=Token, summary="Sign in and receive a bearer token")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = await get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password) or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.email))
