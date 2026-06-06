import json
import uuid
import os
import tempfile
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
    requests,
    File,
    UploadFile,
)
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
from models.enums import ExchangeType
from models.Portfolio import Portfolio
from models.WatchedSymbol import WatchedSymbol
from dependencies.auth_deps import get_current_active_user
from dependencies.transactions.jobs import process_mmk_pdf_background

router = APIRouter()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
cache_file_path = os.path.join(SERVER_ROOT, "core", "data", "cache", "sector_cache.json")


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

    if portfolio.exchange == ExchangeType.PSX:
        with open(cache_file_path, "r", encoding="utf-8") as f:
            companies_sectors = json.load(f)

        if transaction_in.symbol not in companies_sectors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid symbol or Not Supported"
            )

        transaction_in.sector = companies_sectors[transaction_in.symbol]
        transaction_in.company = (
            ""  # TODO: add company name to the cache and set it here
        )
        transaction_in.total_amount = transaction_in.quantity * transaction_in.rate

        return create_transaction(db, portfolio, transaction_in)

    return create_transaction(db, portfolio, transaction_in)


@router.post(
    "/{portfolio_id}/upload/pdf",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_transaction_with_mmk_pdf(
    portfolio_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
):
    portfolio = (
        db.query(Portfolio).filter_by(id=portfolio_id, user_id=current_user.id).first()
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    if file.size > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File too large"
        )

    if not file.file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file"
        )

    temp_file_path = os.path.join(
        tempfile.gettempdir(), f"{uuid.uuid4()}_{file.filename}"
    )

    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.file.read())

    # Schedule the initial job registration and execution
    job_id = process_mmk_pdf_background(
        background_tasks=background_tasks,
        portfolio_id=portfolio_id,
        file_path=temp_file_path,
        db=db,
    )

    return {
        "message": "File uploaded successfully. Processing...",
        "job_id": job_id,
    }
