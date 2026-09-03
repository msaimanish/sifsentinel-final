from __future__ import annotations

from datetime import datetime
from typing import Any

import math
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models.report import Report
from app.models.prediction import ModelPrediction
from app.models.precursor import PrecursorFeature
from app.models.intelligence import ReportIntelligence


MODEL_VERSION = "sif_baseline_v03"

BATCH_SIZE = 500


def clean(value: Any) -> str | None:

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def parse_float(value: Any) -> float | None:

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(value):
        return None

    return value


def parse_lsr(value: Any) -> list[str]:

    value = clean(value)

    if not value:
        return []

    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]


def make_payload(
    row: pd.Series,
) -> dict[str, Any]:

    payload = {}

    for key, value in row.items():

        if pd.isna(value):
            payload[key] = None

        elif isinstance(
            value,
            pd.Timestamp,
        ):
            payload[key] = value.isoformat()

        else:
            payload[key] = value

    return payload


def persist_results(
    unified: pd.DataFrame,
) -> dict[str, int]:

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    report_ids = (
        unified["report_id"]
        .astype(str)
        .tolist()
    )

    inserted_predictions = 0
    inserted_precursors = 0
    upserted_intelligence = 0

    with Session(engine) as session:

        reports = (
            session.query(Report)
            .filter(
                Report.report_id.in_(report_ids)
            )
            .all()
        )

        report_map = {
            report.report_id: report
            for report in reports
        }

        missing = [
            report_id
            for report_id in report_ids
            if report_id not in report_map
        ]

        if missing:
            raise RuntimeError(
                "Some reports were not loaded into "
                f"PostgreSQL before persistence. "
                f"Missing: {missing[:10]}"
            )

        # -----------------------------------------------------
        # Remove old derived data for these reports.
        # -----------------------------------------------------

        report_db_ids = [
            report.id
            for report in reports
        ]

        session.query(
            ModelPrediction
        ).filter(
            ModelPrediction.report_id.in_(
                report_db_ids
            ),
            ModelPrediction.model_version
            == MODEL_VERSION,
        ).delete(
            synchronize_session=False
        )

        session.query(
            PrecursorFeature
        ).filter(
            PrecursorFeature.report_id.in_(
                report_db_ids
            )
        ).delete(
            synchronize_session=False
        )

        session.commit()

        # -----------------------------------------------------
        # Insert derived results.
        # -----------------------------------------------------

        prediction_batch = []
        precursor_batch = []

        for _, row in unified.iterrows():

            external_id = str(
                row["report_id"]
            )

            report = report_map[
                external_id
            ]

            probability = parse_float(
                row.get("sif_probability")
            )

            sif_label = clean(
                row.get("predicted_sif")
            ) or "NO"

            prediction_batch.append(
                ModelPrediction(
                    report_id=report.id,
                    model_version=MODEL_VERSION,
                    sif_probability=probability or 0.0,
                    sif_label=sif_label,
                    confidence=probability,
                    prediction_timestamp=datetime.utcnow(),
                )
            )

            precursor_batch.append(
                PrecursorFeature(
                    report_id=report.id,
                    activity=clean(
                        row.get("activity")
                    ),
                    hazard=clean(
                        row.get("hazard")
                    ),
                    exposure=clean(
                        row.get("exposure")
                    ),
                    barrier=clean(
                        row.get("barrier")
                    ),
                    barrier_failure=clean(
                        row.get("barrier_failure")
                    ),
                    life_saving_rules=clean(
                        row.get("life_saving_rules")
                    ),
                )
            )

            if len(prediction_batch) >= BATCH_SIZE:

                session.add_all(
                    prediction_batch
                )

                session.add_all(
                    precursor_batch
                )

                session.commit()

                inserted_predictions += (
                    len(prediction_batch)
                )

                inserted_precursors += (
                    len(precursor_batch)
                )

                prediction_batch.clear()
                precursor_batch.clear()

        if prediction_batch:

            session.add_all(
                prediction_batch
            )

            session.add_all(
                precursor_batch
            )

            session.commit()

            inserted_predictions += (
                len(prediction_batch)
            )

            inserted_precursors += (
                len(precursor_batch)
            )

        # -----------------------------------------------------
        # Report intelligence
        # -----------------------------------------------------

        for _, row in unified.iterrows():

            external_id = str(
                row["report_id"]
            )

            intelligence = (
                session.query(
                    ReportIntelligence
                )
                .filter(
                    ReportIntelligence.report_id
                    == external_id
                )
                .first()
            )

            if intelligence is None:

                intelligence = (
                    ReportIntelligence(
                        report_id=external_id
                    )
                )

                session.add(
                    intelligence
                )

            intelligence.sif_probability = (
                parse_float(
                    row.get(
                        "sif_probability"
                    )
                )
            )

            intelligence.sif_label = clean(
                row.get("predicted_sif")
            )

            intelligence.life_saving_rules = (
                parse_lsr(
                    row.get(
                        "life_saving_rules"
                    )
                )
            )

            intelligence.activity = clean(
                row.get("activity")
            )

            intelligence.hazard = clean(
                row.get("hazard")
            )

            intelligence.exposure = clean(
                row.get("exposure")
            )

            intelligence.barrier = clean(
                row.get("barrier")
            )

            intelligence.barrier_failure = clean(
                row.get("barrier_failure")
            )

            intelligence.priority_score = (
                parse_float(
                    row.get(
                        "precursor_priority_score"
                    )
                )
            )

            intelligence.priority_band = clean(
                row.get("priority_band")
            )

            intelligence.payload = (
                make_payload(row)
            )

            upserted_intelligence += 1

        session.commit()

    return {
        "predictions": inserted_predictions,
        "precursors": inserted_precursors,
        "intelligence": upserted_intelligence,
    }
