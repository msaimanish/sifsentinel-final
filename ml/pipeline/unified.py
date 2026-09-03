from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_unified_intelligence(
    canonical_path: str | Path,
    sif_path: str | Path,
    precursor_path: str | Path,
    lsr_path: str | Path,
) -> pd.DataFrame:

    canonical = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    sif = pd.read_csv(
        sif_path,
        low_memory=False,
    )

    precursor = pd.read_csv(
        precursor_path,
        low_memory=False,
    )

    lsr = pd.read_csv(
        lsr_path,
        low_memory=False,
    )

    for df in [canonical, sif, precursor, lsr]:
        df["report_id"] = (
            df["report_id"]
            .astype(str)
            .str.strip()
        )

    canonical_required = {
        "report_id",
        "event_date",
        "description",
        "nature",
        "event",
    }

    sif_required = {
        "report_id",
        "sif_probability",
        "predicted_sif",
    }

    precursor_required = {
        "report_id",
        "activity",
        "activity_evidence",
        "hazard",
        "hazard_evidence",
        "exposure",
        "exposure_evidence",
        "barrier",
        "barrier_evidence",
        "barrier_status",
        "barrier_failure",
        "barrier_failure_evidence",
        "barrier_failure_status",
    }

    lsr_required = {
        "report_id",
        "life_saving_rules",
        "lsr_confidence",
        "lsr_reason",
    }

    if missing := canonical_required - set(canonical.columns):
        raise ValueError(
            f"Canonical data missing columns: {sorted(missing)}"
        )

    if missing := sif_required - set(sif.columns):
        raise ValueError(
            f"SIF result missing columns: {sorted(missing)}"
        )

    if missing := precursor_required - set(precursor.columns):
        raise ValueError(
            "Precursor result missing columns: "
            f"{sorted(missing)}"
        )

    if missing := lsr_required - set(lsr.columns):
        raise ValueError(
            f"LSR result missing columns: {sorted(missing)}"
        )

    # ---------------------------------------------------------
    # Keep the core report metadata.
    # ---------------------------------------------------------
    metadata = canonical[
        [
            "report_id",
            "event_date",
            "description",
            "nature",
            "event",
            "employer",
            "city",
            "state",
            "naics",
            "report_type",
            "data_source",
        ]
    ].copy()


    sif = sif[
        [
            "report_id",
            "sif_probability",
            "predicted_sif",
        ]
    ].copy()

    precursor = precursor[
        [
            "report_id",
            "activity",
            "activity_evidence",
            "hazard",
            "hazard_evidence",
            "exposure",
            "exposure_evidence",
            "barrier",
            "barrier_evidence",
            "barrier_status",
            "barrier_failure",
            "barrier_failure_evidence",
            "barrier_failure_status",
        ]
    ].copy()

    lsr = lsr[
        [
            "report_id",
            "life_saving_rules",
            "lsr_confidence",
            "lsr_reason",
        ]
    ].copy()

    # ---------------------------------------------------------
    # Build the unified record.
    # ---------------------------------------------------------

    unified = metadata.merge(
        sif,
        on="report_id",
        how="inner",
        validate="one_to_one",
    )

    unified = unified.merge(
        lsr,
        on="report_id",
        how="left",
        validate="one_to_one",
    )

    unified = unified.merge(
        precursor,
        on="report_id",
        how="left",
        validate="one_to_one",
    )

    text_columns = [
        "life_saving_rules",
        "lsr_reason",
        "activity",
        "activity_evidence",
        "hazard",
        "hazard_evidence",
        "exposure",
        "exposure_evidence",
        "barrier",
        "barrier_evidence",
        "barrier_status",
        "barrier_failure",
        "barrier_failure_evidence",
        "barrier_failure_status",
    ]

    for column in text_columns:
        unified[column] = (
            unified[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    unified["has_lsr"] = (
        unified["life_saving_rules"] != ""
    )

    unified["has_activity"] = (
        unified["activity"] != ""
    )

    unified["has_hazard"] = (
        unified["hazard"] != ""
    )

    unified["has_exposure"] = (
        unified["exposure"] != ""
    )

    unified["has_barrier"] = (
        unified["barrier"] != ""
    )

    unified["has_barrier_failure"] = (
        unified["barrier_failure"] != ""
    )

    if unified["report_id"].duplicated().any():
        raise RuntimeError(
            "Unified intelligence contains duplicate report IDs."
        )

    return unified