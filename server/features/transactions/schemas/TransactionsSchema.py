import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field

from features.transactions.models.Side import Side
from features.base.schema import BaseSchema


class TransactionSchema(BaseSchema):
    id: uuid.UUID
    transaction_date: date
    company: str
    symbol: str
    sector: Optional[str] = None
    side: Side
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
    side: Side
    quantity: Decimal
    rate: Decimal
    commission: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    charges: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class TransactionCreateSchema(BaseSchema):
    transaction_date: date
    company: Optional[str] = None
    symbol: str = Field(..., min_length=1, max_length=20)
    sector: Optional[str] = None
    side: Side
    quantity: Decimal = Field(..., gt=0)
    rate: Decimal = Field(..., ge=0)
    commission: Decimal = Field(default=Decimal("0.00"), ge=0)
    taxes: Decimal = Field(default=Decimal("0.00"), ge=0)
    charges: Decimal = Field(default=Decimal("0.00"), ge=0)
    # 0 / omitted means "compute it": gross +/- fees for BUY/SELL.
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class TransactionUpdateSchema(TransactionCreateSchema):
    pass
