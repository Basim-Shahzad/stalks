from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from db.database import get_db
from schemas.UserSchema import UserCreateSchema, UserResponseSchema
from schemas.TokenSchema import AccessTokenResponse, LoginSchema
from crud.crud_auth import (
    get_user_by_email,
    create_user,
    create_refresh_token_record,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    get_user_by_id,
)
from core.security import create_access_token, create_refresh_token
from core.config import settings
from services.auth_service import authenticate_user
from dependencies.auth_deps import get_current_active_user
from models.User import User

router = APIRouter()

REFRESH_TOKEN_COOKIE = "refresh_token"


def _set_tokens(response: Response, db: Session, user: User) -> AccessTokenResponse:
    """
    Issues both tokens. Access token is returned in JSON.
    Refresh token is set as an httpOnly cookie — JS cannot read it.
    """
    access_token = create_access_token(data={"sub": user.email})
    raw_refresh, expires_at = create_refresh_token()
    create_refresh_token_record(db, user_id=user.id, token=raw_refresh, expires_at=expires_at)

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=raw_refresh,
        httponly=True,           # JS cannot access this
        secure=True,             # HTTPS only — set False for local dev if needed
        samesite="lax",          # protects against CSRF
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",      # cookie only sent to auth endpoints, not every request
    )
    return AccessTokenResponse(access_token=access_token)


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreateSchema, db: Session = Depends(get_db)):
    """Create a new account. Call /login after to get tokens."""
    if get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return create_user(db, user_in)


@router.post("/login", response_model=AccessTokenResponse)
def login(credentials: LoginSchema, response: Response, db: Session = Depends(get_db)):
    """
    JSON login. Returns access_token in body, sets refresh_token as httpOnly cookie.
    Frontend stores access_token in memory (JS variable), never in localStorage.
    """
    user = authenticate_user(db, email=credentials.email, password=credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return _set_tokens(response, db, user)


@router.post("/token", response_model=AccessTokenResponse)
def token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 form-based endpoint — only for Swagger UI /docs."""
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return _set_tokens(response, db, user)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    """
    Uses the httpOnly cookie automatically — frontend just calls this endpoint,
    no need to manually send anything. Returns a new access_token + rotates the cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    db_token = get_refresh_token(db, refresh_token)
    if not db_token or db_token.revoked or db_token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    revoke_refresh_token(db, db_token)
    user = get_user_by_id(db, db_token.user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return _set_tokens(response, db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    """Revokes the refresh token cookie and clears it."""
    if refresh_token:
        db_token = get_refresh_token(db, refresh_token)
        if db_token and db_token.user_id == current_user.id:
            revoke_refresh_token(db, db_token)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/v1/auth")


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke all sessions across all devices."""
    revoke_all_user_refresh_tokens(db, current_user.id)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/auth")


@router.get("/me", response_model=UserResponseSchema)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Returns the currently authenticated user's profile."""
    return current_user