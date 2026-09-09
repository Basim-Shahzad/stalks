from sqlalchemy.ext.asyncio import AsyncSession

from features.base.repository import BaseRepository

from models.Job import Job


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: AsyncSession):
        super().__init__(Job, db)
