import uuid
from datetime import datetime, timezone
from uuid import UUID

from features.base.service import BaseService
from models.Job import Job, JobStatus
from repositories.job import JobRepository


class JobService(BaseService[Job]):
    def __init__(self, repository: JobRepository):
        super().__init__(repository, entity_name="Job")
        self.repository: JobRepository = repository

    async def start_pdf_processing(
        self, portfolio_id: UUID, file_path: str, job_type: str
    ) -> Job:
        try:
            job = await self.repository.create(
                {
                    "id": uuid.uuid4(),
                    "status": JobStatus.PENDING,
                    "job_type": job_type,
                    "payload": {
                        "file_path": file_path,
                        "portfolio_id": str(portfolio_id),
                    },
                    "started_at": datetime.now(timezone.utc),
                    "completed_at": None,
                }
            )
            return job
        except Exception as e:
            raise Exception(f"Failed to create job: {str(e)}")