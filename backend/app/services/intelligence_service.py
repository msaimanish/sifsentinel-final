from sqlalchemy.orm import Session

from app.models.intelligence import ReportIntelligence


def get_intelligence(
    db: Session,
    report_id: str,
):
    return (
        db.query(ReportIntelligence)
        .filter(ReportIntelligence.report_id == report_id)
        .first()
    )


def intelligence_to_dict(row):
    if not row:
        return None

    return {
        "sif_probability": row.sif_probability,
        "sif_label": row.sif_label,
        "life_saving_rules": row.life_saving_rules or [],
        "activity": row.activity,
        "hazard": row.hazard,
        "exposure": row.exposure,
        "barrier": row.barrier,
        "barrier_failure": row.barrier_failure,
        "priority_score": row.priority_score,
        "priority_band": row.priority_band,
    }
