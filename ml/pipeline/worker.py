from __future__ import annotations

import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models.processing_job import ProcessingJob

from pipeline.ingest import ingest_dataset
from pipeline.validate import validate_dataset
from pipeline.load_reports import load_reports
from pipeline.classify_sif import classify_sif
from pipeline.extract_precursors import extract_precursors
from pipeline.map_lsr import map_lsr
from pipeline.unified import build_unified_intelligence
from pipeline.risk import build_risk_scores
from pipeline.persist import persist_results
from pipeline.generate_embeddings import generate_embeddings

POLL_INTERVAL = 5


def update_job(
    session: Session,
    job: ProcessingJob,
    *,
    status: str | None = None,
    stage: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    error: str | None = None,
) -> None:

    if status is not None:
        job.status = status

    if stage is not None:
        job.current_stage = stage

    if progress is not None:
        job.progress = progress

    if message is not None:
        job.message = message

    if error is not None:
        job.error_message = error

    session.commit()


def process_job(
    session: Session,
    job: ProcessingJob,
) -> None:

    dataset_id = job.dataset_id

    input_path = (
        Path("/data/incoming")
        / f"{dataset_id}.csv"
    )

    output_dir = (
        Path("/data/processed")
        / dataset_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        # -----------------------------------------------------
        # Start
        # -----------------------------------------------------

        update_job(
            session,
            job,
            status="processing",
            stage="ingestion",
            progress=5,
            message="Starting dataset ingestion.",
            error=None,
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Uploaded dataset not found: {input_path}"
            )

        # -----------------------------------------------------
        # Stage 1: ingestion
        # -----------------------------------------------------

        canonical_path = ingest_dataset(
            input_path=input_path,
            output_dir=output_dir,
        )

        update_job(
            session,
            job,
            stage="validation",
            progress=15,
            message="Ingestion complete. Validating dataset.",
        )

        # -----------------------------------------------------
        # Stage 2: validation
        # -----------------------------------------------------

        validate_dataset(
            canonical_path
        )

        update_job(
            session,
            job,
            stage="load_reports",
            progress=25,
            message="Validation complete. Loading reports.",
        )

        # -----------------------------------------------------
        # Stage 3: database report loading
        # -----------------------------------------------------

        load_reports(
            canonical_path
        )

        sif_output = (
            output_dir
            / "sif_predictions.csv"
        )

        update_job(
            session,
            job,
            stage="sif_classification",
            progress=40,
            message="Running SIF classification.",
        )

        # -----------------------------------------------------
        # Stage 4: SIF classification
        # -----------------------------------------------------

        classify_sif(
            canonical_path,
            sif_output,
        )

        precursor_output = (
            output_dir
            / "precursors.csv"
        )

        update_job(
            session,
            job,
            stage="precursors",
            progress=52,
            message="Extracting SIF precursor features.",
        )

        # -----------------------------------------------------
        # Stage 5: precursor extraction
        # -----------------------------------------------------

        extract_precursors(
            canonical_path,
            precursor_output,
        )

        lsr_output = (
            output_dir
            / "lsr.csv"
        )

        update_job(
            session,
            job,
            stage="lsr_mapping",
            progress=62,
            message="Mapping IOGP Life-Saving Rules.",
        )

        # -----------------------------------------------------
        # Stage 6: LSR
        # -----------------------------------------------------

        map_lsr(
            canonical_path,
            lsr_output,
        )

        update_job(
            session,
            job,
            stage="risk_analysis",
            progress=72,
            message="Building unified safety intelligence.",
        )

        # -----------------------------------------------------
        # Stage 7: unified intelligence
        # -----------------------------------------------------

        unified = build_unified_intelligence(
            canonical_path,
            sif_output,
            precursor_output,
            lsr_output,
        )

        # -----------------------------------------------------
        # Stage 8: risk scoring
        # -----------------------------------------------------

        update_job(
            session,
            job,
            stage="risk_analysis",
            progress=78,
            message="Calculating precursor priority.",
        )

        risked = build_risk_scores(
            unified
        )

        # Persist the calculated dataframe in the
        # same output directory for diagnostics.
        risk_output = (
            output_dir
            / "risk.csv"
        )

        risked.to_csv(
            risk_output,
            index=False,
        )

        # -----------------------------------------------------
        # Stage 9: database persistence
        # -----------------------------------------------------

        update_job(
            session,
            job,
            stage="database",
            progress=85,
            message="Saving intelligence to PostgreSQL.",
        )

        persist_results(
            risked
        )
        # -----------------------------------------------------
        # Stage 10: embeddings
        # -----------------------------------------------------

        update_job(
            session,
            job,
            stage="embeddings",
            progress=92,
            message="Generating semantic report embeddings.",
        )

        generate_embeddings(
            canonical_path
        )

        # -----------------------------------------------------
        # Stage 11: complete for now
        # -----------------------------------------------------

        update_job(
            session,
            job,
            status="complete",
            stage="complete",
            progress=100,
            message=(
                f"Processed {len(risked):,} reports successfully."
            ),
        )

        print(
            f"[WORKER] Completed dataset "
            f"{dataset_id}"
        )

    except Exception as exc:

        session.rollback()

        error_message = str(exc)

        print(
            f"[WORKER] Dataset {dataset_id} failed: "
            f"{error_message}"
        )

        update_job(
            session,
            job,
            status="failed",
            stage="error",
            progress=0,
            message="Dataset processing failed.",
            error=error_message,
        )


def get_next_job(
    session: Session,
) -> ProcessingJob | None:

    return (
        session.query(ProcessingJob)
        .filter(
            ProcessingJob.status == "queued"
        )
        .order_by(
            ProcessingJob.created_at.asc()
        )
        .first()
    )


def main() -> None:

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    print("=" * 64)
    print("SIFSentinel ML Worker")
    print("=" * 64)

    while True:

        try:

            with Session(engine) as session:

                job = get_next_job(
                    session
                )

                if job is not None:

                    print(
                        f"[WORKER] Found queued job "
                        f"{job.dataset_id}"
                    )

                    process_job(
                        session,
                        job,
                    )

        except Exception as exc:

            print(
                f"[WORKER] Worker error: {exc}"
            )

        time.sleep(
            POLL_INTERVAL
        )


if __name__ == "__main__":
    main()