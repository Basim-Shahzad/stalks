import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from features.base.schema import BaseSchema


class TransactionSchema(BaseSchema):
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


class TransactionsListItemSchema(BaseSchema):
    id: uuid.UUID
    transaction_date: date
    company: Optional[str] = None
    symbol: str
    sector: Optional[str] = None
    side: str
    quantity: Decimal
    rate: Decimal
    commission: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    charges: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class TransactionCreateSchema(BaseSchema):
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
