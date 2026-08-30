import json
import os
import uuid
from datetime import datetime, timezone
from uuid import UUID

from core.logger import logger
from db.database import AsyncSessionLocal
from features.base.exceptions import ValidationException
from features.base.service import BaseService
from features.portfolios.models.Portfolio import Portfolio
from models.enums import ExchangeType

from .models.Job import Job, JobStatus
from .models.Transaction import Transaction
from .repository import JobRepository, TransactionRepository
from .schemas.TransactionsSchema import TransactionCreateSchema
from .statement_parser import SECTOR_CACHE_FILE, process_statement


class TransactionService(BaseService[Transaction]):
    def __init__(self, repository: TransactionRepository):
        super().__init__(repository, entity_name="Transaction")
        self.repository: TransactionRepository = repository

    async def list_for_user(
        self,
        user_id: UUID,
        portfolio_ids: list[UUID] | None = None,
        sides: list[str] | None = None,
    ) -> list[Transaction]:
        return await self.repository.list_for_user(user_id, portfolio_ids, sides)

    async def create_for_portfolio(
        self, portfolio: Portfolio, obj_in: TransactionCreateSchema
    ) -> Transaction:
        if portfolio.exchange == ExchangeType.PSX:
            companies_sectors = json.loads(
                SECTOR_CACHE_FILE.read_text(encoding="utf-8")
            )

            if obj_in.symbol not in companies_sectors:
                raise ValidationException("Invalid symbol or Not Supported")

            obj_in.sector = companies_sectors[obj_in.symbol]
            obj_in.company = ""  # TODO: add company name to the cache and set it here
            obj_in.total_amount = obj_in.quantity * obj_in.rate

        data = obj_in.model_dump()
        data["portfolio_id"] = portfolio.id
        transaction = await self.repository.create(data)

        await self.repository.ensure_symbol_watched(obj_in.symbol, portfolio.exchange)

        return transaction


class JobService(BaseService[Job]):
    def __init__(self, repository: JobRepository):
        super().__init__(repository, entity_name="Job")
        self.repository: JobRepository = repository

    async def start_pdf_processing(self, portfolio_id: UUID, file_path: str) -> Job:
        return await self.repository.create(
            {
                "id": uuid.uuid4(),
                "status": JobStatus.PENDING,
                "job_type": "MMK_PDF_PROCESSING",
                "payload": {
                    "file_path": file_path,
                    "portfolio_id": str(portfolio_id),
                },
                "started_at": datetime.now(timezone.utc),
                "completed_at": None,
            }
        )


async def run_pdf_processing_job(
    portfolio_id: UUID, file_path: str, job_id: UUID
) -> None:
    """Background task: parse the uploaded PDF, persist the resulting
    transactions, and update the job's status. Uses its own DB session
    since it keeps running after the request/response cycle has ended."""
    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        job = await job_repo.get(job_id)
        if job is None:
            return

        try:
            job.status = JobStatus.IN_PROGRESS
            await db.commit()

            data = await process_statement(file_path)

            if data:
                tx_repo = TransactionRepository(db)
                for row in data:
                    parsed_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    await tx_repo.create(
                        {
                            "portfolio_id": portfolio_id,
                            "transaction_date": parsed_date,
                            "company": row["company"],
                            "symbol": row["symbol"],
                            "sector": row.get("sector"),
                            "side": row["side"],
                            "quantity": row["quantity"],
                            "rate": row["rate"],
                            "commission": row.get("commission", 0.00),
                            "taxes": row.get("taxes", 0.00),
                            "charges": row.get("charges", 0.00),
                            "total_amount": row["total_amount"],
                        }
                    )
                job.status = JobStatus.COMPLETED
                job.result = "Processing completed successfully"
            else:
                job.status = JobStatus.FAILED
                job.error_message = "Processing failed"
                logger.warning("Background job %s failed during processing", job_id)

            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            await db.rollback()
            job = await job_repo.get(job_id)
            if job is not None:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
