from datetime import datetime, date
from pydantic import Field
from decimal import Decimal
import uuid
from typing import Optional
from .base import Base


class TransactionSchema(Base):
    id: uuid.UUID
    transaction_date: date
    company: str
    symbol: str
    sector: str
    side: str
    quantity: Decimal
    rate: Decimal
    commission: Decimal = Decimal("0.00")
    taxes: Decimal = Decimal("0.00")
    charges: Decimal = Decimal("0.00")
    total_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionsListItemSchema(Base):

    id: uuid.UUID
    transaction_date: date
    company: Optional[str] = None
    sector: Optional[str] = None
    symbol: str
    sector: str
    side: str
    quantity: Decimal
    rate: Decimal
    commission: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    charges: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class TransactionCreateSchema(Base):

    transaction_date: date
    company: Optional[str] = None
    symbol: str
    sector: Optional[str] = None
    side: str
    quantity: Decimal
    rate: Decimal
    commission: Decimal = Decimal("0.00")
    taxes: Decimal = Decimal("0.00")
    charges: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")


class TransactionUpdateSchema(TransactionCreateSchema):
    pass
