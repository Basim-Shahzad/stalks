import uuid
from typing import Optional

from features.base.schema import BaseSchema
from features.transactions.models.Job import JobStatus


class JobStatusResponse(BaseSchema):
    id: uuid.UUID
    status: JobStatus
    error_message: Optional[str] = None
