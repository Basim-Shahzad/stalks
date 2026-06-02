import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.models.Jobs import Job

router = APIRouter()


@router.get("/status/{job_id}", status_code=status.HTTP_200_OK)
def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,  # PENDING, IN_PROGRESS, COMPLETED, FAILED
        "error_message": job.error_message,
    }
