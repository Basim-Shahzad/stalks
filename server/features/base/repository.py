"""
Generic base repository providing standard async CRUD operations.

Every feature repository should inherit from BaseRepository 
and only add feature-specific query methods.

Design decisions baked into this file:
- All methods are async, expecting an AsyncSession.
- Repos add/flush but do NOT commit. Commit boundaries live at the service
  layer (or a request-scoped unit-of-work dependency), so a single request
  that touches multiple repos can be committed atomically.
- Generic filtering supports simple field=value equality via **filters.
  Anything more complex (joins,s OR conditions, full-text search) belongs
  in the subclass as its own named method — don't grow this into a
  query-builder.
"""

from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


def _apply_filters(query, model, filters: dict[str, Any]):
    for field, value in filters.items():
        column = getattr(model, field, None)
        if column is None:
            raise ValueError(f"{model.__name__} has no field {field!r} to filter on")
        query = query.where(column == value)
    return query


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> ModelType | None:
        """Fetch a single row by primary key. Returns None if not found."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int,
        limit: int,
        **filters: Any,
    ) -> list[ModelType]:
        """
        Fetch multiple rows with pagination and optional equality filters.

        Example: repo.get_multi(skip=0, limit=20, freelancer_id=freelancer_id)
        """
        # Stable ordering is required for offset/limit pagination to be sane.
        query = _apply_filters(select(self.model), self.model, filters)
        query = query.order_by(self.model.created_at, self.model.id)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """Count rows matching the given equality filters."""
        query = _apply_filters(select(func.count()).select_from(self.model), self.model, filters)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists(self, **filters: Any) -> bool:
        """Check whether any row matches the given equality filters."""
        return await self.count(**filters) > 0

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create a new row from a dict of field values. Flushes, does not commit."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """Update fields on an existing row. Flushes, does not commit."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def remove(self, db_obj: ModelType) -> None:
        """Delete an already-loaded row. Flushes, does not commit."""
        await self.db.delete(db_obj)
        await self.db.flush()

    async def delete(self, id: Any) -> ModelType | None:
        """Delete a row by primary key. Returns the deleted object, or None if not found."""
        db_obj = await self.get(id)
        if db_obj is None:
            return None
        await self.remove(db_obj)
        return db_obj
