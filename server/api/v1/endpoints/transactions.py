import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.TransactionsSchema import (
    TransactionsListItemSchema,
    TransactionCreateSchema,
    TransactionUpdateSchema,
    TransactionSchema,
)
from crud.crud_transactions import get_transactions, create_transaction
from models.User import User
from models.Portfolio import Portfolio
from models.WatchedSymbol import WatchedSymbol
from dependencies.auth_deps import get_current_active_user

router = APIRouter()


@router.get(
    "/",
    response_model=list[TransactionsListItemSchema],
    status_code=status.HTTP_200_OK,
)
def get_transactions_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    portfolios: list[uuid.UUID] = Query(default=[]),
    sides: list[str] = Query(default=[]),
):
    transactions = get_transactions(db, current_user.id, portfolios, sides)
    return transactions


@router.post(
    "/{portfolio_id}",
    response_model=TransactionSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction_endpoint(
    portfolio_id: uuid.UUID,
    transaction_in: TransactionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    portfolio = (
        db.query(Portfolio).filter_by(id=portfolio_id, user_id=current_user.id).first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return create_transaction(db, portfolio, transaction_in)
