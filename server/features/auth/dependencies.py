"""
Async auth dependencies for the feature-based architecture.

Mirrors the (legacy) sync dependencies/auth_deps.py but works with
AsyncSession and the feature repository/service layer.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from api.deps import DBSession
from core.config import settings
from core.security import oauth2_scheme
from features.auth.models.User import User
from features.auth.repository import UserRepository
from features.auth.schemas.TokenSchema import TokenData

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DBSession,
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
        token_data = TokenData(
            user_id=payload["sub"],
            token_version=payload.get("token_version", 0),
        )
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    user = await UserRepository(db).get(token_data.user_id)
    if user is None or user.token_version != token_data.token_version:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user
