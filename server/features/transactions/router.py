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
from repositories.job import JobRepository
from services.job import JobService

from .repository import TransactionRepository
from .schemas.JobSchema import JobStatusResponse
from .schemas.TransactionsSchema import (
    TransactionCreateSchema,
    TransactionSchema,
    TransactionsListItemSchema,
)
from .service import TransactionService, run_pdf_processing_job

router = APIRouter(prefix="/transactions", tags=["Transactions"])
jobs_router = APIRouter(prefix="/jobs", tags=["Jobs"])

MAX_PDF_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB
_UPLOAD_CHUNK_BYTES = 1024 * 1024  # 1 MB
_PDF_MAGIC = b"%PDF-"


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
async def upload_broker_statement_pdf(
    portfolio_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
):
    """Upload a brokerage-statement PDF for background parsing. The broker
    (and therefore which parser runs) is resolved from the portfolio's
    `broker` field — the caller never chooses a parser directly."""
    portfolio = await PortfolioService(PortfolioRepository(db)).get_owned_or_404(
        portfolio_id, current_user.id
    )

    # Fail fast (before touching disk) for portfolios whose broker has no
    # supported parser.
    job_type = get_transaction_service(db).get_pdf_job_type(portfolio)

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .pdf files are accepted.",
        )
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Generated filename — never trust the client-supplied filename for the
    # on-disk path (path traversal / arbitrary filename injection).
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.pdf")

    size = 0
    try:
        with open(temp_file_path, "wb") as temp_file:
            while chunk := await file.read(_UPLOAD_CHUNK_BYTES):
                size += len(chunk)
                if size > MAX_PDF_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File too large (max 2 MB).",
                    )
                temp_file.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file"
            )

        with open(temp_file_path, "rb") as temp_file:
            if temp_file.read(len(_PDF_MAGIC)) != _PDF_MAGIC:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File is not a valid PDF.",
                )
    except HTTPException:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

    try:
        job = await get_job_service(db).start_pdf_processing(
            portfolio_id, temp_file_path, job_type
        )
        await db.commit()
    except Exception:
        # No background task will ever own this file, so don't leak it.
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

    background_tasks.add_task(
        run_pdf_processing_job,
        portfolio_id=portfolio_id,
        file_path=temp_file_path,
        job_id=job.id,
        broker=portfolio.broker,
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
async def get_job_status(
    job_id: uuid.UUID,
    db: DBSession,
    current_user: User = Depends(get_current_active_user),
):
    job = await get_job_service(db).get_or_404(job_id)

    # Jobs have no direct owner column — the owning portfolio_id lives in
    # the job payload, so authorize by resolving it back to a portfolio
    # the current user owns. Without this, any authenticated user could
    # poll any job by guessing/enumerating UUIDs.
    try:
        portfolio_id = uuid.UUID(str((job.payload or {}).get("portfolio_id")))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    await PortfolioService(PortfolioRepository(db)).get_owned_or_404(
        portfolio_id, current_user.id
    )

    return job
