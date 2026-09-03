from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.embedding import ReportEmbedding
from app.models.report import Report
from app.models.intelligence import ReportIntelligence


EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"


def has_embedding(
    db: Session,
    report_id: int,
) -> bool:
    result = db.scalar(
        select(ReportEmbedding.id)
        .where(
            ReportEmbedding.report_id == report_id,
            ReportEmbedding.model_name == EMBEDDING_MODEL,
        )
        .limit(1)
    )

    return result is not None


def find_similar_reports(
    db: Session,
    report_id: int,
    limit: int = 5,
):
    query_embedding = db.scalar(
        select(ReportEmbedding.embedding)
        .where(
            ReportEmbedding.report_id == report_id,
            ReportEmbedding.model_name == EMBEDDING_MODEL,
        )
        .limit(1)
    )

    if query_embedding is None:
        return []

    distance = (
        ReportEmbedding.embedding.cosine_distance(
            query_embedding
        )
    )

    statement = (
        select(
            Report.id,
            Report.report_id,
            Report.description,
            Report.event_date,
            Report.employer,
            Report.city,
            Report.state,
            distance.label("distance"),
        )
        .join(
            ReportEmbedding,
            ReportEmbedding.report_id == Report.id,
        )
        .where(
            Report.id != report_id,
            ReportEmbedding.model_name == EMBEDDING_MODEL,
        )
        .order_by(distance)
        .limit(limit)
    )

    rows = db.execute(statement).all()

    results = []

    for row in rows:

        intelligence = db.scalar(
            select(ReportIntelligence)
            .where(
                ReportIntelligence.report_id == row.report_id
            )
            .limit(1)
        )

        results.append(
            {
                "report_id": row.report_id,

                "similarity": round(
                    1 - float(row.distance),
                    4,
                ),

                "event_date": row.event_date,

                "employer": row.employer,

                "city": row.city,

                "state": row.state,

                "description": row.description,

                "sif_probability": (
                    intelligence.sif_probability
                    if intelligence
                    else None
                ),

                "sif_label": (
                    intelligence.sif_label
                    if intelligence
                    else None
                ),

                "life_saving_rules": (
                    intelligence.life_saving_rules
                    if intelligence
                    and intelligence.life_saving_rules
                    else []
                ),

                "activity": (
                    intelligence.activity
                    if intelligence
                    else None
                ),

                "hazard": (
                    intelligence.hazard
                    if intelligence
                    else None
                ),

                "exposure": (
                    intelligence.exposure
                    if intelligence
                    else None
                ),

                "barrier": (
                    intelligence.barrier
                    if intelligence
                    else None
                ),

                "barrier_failure": (
                    intelligence.barrier_failure
                    if intelligence
                    else None
                ),

                "priority_score": (
                    intelligence.priority_score
                    if intelligence
                    else None
                ),

                "priority_band": (
                    intelligence.priority_band
                    if intelligence
                    else None
                ),
            }
        )

    return results