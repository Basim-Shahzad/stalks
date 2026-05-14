import enum
from datetime import datetime
from decimal import Decimal
import uuid
from .base import Base
from models.enums import ExchangeType

class PortfolioSchema(Base):

    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioListItemSchema(Base):

    id: uuid.UUID
    exchange: ExchangeType
    currency: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioCreateSchema(Base):

    exchange: ExchangeType = ExchangeType.NYSE
    currency: str = "USD"
    name: str
    description: str

    class Config:
        from_attributes = True


class PortfolioUpdateSchema(PortfolioCreateSchema):
    pass
