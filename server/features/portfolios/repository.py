from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository

from .models.Portfolio import Portfolio


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self, db: AsyncSession):
        super().__init__(Portfolio, db)

    async def list_for_user(self, user_id: UUID) -> list[Portfolio]:
        """Fetch all portfolios for a user, newest first."""
        result = await self.db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )
        return list(result.scalars().all())
