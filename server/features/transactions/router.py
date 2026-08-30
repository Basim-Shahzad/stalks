import os
import tempfile
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from api.deps import DBSession
from features.auth.dependencies import get_current_active_user
from features.auth.models.User import User
from features.portfolios.repository import PortfolioRepository
from features.portfolios.service import PortfolioService

from .repository import JobRepository, TransactionRepository
from .schemas.JobSchema import JobStatusResponse
from .schemas.TransactionsSchema import (
    TransactionCreateSchema,
    TransactionSchema,
    TransactionsListItemSchema,
)
from .service import JobService, TransactionService, run_pdf_processing_job

router = APIRouter(prefix="/transactions", tags=["Transactions"])
jobs_router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_transaction_service(db: DBSession) -> TransactionService:
    return TransactionService(TransactionRepository(db))


def get_job_service(db: DBSession) -> JobService:
    return JobService(JobRepository(db))


@router.get(
    "/",
    response_model=list[TransactionsListItemSchema],
    status_code=status.HTTP_200_OK,
)
async def get_transactions_list(
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    portfolios: list[uuid.UUID] = Query(default=[]),
    sides: list[str] = Query(default=[]),
):
    return await get_transaction_service(db).list_for_user(
        current_user.id, portfolios, sides
    )


@router.post(
    "/{portfolio_id}",
    response_model=TransactionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction_endpoint(
    portfolio_id: uuid.UUID,
    transaction_in: TransactionCreateSchema,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    portfolio = await PortfolioService(PortfolioRepository(db)).get_owned_or_404(
        portfolio_id, current_user.id
    )
    return await get_transaction_service(db).create_for_portfolio(
        portfolio, transaction_in
    )


@router.post(
    "/{portfolio_id}/upload/pdf",
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_transaction_with_mmk_pdf(
    portfolio_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
):
    await PortfolioService(PortfolioRepository(db)).get_owned_or_404(
        portfolio_id, current_user.id
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

    job = await get_job_service(db).start_pdf_processing(portfolio_id, temp_file_path)

    background_tasks.add_task(
        run_pdf_processing_job,
        portfolio_id=portfolio_id,
        file_path=temp_file_path,
        job_id=job.id,
    )

    return {
        "message": "File uploaded successfully. Processing...",
        "job_id": job.id,
    }


@jobs_router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_job_status(job_id: uuid.UUID, db: DBSession):
    return await get_job_service(db).get_or_404(job_id)
