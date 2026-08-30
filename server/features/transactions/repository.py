from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository
from features.portfolios.models.Portfolio import Portfolio
from models.enums import ExchangeType

from .models.Job import Job
from .models.Transaction import Transaction
from .models.WatchedSymbol import WatchedSymbol


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    async def list_for_user(
        self,
        user_id: UUID,
        portfolio_ids: list[UUID] | None = None,
        sides: list[str] | None = None,
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

    async def ensure_symbol_watched(self, symbol: str, exchange: ExchangeType) -> None:
        """Add (symbol, exchange) to watched_symbols if not already tracked.
        Flushes, does not commit."""
        result = await self.db.execute(
            select(WatchedSymbol).where(
                WatchedSymbol.symbol == symbol,
                WatchedSymbol.exchange == exchange,
            )
        )
        if result.scalar_one_or_none() is None:
            self.db.add(WatchedSymbol(symbol=symbol, exchange=exchange))
            await self.db.flush()


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: AsyncSession):
        super().__init__(Job, db)
