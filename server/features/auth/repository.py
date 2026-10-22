from uuid import UUID
from datetime import datetime

from datetime import UTC, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository
from .schemas.TokenSchema import CreateRefreshToken
from .models.User import User
from .models.RefreshToken import RefreshToken


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a single user by their (unique) email address, case-insensitively.

        Emails are stored lower-cased, so the indexed equality lookup is tried
        first; the non-indexed lower() scan only runs for legacy mixed-case
        rows (or when the email doesn't exist)."""
        email = email.lower()
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is not None:
            return user
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == email)
        )
        return result.scalar_one_or_none()


class TokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def create_refresh_token_record(
        self, obj_in: CreateRefreshToken
    ) -> RefreshToken:
        """Persist a new refresh token record for a user. Flushes, does not commit."""
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Look up a refresh token record by its stored (hashed) token value."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke(self, db_token: RefreshToken) -> RefreshToken:
        """Mark a single refresh token as revoked."""
        db_token.revoked = True
        await self.db.flush()
        return db_token

    async def claim(self, token_id: UUID) -> bool:
        """Atomically revoke a still-active token. Returns False if another
        request revoked it first (so only one concurrent refresh can win)."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id, RefreshToken.revoked.is_(False))
            .values(revoked=True, updated_at=datetime.now(UTC))
        )
        return result.rowcount == 1

    async def revoke_all_active_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user (logout-all-devices)."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True, updated_at=datetime.now(UTC))
        )

    async def purge_stale(self, keep_revoked_for: timedelta = timedelta(days=1)) -> int:
        """Delete expired tokens, and revoked tokens older than `keep_revoked_for`
        (kept briefly so reuse of a rotated token is still detected)."""
        now = datetime.now(UTC)
        result = await self.db.execute(
            delete(RefreshToken).where(
                (RefreshToken.expires_at < now)
                | (
                    RefreshToken.revoked.is_(True)
                    & (RefreshToken.updated_at < now - keep_revoked_for)
                )
            )
        )
        return result.rowcount or 0