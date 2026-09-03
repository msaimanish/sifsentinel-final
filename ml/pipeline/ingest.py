from pathlib import Path
import shutil

import pandas as pd


REQUIRED_COLUMNS = [
    "ID",
    "EventDate",
    "Employer",
    "City",
    "State",
    "Primary NAICS",
    "Hospitalized",
    "Amputation",
    "Loss of Eye",
    "Final Narrative",
    "NatureTitle",
    "EventTitle",
    "SourceTitle",
    "Secondary Source Title",
    "FederalState",
]


def clean_text(value) -> str:
    if pd.isna(value):
        return ""

    text = str(value)

    text = (
        text
        .replace("\r\n", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )

    return " ".join(text.split())


def create_dataset_id(input_path: Path) -> str:
    """
    Convert a dataset filename into a safe dataset ID.

    Example:
        OSHA_2026.csv
        -> OSHA_2026
    """

    return input_path.stem.lower().replace(" ", "_")


def ingest_dataset(
    input_path: Path,
    output_dir: Path,
) -> Path:

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    print()
    print("=" * 64)
    print("SIFSentinel - Dataset Ingestion")
    print("=" * 64)

    print(f"Input : {input_path}")
    print(f"Output: {output_dir}")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Dataset does not exist: {input_path}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Read dataset
    # ---------------------------------------------------------

    df = pd.read_csv(
        input_path,
        low_memory=False,
    )

    print(
        f"Loaded {len(df):,} rows."
    )

    # ---------------------------------------------------------
    # Validate source columns
    # ---------------------------------------------------------

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Dataset is missing required OSHA columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    # ---------------------------------------------------------
    # Remove duplicate IDs
    # ---------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["ID"],
        keep="first",
    ).copy()

    duplicates_removed = (
        before - len(df)
    )

    # ---------------------------------------------------------
    # Canonical report schema
    # ---------------------------------------------------------

    canonical = pd.DataFrame()

    canonical["report_id"] = (
        df["ID"]
        .astype(str)
        .str.strip()
    )

    canonical["data_source"] = "osha"

    canonical["source_record_id"] = (
        df["ID"]
        .astype(str)
        .str.strip()
    )

    canonical["report_type"] = "incident"

    canonical["event_date"] = (
        pd.to_datetime(
            df["EventDate"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    canonical["employer"] = (
        df["Employer"]
        .map(clean_text)
    )

    canonical["city"] = (
        df["City"]
        .map(clean_text)
    )

    canonical["state"] = (
        df["State"]
        .map(clean_text)
    )

    canonical["naics"] = (
        df["Primary NAICS"]
        .astype("string")
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .fillna("")
        .str.strip()
    )

    canonical["description"] = (
        df["Final Narrative"]
        .map(clean_text)
    )

    canonical["nature"] = (
        df["NatureTitle"]
        .map(clean_text)
    )

    canonical["event"] = (
        df["EventTitle"]
        .map(clean_text)
    )

    canonical["source"] = (
        df["SourceTitle"]
        .map(clean_text)
    )

    canonical["secondary_source"] = (
        df["Secondary Source Title"]
        .map(clean_text)
    )

    canonical["federal_state"] = (
        df["FederalState"]
        .map(clean_text)
    )

    canonical["hospitalized"] = (
        df["Hospitalized"]
        .map(clean_text)
    )

    canonical["amputation"] = (
        df["Amputation"]
        .map(clean_text)
    )

    canonical["loss_of_eye"] = (
        df["Loss of Eye"]
        .map(clean_text)
    )

    # These fields intentionally remain empty at ingestion.
    # They are generated later by the intelligence pipeline.
    canonical["outcome_severity_anchor"] = 1

    canonical["sif_label"] = ""

    canonical["sif_label_status"] = "unannotated"

    canonical["life_saving_rules"] = ""

    canonical["activity"] = ""

    canonical["hazard"] = ""

    canonical["exposure"] = ""

    canonical["barrier"] = ""

    canonical["barrier_failure"] = ""

    canonical["scenario_group"] = ""

    # ---------------------------------------------------------
    # Remove empty narratives
    # ---------------------------------------------------------

    canonical = canonical[
        canonical["description"].str.strip() != ""
    ].copy()

    canonical = canonical.reset_index(
        drop=True
    )

    # ---------------------------------------------------------
    # Write canonical dataset
    # ---------------------------------------------------------

    output_path = (
        output_dir / "canonical.csv"
    )

    canonical.to_csv(
        output_path,
        index=False,
    )

    # ---------------------------------------------------------
    # Write ingestion metadata
    # ---------------------------------------------------------

    metadata = {
        "input_file": str(input_path),
        "input_rows": int(before),
        "duplicate_ids_removed": int(
            duplicates_removed
        ),
        "empty_narratives_removed": int(
            before
            - duplicates_removed
            - len(canonical)
        ),
        "canonical_rows": int(
            len(canonical)
        ),
        "columns": list(
            canonical.columns
        ),
    }

    metadata_path = (
        output_dir / "ingestion_stats.json"
    )

    metadata_path.write_text(
        __import__("json").dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Preserve source filename
    # ---------------------------------------------------------

    source_copy = (
        output_dir
        / f"source_{input_path.name}"
    )

    shutil.copy2(
        input_path,
        source_copy,
    )

    print()
    print(
        f"Canonical rows: {len(canonical):,}"
    )
    print(
        f"Duplicates removed: "
        f"{duplicates_removed:,}"
    )
    print()
    print(
        f"Saved: {output_path}"
    )
    print(
        f"Saved: {metadata_path}"
    )

    return output_path