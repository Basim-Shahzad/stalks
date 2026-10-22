from fastapi import Response
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

from features.base.exceptions import (
    ConflictException,
    UnauthorizedException,
)
from features.base.service import BaseService

from .schemas.TokenSchema import (
    AccessTokenResponse,
    CreateRefreshToken,
    LoginSchema,
)
from .schemas.UserSchema import UserCreateSchema, UserUpdateSchema
from .models.User import User
from .models.RefreshToken import RefreshToken
from .repository import UserRepository, TokenRepository

REFRESH_TOKEN_COOKIE = "refresh_token"

# A valid hash of a throwaway password, used when the email does not exist so
# the login request still runs a hash comparison (avoids user enumeration
# via timing).
_DUMMY_PASSWORD_HASH = hash_password("dummy-timing-password")


def _cookie_path() -> str:
    # Only sent to the auth endpoints (refresh / logout), not every API call.
    return "/api/v1/auth"


class AuthService(BaseService[User]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository, entity_name="User")
        self.repository: UserRepository = repository

    async def register(self, obj_in: UserCreateSchema) -> User:
        email = obj_in.email.lower()
        if await self.repository.get_by_email(email) is not None:
            raise ConflictException(f"User with email {email} already exists")

        data = obj_in.model_dump(exclude={"password", "is_active"})
        data["email"] = email
        data["password_hash"] = hash_password(obj_in.password)
        try:
            return await self.repository.create(data)
        except IntegrityError:
            # Lost a race with a concurrent registration for the same email.
            raise ConflictException(f"User with email {email} already exists")

    async def login(self, obj_in: LoginSchema) -> User:
        existing = await self.repository.get_by_email(obj_in.email)

        if existing is None:
            verify_password(obj_in.password, _DUMMY_PASSWORD_HASH)
            raise UnauthorizedException("Incorrect email or password")

        if not verify_password(obj_in.password, existing.password_hash):
            raise UnauthorizedException("Incorrect email or password")

        if not existing.is_active:
            raise UnauthorizedException("Account is deactivated")

        return existing

    async def update_me(self, user: User, obj_in: UserUpdateSchema) -> User:
        data = obj_in.model_dump(exclude_unset=True)

        if "password" in data:
            data["password_hash"] = hash_password(data.pop("password"))

        if not data:
            return user

        return await self.repository.update(user, data)


class TokenService(BaseService[RefreshToken]):
    def __init__(self, repository: TokenRepository):
        super().__init__(repository, entity_name="RefreshToken")
        self.repository: TokenRepository = repository

    async def _issue(self, response: Response, user: User) -> AccessTokenResponse:
        """
        Issues both tokens. Access token is returned in JSON.
        Refresh token is set as an httpOnly cookie — JS cannot read it.
        """
        access_token = create_access_token(data={"sub": user.email})
        raw_refresh, expires_at = create_refresh_token()

        await self.repository.create_refresh_token_record(
            CreateRefreshToken(
                user_id=user.id,
                token=hash_refresh_token(raw_refresh),
                expires_at=expires_at,
            )
        )

        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE,
            value=raw_refresh,
            httponly=True,
            secure=settings.app_env != "development",
            samesite="lax",
            max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
            path=_cookie_path(),
        )
        return AccessTokenResponse(access_token=access_token)

    async def set_tokens(self, response: Response, user: User) -> AccessTokenResponse:
        """Issue a fresh token pair (login / token endpoints)."""
        return await self._issue(response, user)

    async def rotate(
        self, response: Response, raw_refresh: str | None
    ) -> AccessTokenResponse:
        """
        Validates the refresh token, revokes it (rotation) and issues a new pair.
        Presenting an already-used token is treated as theft: every session of
        that user is revoked.
        """
        if not raw_refresh:
            raise UnauthorizedException("No refresh token")

        db_token = await self.repository.get_by_token(hash_refresh_token(raw_refresh))
        if db_token is None:
            raise UnauthorizedException("Invalid or expired refresh token")
        if db_token.revoked:
            await self.repository.revoke_all_active_for_user(db_token.user_id)
            # get_db() rolls back on exceptions, so persist the revocation first.
            await self.repository.db.commit()
            raise UnauthorizedException("Invalid or expired refresh token")
        if db_token.is_expired():
            raise UnauthorizedException("Invalid or expired refresh token")

        user = await UserRepository(self.repository.db).get(db_token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        await self.repository.revoke(db_token)
        return await self._issue(response, user)

    async def logout(self, response: Response, raw_refresh: str | None) -> None:
        """Revoke the presented refresh token and clear the cookie."""
        if raw_refresh:
            db_token = await self.repository.get_by_token(
                hash_refresh_token(raw_refresh)
            )
            if db_token is not None:
                await self.repository.revoke(db_token)
        response.delete_cookie(REFRESH_TOKEN_COOKIE, path=_cookie_path())

    async def logout_all(self, response: Response, user: User) -> None:
        """Revoke every session for the user and clear the cookie."""
        await self.repository.revoke_all_active_for_user(user.id)
        response.delete_cookie(REFRESH_TOKEN_COOKIE, path=_cookie_path())
