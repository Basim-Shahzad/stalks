from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.UserSchema import UserCreateSchema, UserResponseSchema
from schemas.TokenSchema import TokenResponse, LoginSchema, RefreshTokenRequest
from crud.crud_auth import (
    get_user_by_email,
    create_user,
    create_refresh_token_record,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
)
from core.security import create_access_token, create_refresh_token
from services.auth_service import authenticate_user
from dependencies.auth_deps import get_current_active_user
from models.User import User

router = APIRouter()


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    """Internal helper — create access + refresh tokens and persist the refresh token."""
    access_token = create_access_token(data={"sub": user.email})
    raw_refresh, expires_at = create_refresh_token()
    create_refresh_token_record(
        db, user_id=user.id, token=raw_refresh, expires_at=expires_at
    )
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post(
    "/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
def register(user_in: UserCreateSchema, db: Session = Depends(get_db)):
    """Create a new account. Returns the user — client must call /login to get tokens."""
    if get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return create_user(db, user_in)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    """
    JSON login — accepts { email, password }.
    Returns access_token (short-lived JWT) + refresh_token (long-lived opaque token).
    """
    user = authenticate_user(db, email=credentials.email, password=credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )
    return _issue_tokens(db, user)


@router.post("/token", response_model=TokenResponse)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 form-based token endpoint (used by Swagger UI /docs).
    Accepts form fields: username (email) + password.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token + rotated refresh token.
    The old refresh token is revoked immediately (rotation prevents reuse attacks).
    """
    db_token = get_refresh_token(db, body.refresh_token)

    if not db_token or db_token.revoked or db_token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Revoke the used token before issuing new ones (token rotation)
    revoke_refresh_token(db, db_token)

    user: User = db_token.user  # loaded via relationship on RefreshToken if configured,
    # or fetch manually:
    from crud.crud_auth import get_user_by_id

    user = get_user_by_id(db, db_token.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke the provided refresh token.
    Access token expiry is handled client-side (drop it from storage).
    """
    db_token = get_refresh_token(db, body.refresh_token)
    if db_token and db_token.user_id == current_user.id:
        revoke_refresh_token(db, db_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke all refresh tokens for the current user (logout from all devices)."""
    revoke_all_user_refresh_tokens(db, current_user.id)


@router.get("/me", response_model=UserResponseSchema)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Returns the currently authenticated user's profile."""
    return current_user
