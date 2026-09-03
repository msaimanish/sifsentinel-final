from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import ModelPrediction
from app.models.report import Report
from app.models.intelligence import ReportIntelligence

from app.services.similarity_service import (
    find_similar_reports,
    has_embedding,
)


def _parse_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def build_analysis(
    db: Session,
    report_id: str,
):
    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------

    report = db.scalar(
        select(Report).where(
            Report.report_id == report_id
        )
    )

    if report is None:
        return None



    # ---------------------------------------------------------
    # STORED MODEL PREDICTION
    # ---------------------------------------------------------

    prediction = db.scalar(
        select(ModelPrediction)
        .where(
            ModelPrediction.report_id == report.id
        )
        .order_by(
            ModelPrediction.id.desc()
        )
    )

    # ---------------------------------------------------------
    # UNIFIED INTELLIGENCE
    # ---------------------------------------------------------

    intelligence = db.scalar(
        select(ReportIntelligence)
        .where(
            ReportIntelligence.report_id == report_id
        )
        .limit(1)
    )

    # ---------------------------------------------------------
    # SIF ASSESSMENT
    #
    # Stored prediction takes precedence over imported
    # intelligence.
    # ---------------------------------------------------------

    if prediction:
        sif_probability = prediction.sif_probability
        sif_label = prediction.sif_label
        model_version = prediction.model_version
    elif intelligence:
        sif_probability = intelligence.sif_probability
        sif_label = intelligence.sif_label
        model_version = "unified_intelligence_v01"
    else:
        sif_probability = None
        sif_label = None
        model_version = None

    # ---------------------------------------------------------
    # SAFETY FEATURES
    # ---------------------------------------------------------

    if intelligence:
        activity = intelligence.activity

        hazards = (
            [intelligence.hazard]
            if intelligence.hazard
            else []
        )

        exposure = intelligence.exposure

        barriers = (
            [intelligence.barrier]
            if intelligence.barrier
            else []
        )

        barrier_failures = (
            [intelligence.barrier_failure]
            if intelligence.barrier_failure
            else []
        )

        life_saving_rules = (
            intelligence.life_saving_rules
            if intelligence.life_saving_rules
            else []
        )

    else:
        activity = None
        hazards = []
        exposure = None
        barriers = []
        barrier_failures = []
        life_saving_rules = []
    # ---------------------------------------------------------
    # RISK
    # ---------------------------------------------------------

    risk = {
        "score": (
            intelligence.priority_score
            if intelligence
            else None
        ),
        "band": (
            intelligence.priority_band
            if intelligence
            else None
        ),
    }

    # ---------------------------------------------------------
    # SIMILAR REPORTS
    # ---------------------------------------------------------

    similar = find_similar_reports(
        db=db,
        report_id=report.id,
        limit=5,
    )

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {
        "report": {
            "report_id": report.report_id,
            "event_date": report.event_date,
            "employer": report.employer,
            "city": report.city,
            "state": report.state,
            "naics": report.naics,
            "event": report.event,
            "nature": report.nature,
            "description": report.description,
        },

        "sif_assessment": {
            "probability": sif_probability,
            "label": sif_label,
            "model_version": model_version,
        },

        "safety_features": {
            "activity": activity,
            "hazards": hazards,
            "exposure": exposure,
            "barriers": barriers,
            "barrier_failures": barrier_failures,
            "life_saving_rules": life_saving_rules,
        },

        "risk": risk,

        "similar_reports": similar,

        "status": {
            "has_prediction": prediction is not None,
            "has_embedding": has_embedding(
                db,
                report.id,
            ),
            "has_intelligence": intelligence is not None,
        },
    }