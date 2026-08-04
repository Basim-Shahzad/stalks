from fastapi import APIRouter, Depends, Cookie, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from api.deps import DBSession
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from features.auth.repository import TokenRepository, UserRepository
from features.auth.schemas.TokenSchema import AccessTokenResponse, LoginSchema
from features.auth.schemas.UserSchema import (
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
    UserUpdateResponseSchema,
)
from features.auth.service import AuthService, TokenService

router = APIRouter(prefix="/auth", tags=["authentication"])

REFRESH_TOKEN_COOKIE = "refresh_token"


def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(UserRepository(db))


def get_token_service(db: DBSession) -> TokenService:
    return TokenService(TokenRepository(db))


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreateSchema, db: DBSession):
    """Create a new account. Call /login after to get tokens."""
    return await get_auth_service(db).register(payload)


@router.post("/login", response_model=AccessTokenResponse)
async def login(credentials: LoginSchema, response: Response, db: DBSession):
    """
    JSON login. Returns access_token in body, sets refresh_token as httpOnly cookie.
    """
    user = await get_auth_service(db).login(credentials)
    return await get_token_service(db).set_tokens(response, user)


@router.post("/token", response_model=AccessTokenResponse)
async def token(
    response: Response,
    db: DBSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """OAuth2 form-based endpoint — for Swagger UI /docs."""
    credentials = LoginSchema(email=form_data.username, password=form_data.password)
    user = await get_auth_service(db).login(credentials)
    return await get_token_service(db).set_tokens(response, user)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    db: DBSession,
    refresh_token: str = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    """
    Uses the httpOnly cookie automatically. Returns a new access_token and
    rotates the refresh token (the old one is revoked).
    """
    return await get_token_service(db).rotate(response, refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    refresh_token: str = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    """Revoke the current session's refresh token and clear the cookie."""
    await get_token_service(db).logout(response, refresh_token, current_user)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    """Revoke all sessions across all devices and clear the cookie."""
    await get_token_service(db).logout_all(response, current_user)


@router.get("/me", response_model=UserResponseSchema)
async def read_me(current_user: User = Depends(get_current_active_user)):
    """Returns the currently authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserUpdateResponseSchema)
async def update_me(
    payload: UserUpdateSchema,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    """Update the current user's profile (name / password)."""
    return await get_auth_service(db).update_me(current_user, payload)
