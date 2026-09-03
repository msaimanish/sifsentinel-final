from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = Path(
    "/workspace/models/sif_baseline_v03.joblib"
)

PROBABILITY_THRESHOLD = 0.50


def make_text(df: pd.DataFrame) -> pd.Series:
    description = (
        df["description"]
        .fillna("")
        .astype(str)
    )

    nature = (
        df["nature"]
        .fillna("")
        .astype(str)
    )

    event = (
        df["event"]
        .fillna("")
        .astype(str)
    )

    return (
        "DESCRIPTION: "
        + description
        + " NATURE: "
        + nature
        + " EVENT: "
        + event
    )


def classify_sif(
    canonical_path: str | Path,
    output_path: str | Path,
) -> Path:

    canonical_path = Path(canonical_path)
    output_path = Path(output_path)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"SIF model not found: {MODEL_PATH}"
        )

    df = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    required_columns = {
        "report_id",
        "description",
        "nature",
        "event",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Missing SIF model input columns: "
            f"{sorted(missing)}"
        )

    print(
        f"Loading SIF model: {MODEL_PATH}"
    )

    model = joblib.load(MODEL_PATH)

    text = make_text(df)

    print(
        f"Running SIF classification "
        f"for {len(df):,} reports..."
    )

    probabilities = model.predict_proba(
        text
    )[:, 1]

    predictions = (
        probabilities >= PROBABILITY_THRESHOLD
    )

    result = df[
        [
            "report_id",
        ]
    ].copy()

    result["sif_probability"] = probabilities

    result["predicted_sif"] = [
        "YES" if prediction else "NO"
        for prediction in predictions
    ]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print(
        "\nSIF classification complete."
    )

    print(
        pd.Series(result["predicted_sif"])
        .value_counts()
        .to_string()
    )

    print(
        f"\nSaved: {output_path}"
    )

    return output_path
