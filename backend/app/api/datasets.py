from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.processing_job import ProcessingJob


router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)


UPLOAD_DIR = Path("/data/incoming")


def make_dataset_id(name: str) -> str:

    cleaned = name.strip().lower()

    cleaned = re.sub(
        r"[^a-z0-9]+",
        "_",
        cleaned,
    )

    cleaned = cleaned.strip("_")

    if not cleaned:
        cleaned = "dataset"

    return f"{cleaned}_{uuid.uuid4().hex[:8]}"


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    dataset_name = dataset_name.strip()

    if not dataset_name:
        raise HTTPException(
            status_code=400,
            detail="Dataset name cannot be empty.",
        )

    dataset_id = make_dataset_id(
        dataset_name
    )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        UPLOAD_DIR /
        f"{dataset_id}.csv"
    )

    try:

        with output_path.open("wb") as destination:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                destination.write(chunk)

    except Exception as exc:

        if output_path.exists():
            output_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save uploaded file: {exc}",
        ) from exc

    job = ProcessingJob(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        filename=file.filename,
        status="queued",
        current_stage="queued",
        progress=0,
        message="Dataset uploaded and queued for processing.",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "dataset_id": job.dataset_id,
        "dataset_name": job.dataset_name,
        "filename": job.filename,
        "status": job.status,
        "stage": job.current_stage,
        "progress": job.progress,
        "message": job.message,
    }


@router.get("/{dataset_id}/status")
def dataset_status(
    dataset_id: str,
    db: Session = Depends(get_db),
):

    job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.dataset_id == dataset_id
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    return {
        "dataset_id": job.dataset_id,
        "dataset_name": job.dataset_name,
        "filename": job.filename,
        "status": job.status,
        "stage": job.current_stage,
        "progress": job.progress,
        "message": job.message,
        "error": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }

@router.post("/{dataset_id}/retry")
def retry_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.dataset_id == dataset_id
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    if job.status == "queued" or job.status == "processing":
        raise HTTPException(
            status_code=409,
            detail="Dataset is already being processed.",
        )

    job.status = "queued"
    job.current_stage = "queued"
    job.progress = 0
    job.message = "Dataset requeued for processing."
    job.error_message = None

    db.commit()
    db.refresh(job)

    return {
        "dataset_id": job.dataset_id,
        "dataset_name": job.dataset_name,
        "filename": job.filename,
        "status": job.status,
        "stage": job.current_stage,
        "progress": job.progress,
        "message": job.message,
    }