from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository
from .schemas.TokenSchema import CreateRefreshToken
from .models.User import User
from .models.RefreshToken import RefreshToken


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a single user by their (unique) email address."""
        result = await self.db.execute(
            select(User).where(User.email == email)
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
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Look up a refresh token record by its raw token value."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke(self, db_token: RefreshToken) -> RefreshToken:
        """Mark a single refresh token as revoked."""
        db_token.revoked = True
        await self.db.flush()
        return db_token

    async def revoke_all_active_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user (logout-all-devices)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
        )
        for token in result.scalars().all():
            token.revoked = True
        await self.db.flush()