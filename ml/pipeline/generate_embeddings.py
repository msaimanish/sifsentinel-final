from __future__ import annotations

from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.embedding import ReportEmbedding
from app.models.report import Report


MODEL_NAME = "BAAI/bge-base-en-v1.5"
BATCH_SIZE = 32


def build_embedding_text(row: pd.Series) -> str:
    """
    Build the text that will be converted into a semantic embedding.
    """

    parts = [
        str(row.get("description", "") or ""),
        str(row.get("nature", "") or ""),
        str(row.get("event", "") or ""),
    ]

    return " ".join(
        part.strip()
        for part in parts
        if part.strip()
    )


def generate_embeddings(
    canonical_path: str | Path,
) -> int:
    """
    Generate and store embeddings for reports in canonical.csv.

    Returns:
        Number of new embeddings generated.
    """

    canonical_path = Path(canonical_path)

    print(
        f"Loading canonical dataset: {canonical_path}"
    )

    df = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    if "report_id" not in df.columns:
        raise ValueError(
            "Canonical dataset is missing report_id."
        )

    # ---------------------------------------------------------
    # Load embedding model
    # ---------------------------------------------------------

    print(
        f"Loading embedding model: {MODEL_NAME}"
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    # ---------------------------------------------------------
    # Prepare report IDs and text
    # ---------------------------------------------------------

    df["report_id"] = (
        df["report_id"]
        .astype(str)
        .str.strip()
    )

    texts = [
        build_embedding_text(row)
        for _, row in df.iterrows()
    ]

    report_ids = df["report_id"].tolist()

    # ---------------------------------------------------------
    # Look up corresponding database reports
    # ---------------------------------------------------------

    with Session(engine) as session:

        reports = session.execute(
            select(Report)
            .where(
                Report.report_id.in_(report_ids)
            )
        ).scalars().all()

        report_by_external_id = {
            report.report_id: report
            for report in reports
        }

        # -----------------------------------------------------
        # Find embeddings that already exist
        # -----------------------------------------------------

        existing_rows = session.execute(
            select(ReportEmbedding.report_id)
            .join(
                Report,
                Report.id == ReportEmbedding.report_id,
            )
            .where(
                Report.report_id.in_(report_ids),
                ReportEmbedding.model_name == MODEL_NAME,
            )
        ).all()

        existing_report_ids = {
            row[0]
            for row in existing_rows
        }

        # -----------------------------------------------------
        # Build list of reports requiring embeddings
        # -----------------------------------------------------

        pending = []

        for external_id, text in zip(
            report_ids,
            texts,
        ):

            report = report_by_external_id.get(
                external_id
            )

            if report is None:
                continue

            if report.id in existing_report_ids:
                continue

            if not text.strip():
                continue

            pending.append(
                (
                    report.id,
                    text,
                )
            )

        print(
            f"Reports requiring embeddings: "
            f"{len(pending)}"
        )

        if not pending:
            print(
                "No new embeddings required."
            )
            return 0

        # -----------------------------------------------------
        # Generate embeddings in batches
        # -----------------------------------------------------

        total = 0

        for start in range(
            0,
            len(pending),
            BATCH_SIZE,
        ):

            batch = pending[
                start:start + BATCH_SIZE
            ]

            batch_texts = [
                text
                for _, text in batch
            ]

            print(
                f"Embedding batch "
                f"{start + 1}-"
                f"{start + len(batch)} "
                f"of {len(pending)}"
            )

            vectors = model.encode(
                batch_texts,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            for (
                (report_id, _),
                vector,
            ) in zip(
                batch,
                vectors,
            ):

                session.add(
                    ReportEmbedding(
                        report_id=report_id,
                        model_name=MODEL_NAME,
                        embedding=vector.tolist(),
                    )
                )

            session.commit()

            total += len(batch)

            print(
                f"Stored embeddings: "
                f"{total}/{len(pending)}"
            )

        print(
            f"Embedding generation complete: "
            f"{total} new embeddings."
        )

        return total