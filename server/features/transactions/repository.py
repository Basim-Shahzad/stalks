from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository
from features.portfolios.models.Portfolio import Portfolio

from .models.Side import Side
from .models.Transaction import Transaction


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    async def list_for_user(
        self,
        user_id: UUID,
        portfolio_ids: list[UUID] | None = None,
        sides: list[Side] | None = None,
    ) -> list[Transaction]:
        query = (
            select(Transaction)
            .join(Portfolio, Transaction.portfolio_id == Portfolio.id)
            .where(Portfolio.user_id == user_id)
        )

        if portfolio_ids:
            query = query.where(Transaction.portfolio_id.in_(portfolio_ids))
        if sides:
            query = query.where(Transaction.side.in_(sides))

        query = query.order_by(Transaction.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_portfolio(self, portfolio_id: UUID) -> list[Transaction]:
        """All transactions of one portfolio. The caller must already have
        verified ownership (e.g. PortfolioService.get_owned_or_404), so no
        join to portfolios is needed. Oldest first."""
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date, Transaction.created_at)
        )
        return list(result.scalars().all())

