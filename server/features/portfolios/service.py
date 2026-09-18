from uuid import UUID

from features.base.exceptions import NotFoundException
from features.base.service import BaseService
from features.transactions.schemas.TransactionsSchema import TransactionSchema

from .models.Portfolio import Portfolio
from .repository import PortfolioRepository
from .schemas.PortfolioSchema import PortfolioCreateSchema


class PortfolioService(BaseService[Portfolio]):
    def __init__(self, repository: PortfolioRepository):
        super().__init__(repository, entity_name="Portfolio")
        self.repository: PortfolioRepository = repository

    async def list_for_user(self, user_id: UUID) -> list[Portfolio]:
        return await self.repository.list_for_user(user_id)

    async def create_for_user(
        self, obj_in: PortfolioCreateSchema, user_id: UUID
    ) -> Portfolio:
        data = obj_in.model_dump()
        data["user_id"] = user_id
        return await self.repository.create(data)

    async def get_owned_or_404(self, portfolio_id: UUID, user_id: UUID) -> Portfolio:
        """Fetch a portfolio, 404-ing if missing OR not owned by this user
        (an ownership mismatch is reported identically to a missing row, so
        the endpoint never confirms another user's portfolio exists)."""
        portfolio = await self.get_or_404(portfolio_id)
        if portfolio.user_id != user_id:
            raise NotFoundException(f"Portfolio with id {portfolio_id} not found")
        return portfolio
    