import enum
from datetime import datetime

from db.database import Base
from models.mixins.TimestampMixin import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum, JSON


class JobStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.PENDING
    )
    started_at: Mapped[datetime] = mapped_column(nullable=True)
    completed_at: Mapped[datetime] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=3)
    error_message: Mapped[str] = mapped_column(String(255), nullable=True)
    result: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<Job {self.job_type} - {self.status.value}>"
