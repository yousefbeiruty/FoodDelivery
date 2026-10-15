from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.crud.users import get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise credentials_error
    except (jwt.PyJWTError, ValueError):
        raise credentials_error
    user = await get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
