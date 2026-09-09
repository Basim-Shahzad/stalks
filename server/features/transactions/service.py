import asyncio
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID

from core.logger import logger
from db.database import AsyncSessionLocal
from features.base.exceptions import ValidationException
from features.base.service import BaseService
from features.portfolios.models.Portfolio import Broker, Portfolio
from models.enums import ExchangeType
from models.Job import JobStatus
from repositories.job import JobRepository

from .models.Transaction import Transaction
from .parsers.akd import ParseResult as AkdParseResult
from .parsers.akd import parse_pdf as parse_akd_pdf
from .parsers.mmk import (
    SECTOR_CACHE_FILE,
    _enrich_with_sectors as enrich_mmk_sectors,
)
from .parsers.mmk import process_statement as process_mmk_statement
from .repository import TransactionRepository
from .schemas.TransactionsSchema import TransactionCreateSchema

# Job-type identifiers persisted on the Job row, one per supported broker.
# Keyed by the Portfolio.broker enum so the router/service can validate a
# portfolio is actually supported *before* accepting an upload.
BROKER_JOB_TYPES: dict[Broker, str] = {
    Broker.AKD: "AKD_PDF_PROCESSING",
    Broker.MMK: "MMK_PDF_PROCESSING",
}

# Maximum size (in characters) persisted to Job.error_message (String(255)).
_ERROR_MESSAGE_MAX_LEN = 255


def get_job_type_for_broker(broker: Broker | None) -> str:
    """Resolve the background-job type for a portfolio's broker, raising a
    ValidationException for brokers we don't have a statement parser for
    (e.g. Broker.OTHER, or no broker configured at all)."""
    if broker is None or broker not in BROKER_JOB_TYPES:
        raise ValidationException(
            "This portfolio's broker does not support automatic PDF "
            "statement parsing. Supported brokers: "
            f"{', '.join(b.name for b in BROKER_JOB_TYPES)}."
        )
    return BROKER_JOB_TYPES[broker]


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

        return transaction

    def get_pdf_job_type(self, portfolio: Portfolio) -> str:
        """Validate that `portfolio` supports PDF statement parsing and
        return the job_type to record on the Job row. Raises
        ValidationException (-> 422) if unsupported, so the router can
        reject an upload before ever touching disk."""
        if portfolio.exchange != ExchangeType.PSX:
            raise ValidationException(
                "PDF statement parsing is only supported for PSX portfolios."
            )
        return get_job_type_for_broker(portfolio.broker)


def _to_decimal(value) -> Decimal:
    """Coerce a parser-produced number (float, int, Decimal, or numeric
    string) into a Decimal via its string form, never via float(), to avoid
    binary floating-point rounding creeping into money columns."""
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValidationException(f"Could not parse numeric value: {value!r}") from exc


async def _parse_akd_rows(file_path: str) -> list[dict]:
    """Run the (blocking) AKD parser off the event loop, normalize its
    dataclass output into the same row shape the MMK parser produces, and
    fill in any sectors the parser's local cache didn't know about via the
    live PSX lookup used by the MMK pipeline."""
    result: AkdParseResult = await asyncio.to_thread(parse_akd_pdf, file_path)

    if result.errors:
        messages = "; ".join(e.message for e in result.errors)
        raise ValidationException(f"Failed to parse AKD statement: {messages}")

    if not result.transactions:
        raise ValidationException("No transactions were found in the AKD statement.")

    rows: list[dict] = []
    for tx in result.transactions:
        if not tx.transactionDate:
            raise ValidationException(
                f"AKD statement row for {tx.symbol!r} is missing a transaction date."
            )
        rows.append(
            {
                "date": tx.transactionDate,
                "company": tx.company or tx.symbol,
                "symbol": tx.symbol,
                "side": tx.side,
                "quantity": tx.quantity,
                "rate": tx.rate,
                "commission": tx.commission,
                "taxes": tx.taxes,
                "charges": tx.charges,
                "total_amount": tx.totalAmount,
                "sector": tx.sector,
            }
        )

    missing_sector_rows = [row for row in rows if not row.get("sector")]
    if missing_sector_rows:
        # Mutates the dicts in place (they're the same objects held in `rows`),
        # deduplicating by symbol and firing lookups concurrently — mirrors
        # the enrichment step the MMK pipeline runs internally.
        await enrich_mmk_sectors(missing_sector_rows)

    return rows

async def run_pdf_processing_job(
    portfolio_id: UUID, file_path: str, job_id: UUID, broker: Broker
) -> None:
    """Background task: parse the uploaded broker statement PDF (dispatching
    on `broker`), persist the resulting transactions, and update the job's
    status. Uses its own DB session since it keeps running after the
    request/response cycle has ended."""
    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        print(f"Running PDF processing job {job_id} for portfolio {portfolio_id} and broker {broker}")

        job = await job_repo.get(job_id)

        print(f"Job retrieved: {job}")
        if job is None:
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        try:
            job.status = JobStatus.IN_PROGRESS
            await db.commit()

            if broker == Broker.MMK:
                rows = await process_mmk_statement(file_path)
            elif broker == Broker.AKD:
                rows = await _parse_akd_rows(file_path)
            else:
                raise ValidationException(f"Unsupported broker for PDF parsing: {broker}")

            tx_repo = TransactionRepository(db)
            for row in rows:
                parsed_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                await tx_repo.create(
                    {
                        "portfolio_id": portfolio_id,
                        "transaction_date": parsed_date,
                        "company": row["company"],
                        "symbol": row["symbol"],
                        "sector": row.get("sector"),
                        "side": row["side"],
                        "quantity": _to_decimal(row["quantity"]),
                        "rate": _to_decimal(row["rate"]),
                        "commission": _to_decimal(row.get("commission", 0)),
                        "taxes": _to_decimal(row.get("taxes", 0)),
                        "charges": _to_decimal(row.get("charges", 0)),
                        "total_amount": _to_decimal(row["total_amount"]),
                    }
                )

            job.status = JobStatus.COMPLETED
            job.result = f"Processed {len(rows)} transaction(s) successfully"
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            await db.rollback()
            job = await job_repo.get(job_id)
            if job is not None:
                job.status = JobStatus.FAILED
                job.error_message = str(e)[:_ERROR_MESSAGE_MAX_LEN]
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
            logger.exception("PDF processing job %s failed", job_id)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
