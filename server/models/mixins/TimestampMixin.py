from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy import UUID


class TimestampMixin:
    """Inherit from this to get ID and Timestamps automatically"""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        onupdate=func.now(), server_default=func.now()
    )
