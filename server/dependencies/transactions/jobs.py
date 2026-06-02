from datetime import datetime, timezone
import time
import asyncio
import uuid
import os
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from services.psx_statement_parsing_async_service import process_statement
from models.Jobs import Job, JobStatus
from db.database import get_db
from models.Transaction import Transaction


def run_background_job_pipeline(
    portfolio_id: uuid.UUID, file_path: str, job_id: uuid.UUID
):
    """Wrapper execution that handles processing logic and cleanup inside the background thread."""
    # Create a brand new isolated DB session for the background thread
    db = next(get_db())
    try:
        # Fetch the previously committed job row
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        # 1. Change status to IN_PROGRESS and commit immediately
        job.status = JobStatus.IN_PROGRESS  # Ensure IN_PROGRESS exists in your JobStatus enum
        db.commit()

        # 2. Artificial delay for UI/polling testing
        time.sleep(3)

        # Execute processing logic
        data = asyncio.run(process_statement(file_path))

        if data:
            job.status = JobStatus.COMPLETED
            job.result = "Processing completed successfully"

            for transaction_data in data:
                parsed_date = datetime.strptime(
                    transaction_data["date"], "%Y-%m-%d"
                ).date()

                transaction = Transaction(
                    portfolio_id=portfolio_id,
                    transaction_date=parsed_date,
                    company=transaction_data["company"],
                    symbol=transaction_data["symbol"],
                    sector=transaction_data.get(
                        "sector"
                    ),  # Use get() since nullable=True
                    side=transaction_data[
                        "side"
                    ],  # String 'BUY'/'SELL' matches your Enum schema
                    quantity=transaction_data["quantity"],
                    rate=transaction_data["rate"],
                    commission=transaction_data.get("commission", 0.00),
                    taxes=transaction_data.get("taxes", 0.00),
                    charges=transaction_data.get("charges", 0.00),
                    total_amount=transaction_data["total_amount"],
                )
                db.add(transaction)

        else:
            job.status = JobStatus.FAILED
            job.error_message = "Processing failed"
            print(f"Background job {job_id} failed during processing")

        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
        # Clean up file system artifacts
        if os.path.exists(file_path):
            os.remove(file_path)


def process_mmk_pdf_background(
    background_tasks: BackgroundTasks,
    portfolio_id: uuid.UUID,
    file_path: str,
    db: Session,
) -> uuid.UUID:
    """Initializes the job record during the request cycle and enqueues the worker thread."""
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        job_type="MMK_PDF_PROCESSING",
        payload={"file_path": file_path, "portfolio_id": str(portfolio_id)},
        started_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    db.add(job)
    db.commit()

    # Enqueue the actual logic execution wrapper
    background_tasks.add_task(
        run_background_job_pipeline,
        portfolio_id=portfolio_id,
        file_path=file_path,
        job_id=job_id,
    )

    return job_id
