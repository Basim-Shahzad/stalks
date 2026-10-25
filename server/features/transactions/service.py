import asyncio
import os
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import select

from core.logger import logger
from db.database import AsyncSessionLocal
from features.base.exceptions import ValidationException
from features.base.service import BaseService
from features.portfolios.models.Portfolio import Broker, Portfolio
from models.enums import ExchangeType
from models.Job import JobStatus
from repositories.job import JobRepository

from .models.Side import Side
from .models.Transaction import Transaction
from .parsers.akd import ParseResult as AkdParseResult
from .parsers.akd import parse_pdf as parse_akd_pdf
from .parsers.mmk import process_statement as process_mmk_statement
from .repository import TransactionRepository
from .schemas.TransactionsSchema import TransactionCreateSchema
from .sectors import (
    SectorFetchError,
    SectorNotFoundError,
    enrich_with_sectors,
    get_psx_sector,
)

# Job-type identifiers persisted on the Job row, one per supported broker.
# Keyed by the Portfolio.broker enum so the router/service can validate a
# portfolio is actually supported *before* accepting an upload.
BROKER_JOB_TYPES: dict[Broker, str] = {
    Broker.AKD: "AKD_PDF_PROCESSING",
    Broker.MMK: "MMK_PDF_PROCESSING",
}

# Maximum size (in characters) persisted to Job.error_message (String(255)).
_ERROR_MESSAGE_MAX_LEN = 255

_TWO_PLACES = Decimal("0.01")


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
        parsed_sides: list[Side] | None = None
        if sides:
            try:
                parsed_sides = [Side(s.upper()) for s in sides]
            except ValueError as exc:
                valid = ", ".join(s.value for s in Side)
                raise ValidationException(
                    f"Invalid side filter. Valid values: {valid}."
                ) from exc
        return await self.repository.list_for_user(user_id, portfolio_ids, parsed_sides)

    async def create_for_portfolio(
        self, portfolio: Portfolio, obj_in: TransactionCreateSchema
    ) -> Transaction:
        data = obj_in.model_dump()
        symbol = obj_in.symbol.strip().upper()
        data["symbol"] = symbol

        if portfolio.exchange == ExchangeType.PSX:
            # Doubles as symbol validation: PSX has no page / sector for
            # symbols that don't exist. Cached symbols never hit the network.
            try:
                data["sector"] = await get_psx_sector(symbol)
            except SectorNotFoundError as exc:
                raise ValidationException("Invalid symbol or Not Supported") from exc
            except SectorFetchError as exc:
                logger.warning("PSX symbol verification failed for %s: %s", symbol, exc)
                raise ValidationException(
                    "Could not verify the symbol with PSX right now. Please try again."
                ) from exc

        data["company"] = data.get("company") or symbol
        data["total_amount"] = self._resolve_total_amount(obj_in)
        data["portfolio_id"] = portfolio.id
        return await self.repository.create(data)

    @staticmethod
    def _resolve_total_amount(obj_in: TransactionCreateSchema) -> Decimal:
        """Cash amount for the trade. Holdings treats this as the real cash
        flow, i.e. BUY = gross + fees and SELL = gross - fees. An explicit
        positive value from the client wins."""
        if obj_in.total_amount > 0:
            return obj_in.total_amount

        if obj_in.side not in (Side.BUY, Side.SELL):
            raise ValidationException(
                f"total_amount is required for {obj_in.side.value} transactions."
            )

        gross = obj_in.quantity * obj_in.rate
        fees = obj_in.commission + obj_in.taxes + obj_in.charges
        total = gross + fees if obj_in.side == Side.BUY else gross - fees
        if obj_in.side == Side.SELL and total <= 0:
            raise ValidationException(
                "Sell proceeds must be greater than the transaction fees."
            )
        return total.quantize(_TWO_PLACES)

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


async def _parse_akd_rows(file_path: str) -> tuple[list[dict], list[str]]:
    """Run the (blocking) AKD parser off the event loop, normalize its
    dataclass output into the same row shape the MMK parser produces, and
    fill in any sectors the parser's cache didn't know about via the shared
    PSX sector lookup. Returns (rows, parser warnings)."""
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
        # Mutates the dicts in place (they're the same objects held in `rows`).
        await enrich_with_sectors(missing_sector_rows)

    return rows, [w.message for w in result.warnings]


def _dedupe_key(
    txn_date, symbol: str, side: Side, quantity: Decimal, rate: Decimal, total: Decimal
) -> tuple:
    """Identity of a trade for re-upload detection. Money values are rounded to
    2 dp so rows compare equal regardless of column scale."""
    return (
        txn_date,
        symbol.upper(),
        side,
        Decimal(quantity).quantize(_TWO_PLACES),
        Decimal(rate).quantize(_TWO_PLACES),
        abs(Decimal(total)).quantize(_TWO_PLACES),
    )


async def _existing_trade_counts(
    db, portfolio_id: UUID, dates: set[date], symbols: set[str]
) -> Counter:
    result = await db.execute(
        select(
            Transaction.transaction_date,
            Transaction.symbol,
            Transaction.side,
            Transaction.quantity,
            Transaction.rate,
            Transaction.total_amount,
        ).where(
            Transaction.portfolio_id == portfolio_id,
            Transaction.transaction_date.in_(dates),
            Transaction.symbol.in_(symbols),
        )
    )
    return Counter(_dedupe_key(*row) for row in result.all())


async def run_pdf_processing_job(
    portfolio_id: UUID, file_path: str, job_id: UUID, broker: Broker
) -> None:
    """Background task: parse the uploaded broker statement PDF (dispatching
    on `broker`), persist the resulting transactions, and update the job's
    status. Uses its own DB session since it keeps running after the
    request/response cycle has ended."""
    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        logger.info(
            "Running PDF processing job %s for portfolio %s (broker %s)",
            job_id,
            portfolio_id,
            broker,
        )

        job = await job_repo.get(job_id)
        if job is None:
            logger.warning("PDF processing job %s not found; discarding upload", job_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        try:
            job.status = JobStatus.IN_PROGRESS
            await db.commit()

            warnings: list[str] = []
            if broker == Broker.MMK:
                rows = await process_mmk_statement(file_path)
            elif broker == Broker.AKD:
                rows, warnings = await _parse_akd_rows(file_path)
            else:
                raise ValidationException(f"Unsupported broker for PDF parsing: {broker}")

            for w in warnings:
                logger.warning("Job %s parser warning: %s", job_id, w)

            # Serialize imports for the same portfolio so concurrent uploads
            # cannot both observe a trade as absent before inserting it.
            await db.execute(
                select(Portfolio.id)
                .where(Portfolio.id == portfolio_id)
                .with_for_update()
            )

            # Skip trades that are already stored (re-uploading the same
            # statement). A multiset is used so genuinely identical fills
            # within one statement are all kept; only as many as already
            # exist are treated as duplicates.
            statement_dates = {
                datetime.strptime(row["date"], "%Y-%m-%d").date() for row in rows
            }
            statement_symbols = {str(row["symbol"]).upper() for row in rows}
            remaining = await _existing_trade_counts(
                db, portfolio_id, statement_dates, statement_symbols
            )

            new_transactions: list[Transaction] = []
            skipped = 0
            for row in rows:
                parsed_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                side = Side[str(row["side"]).upper()]
                quantity = _to_decimal(row["quantity"])
                rate = _to_decimal(row["rate"])
                total_amount = abs(_to_decimal(row["total_amount"]))

                key = _dedupe_key(
                    parsed_date, row["symbol"], side, quantity, rate, total_amount
                )
                if remaining[key] > 0:
                    remaining[key] -= 1
                    skipped += 1
                    continue

                new_transactions.append(
                    Transaction(
                        portfolio_id=portfolio_id,
                        transaction_date=parsed_date,
                        company=row["company"],
                        symbol=row["symbol"].upper(),
                        sector=row.get("sector"),
                        side=side,
                        quantity=quantity,
                        rate=rate,
                        commission=_to_decimal(row.get("commission", 0)),
                        taxes=_to_decimal(row.get("taxes", 0)),
                        charges=_to_decimal(row.get("charges", 0)),
                        total_amount=total_amount,
                    )
                )

            db.add_all(new_transactions)
            await db.flush()

            summary = f"Processed {len(new_transactions)} new transaction(s)"
            if skipped:
                summary += f", skipped {skipped} already imported"
            if warnings:
                summary += f", {len(warnings)} parser warning(s)"
            job.status = JobStatus.COMPLETED
            job.result = summary[:_ERROR_MESSAGE_MAX_LEN]
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
