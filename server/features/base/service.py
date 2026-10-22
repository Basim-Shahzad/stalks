"""
Generic base service. Thinner than BaseRepository on purpose — business
logic is inherently more bespoke, so this only captures the handful of
patterns that genuinely repeat across every domain: fetch-or-404,
existence checks, and delegating CRUD to the repository.

Domain services (ClientService, InvoiceService, etc.) inherit this,
inject their own repository, and add real business rules on top —
validation, cross-domain calls, side effects like sending emails or
invalidating cache.
"""

from typing import Any, Generic, TypeVar

from features.base.exceptions import NotFoundException
from features.base.repository import BaseRepository, ModelType

RepoType = TypeVar("RepoType", bound=BaseRepository)


class BaseService(Generic[ModelType]):
    def __init__(
        self, repository: BaseRepository[ModelType], entity_name: str = "Resource"
    ):
        self.repository = repository
        self.entity_name = entity_name

    async def get_or_404(self, id: Any) -> ModelType:
        """Fetch by id, raising NotFoundException if missing. Use this instead
        of repository.get() directly whenever a missing row should 404."""
        obj = await self.repository.get(id)
        if obj is None:
            raise NotFoundException(f"{self.entity_name} with id {id} not found")
        return obj

    async def list(
        self, skip: int = 0, limit: int = 100, **filters: Any
    ) -> list[ModelType]:
        return await self.repository.get_multi(skip=skip, limit=limit, **filters)

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        return await self.repository.create(obj_in)

    async def update(self, id: Any, obj_in: dict[str, Any]) -> ModelType:
        db_obj = await self.get_or_404(id)
        return await self.repository.update(db_obj, obj_in)

    async def delete(self, id: Any) -> ModelType:
        db_obj = await self.get_or_404(id)
        await self.repository.remove(db_obj)
        return db_obj
