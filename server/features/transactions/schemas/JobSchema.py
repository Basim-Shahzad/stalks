import uuid
from typing import Optional

from features.base.schema import BaseSchema
from models.Job import JobStatus


class JobStatusResponse(BaseSchema):
    id: uuid.UUID
    status: JobStatus
    error_message: Optional[str] = None
