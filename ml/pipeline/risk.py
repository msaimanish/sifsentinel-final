from __future__ import annotations

import numpy as np
import pandas as pd


def normalize(series: pd.Series) -> pd.Series:
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


def count_semicolon_items(
    series: pd.Series,
) -> pd.Series:
    values = normalize(series)

    return values.apply(
        lambda value: (
            len(
                [
                    item
                    for item in value.split(";")
                    if item.strip()
                ]
            )
            if value
            else 0
        )
    )


def build_risk_scores(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    text_fields = [
        "life_saving_rules",
        "activity",
        "hazard",
        "exposure",
        "barrier",
        "barrier_failure",
        "barrier_status",
        "barrier_failure_status",
    ]

    for field in text_fields:
        if field in df.columns:
            df[field] = normalize(df[field])
        else:
            df[field] = ""

    # ---------------------------------------------------------
    # SIF signal
    # ---------------------------------------------------------

    df["sif_signal"] = (
        pd.to_numeric(
            df["sif_probability"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(0.0, 1.0)
    )

    # ---------------------------------------------------------
    # Precursor richness
    # ---------------------------------------------------------

    precursor_fields = [
        "activity",
        "hazard",
        "exposure",
        "barrier",
        "barrier_failure",
    ]

    df["precursor_count"] = 0

    for field in precursor_fields:
        df["precursor_count"] += (
            df[field] != ""
        ).astype(int)

    df["precursor_signal"] = (
        df["precursor_count"] / 5.0
    )

    # ---------------------------------------------------------
    # LSR signal
    # ---------------------------------------------------------

    df["lsr_count"] = count_semicolon_items(
        df["life_saving_rules"]
    )

    df["lsr_signal"] = (
        df["lsr_count"]
        .clip(upper=3)
        / 3.0
    )

    # ---------------------------------------------------------
    # Barrier failure
    # ---------------------------------------------------------

    df["barrier_failure_signal"] = np.select(
        [
            df["barrier_failure_status"] == "observed",
            df["barrier_failure_status"] == "inferred",
        ],
        [
            1.0,
            0.65,
        ],
        default=0.0,
    )

    # ---------------------------------------------------------
    # Recency
    # ---------------------------------------------------------

    df["event_date"] = pd.to_datetime(
        df["event_date"],
        errors="coerce",
    )

    max_date = df["event_date"].max()

    if pd.notna(max_date):

        age_days = (
            max_date
            - df["event_date"]
        ).dt.days

        df["recency_signal"] = np.exp(
            -age_days.clip(lower=0) / 365.0
        )

    else:
        df["recency_signal"] = 0.0

    # ---------------------------------------------------------
    # Composite priority score
    #
    # 45% SIF
    # 20% precursor richness
    # 15% barrier failure
    # 10% LSR
    # 10% recency
    # ---------------------------------------------------------

    df["precursor_priority_score"] = (
        0.45 * df["sif_signal"]
        + 0.20 * df["precursor_signal"]
        + 0.15 * df["barrier_failure_signal"]
        + 0.10 * df["lsr_signal"]
        + 0.10 * df["recency_signal"]
    ).clip(0.0, 1.0)

    # ---------------------------------------------------------
    # Priority band
    # ---------------------------------------------------------

    df["priority_band"] = pd.cut(
        df["precursor_priority_score"],
        bins=[
            -0.01,
            0.30,
            0.50,
            0.70,
            1.01,
        ],
        labels=[
            "Low",
            "Moderate",
            "High",
            "Critical",
        ],
    ).astype(str)

    return df
