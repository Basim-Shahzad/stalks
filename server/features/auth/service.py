import asyncio
from datetime import UTC, datetime, timedelta

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
    AuthenticationException,
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
# Only sent to the auth endpoints (refresh / logout), not every API call.
REFRESH_COOKIE_PATH = "/api/v1/auth"

# A refresh token revoked this recently was almost certainly consumed by a
# concurrent request from the same client (two tabs, retried 401s), not stolen.
# Such a request is rejected, but does not trigger the revoke-everything
# theft response.
REFRESH_REUSE_GRACE = timedelta(seconds=10)

# A valid hash of a throwaway password, used when the email does not exist so
# the login request still runs a hash comparison (avoids user enumeration
# via timing).
_DUMMY_PASSWORD_HASH = hash_password("dummy-timing-password")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthService(BaseService[User]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository, entity_name="User")
        self.repository: UserRepository = repository

    # Argon2 is deliberately CPU-heavy; keep it off the event loop.
    @staticmethod
    async def _hash(password: str) -> str:
        return await asyncio.to_thread(hash_password, password)

    @staticmethod
    async def _verify(password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(verify_password, password, password_hash)

    async def register(self, obj_in: UserCreateSchema) -> User:
        email = obj_in.email.lower()
        if await self.repository.get_by_email(email) is not None:
            raise ConflictException(f"User with email {email} already exists")

        data = obj_in.model_dump(exclude={"password", "is_active"})
        data["email"] = email
        data["password_hash"] = await self._hash(obj_in.password)
        try:
            return await self.repository.create(data)
        except IntegrityError:
            # Lost a race with a concurrent registration for the same email.
            raise ConflictException(f"User with email {email} already exists")

    async def login(self, obj_in: LoginSchema) -> User:
        existing = await self.repository.get_by_email(obj_in.email)

        if existing is None:
            await self._verify(obj_in.password, _DUMMY_PASSWORD_HASH)
            raise AuthenticationException("Incorrect email or password")

        if not await self._verify(obj_in.password, existing.password_hash):
            raise AuthenticationException("Incorrect email or password")

        if not existing.is_active:
            raise UnauthorizedException("Account is deactivated")

        return existing

    async def update_me(self, user: User, obj_in: UserUpdateSchema) -> User:
        data = obj_in.model_dump(exclude_unset=True)
        # Explicit nulls would try to blank NOT NULL columns.
        data = {k: v for k, v in data.items() if v is not None}

        new_password = data.pop("password", None)
        current_password = data.pop("current_password", None)
        if new_password is not None:
            if not current_password or not await self._verify(
                current_password, user.password_hash
            ):
                raise AuthenticationException("Current password is incorrect")
            data["password_hash"] = await self._hash(new_password)

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
        access_token = create_access_token(data={"sub": str(user.id)})
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
            path=REFRESH_COOKIE_PATH,
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
        Presenting an already-used token long after it was rotated is treated
        as theft: every session of that user is revoked. A token consumed just
        moments ago (concurrent request) is simply rejected.
        """
        invalid = AuthenticationException("Invalid or expired refresh token")

        if not raw_refresh:
            raise AuthenticationException("No refresh token")

        db_token = await self.repository.get_by_token(hash_refresh_token(raw_refresh))
        if db_token is None:
            raise invalid
        if db_token.revoked:
            revoked_at = _as_utc(db_token.updated_at)
            if datetime.now(UTC) - revoked_at > REFRESH_REUSE_GRACE:
                await self.repository.revoke_all_active_for_user(db_token.user_id)
                # get_db() rolls back on exceptions, so persist the revocation first.
                await self.repository.db.commit()
            raise invalid
        if db_token.is_expired():
            raise invalid

        user = await UserRepository(self.repository.db).get(db_token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        # Atomic compare-and-set: exactly one concurrent request wins.
        if not await self.repository.claim(db_token.id):
            raise invalid

        return await self._issue(response, user)

    async def logout(self, response: Response, raw_refresh: str | None) -> None:
        """Revoke the presented refresh token and clear the cookie."""
        if raw_refresh:
            db_token = await self.repository.get_by_token(
                hash_refresh_token(raw_refresh)
            )
            if db_token is not None:
                await self.repository.revoke(db_token)
        response.delete_cookie(REFRESH_TOKEN_COOKIE, path=REFRESH_COOKIE_PATH)

    async def logout_all(self, response: Response, user: User) -> None:
        """Revoke every session for the user and clear the cookie."""
        await self.repository.revoke_all_active_for_user(user.id)
        response.delete_cookie(REFRESH_TOKEN_COOKIE, path=REFRESH_COOKIE_PATH)
