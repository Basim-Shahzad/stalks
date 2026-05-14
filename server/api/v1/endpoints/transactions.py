import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
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
from dependencies.auth_deps import get_current_active_user

router = APIRouter()


@router.get(
    "/{portfolio_id}",
    response_model=list[TransactionsListItemSchema],
    status_code=status.HTTP_200_OK,
)
def get_transactions_list(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    transactions = get_transactions(db, portfolio_id)

    # Optional: Handle the 404 case if the portfolio doesn't exist
    if transactions is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return transactions


@router.post(
    "/",
    response_model=TransactionSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction_endpoint(
    transaction_in: TransactionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_transaction(db, transaction_in)

