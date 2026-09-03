from pathlib import Path

import pandas as pd


REQUIRED_CANONICAL_COLUMNS = [
    "report_id",
    "data_source",
    "source_record_id",
    "report_type",
    "event_date",
    "employer",
    "city",
    "state",
    "naics",
    "description",
    "nature",
    "event",
    "source",
    "secondary_source",
    "federal_state",
    "hospitalized",
    "amputation",
    "loss_of_eye",
    "outcome_severity_anchor",
    "sif_label",
    "sif_label_status",
    "life_saving_rules",
    "activity",
    "hazard",
    "exposure",
    "barrier",
    "barrier_failure",
    "scenario_group",
]


def validate_dataset(
    canonical_path: Path,
):
    canonical_path = Path(canonical_path)

    print()
    print("=" * 64)
    print("SIFSentinel - Dataset Validation")
    print("=" * 64)

    print(
        f"Input: {canonical_path}"
    )

    if not canonical_path.exists():
        raise FileNotFoundError(
            f"Canonical dataset does not exist: "
            f"{canonical_path}"
        )

    df = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    # ---------------------------------------------------------
    # Columns
    # ---------------------------------------------------------

    missing = [
        column
        for column in REQUIRED_CANONICAL_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing canonical columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    # ---------------------------------------------------------
    # Basic quality checks
    # ---------------------------------------------------------

    report_ids_missing = int(
        df["report_id"]
        .isna()
        .sum()
    )

    descriptions_missing = int(
        df["description"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
    )

    duplicate_ids = int(
        df["report_id"]
        .duplicated()
        .sum()
    )

    dates_invalid = int(
        pd.to_datetime(
            df["event_date"],
            errors="coerce",
        )
        .isna()
        .sum()
    )

    report = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_report_ids": report_ids_missing,
        "missing_descriptions": descriptions_missing,
        "duplicate_report_ids": duplicate_ids,
        "invalid_event_dates": dates_invalid,
        "valid": (
            report_ids_missing == 0
            and descriptions_missing == 0
            and duplicate_ids == 0
            and dates_invalid == 0
        ),
    }

    print()
    print(
        f"Rows:                  {report['rows']:,}"
    )
    print(
        f"Missing report IDs:    "
        f"{report['missing_report_ids']:,}"
    )
    print(
        f"Missing descriptions:  "
        f"{report['missing_descriptions']:,}"
    )
    print(
        f"Duplicate report IDs:  "
        f"{report['duplicate_report_ids']:,}"
    )
    print(
        f"Invalid dates:         "
        f"{report['invalid_event_dates']:,}"
    )

    if not report["valid"]:
        raise ValueError(
            "Dataset validation failed."
        )

    print()
    print("Validation: PASSED")

    return report