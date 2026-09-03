from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models.report import Report


BATCH_SIZE = 2000


def clean_value(value):
    if pd.isna(value):
        return None
    return value


def clean_int(value):
    if pd.isna(value):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_date(value):
    if pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.date()


def load_reports(canonical_path: str | Path) -> dict:
    canonical_path = Path(canonical_path)

    print("=" * 64)
    print("SIFSentinel Report Loader")
    print("=" * 64)

    if not canonical_path.exists():
        raise FileNotFoundError(
            f"Canonical CSV not found: {canonical_path}"
        )

    print(f"\nReading: {canonical_path}")

    df = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    print(f"Loaded {len(df):,} CSV rows.")

    required_columns = {
        "report_id",
        "data_source",
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
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Canonical CSV is missing required columns: "
            f"{sorted(missing)}"
        )

    # Defensive deduplication.
    df = df.drop_duplicates(
        subset=["report_id"]
    ).copy()

    print(
        f"After report_id deduplication: "
        f"{len(df):,}"
    )

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    # Make sure ORM tables exist.
    Base.metadata.create_all(
        bind=engine,
    )

    with Session(engine) as session:
        existing_ids = {
            row[0]
            for row in session.query(Report.report_id).all()
        }

    print(
        f"Existing database reports: "
        f"{len(existing_ids):,}"
    )

    df = df[
        ~df["report_id"].astype(str).isin(existing_ids)
    ].copy()

    print(
        f"New reports to insert: "
        f"{len(df):,}"
    )

    if df.empty:
        print("\nNothing to insert.")

        return {
            "input_rows": int(len(df)),
            "inserted_rows": 0,
            "skipped_existing": 0,
        }

    total = len(df)

    for start in range(0, total, BATCH_SIZE):
        batch = df.iloc[start:start + BATCH_SIZE]

        objects: list[Report] = []

        for _, row in batch.iterrows():
            description = clean_value(row["description"])

            if description is None:
                description = ""

            objects.append(
                Report(
                    report_id=str(row["report_id"]),
                    data_source=clean_value(
                        row["data_source"]
                    ),
                    report_type=clean_value(
                        row["report_type"]
                    ),
                    event_date=parse_date(
                        row["event_date"]
                    ),
                    employer=clean_value(
                        row["employer"]
                    ),
                    city=clean_value(
                        row["city"]
                    ),
                    state=clean_value(
                        row["state"]
                    ),
                    naics=clean_value(
                        row["naics"]
                    ),
                    candidate_oil_gas=clean_int(
                        row.get("candidate_oil_gas")
                    ) or 0,
                    description=str(description),
                    nature=clean_value(
                        row["nature"]
                    ),
                    event=clean_value(
                        row["event"]
                    ),
                    source=clean_value(
                        row["source"]
                    ),
                    secondary_source=clean_value(
                        row["secondary_source"]
                    ),
                    federal_state=clean_int(
                        row["federal_state"]
                    ),
                    hospitalized=clean_int(
                        row["hospitalized"]
                    ),
                    amputation=clean_int(
                        row["amputation"]
                    ),
                    loss_of_eye=clean_int(
                        row["loss_of_eye"]
                    ),
                )
            )

        with Session(engine) as session:
            session.add_all(objects)
            session.commit()

        inserted = min(
            start + len(batch),
            total,
        )

        print(
            f"Inserted {inserted:,} / {total:,}"
        )

    result = {
        "input_rows": int(len(df)),
        "inserted_rows": int(total),
        "skipped_existing": int(len(existing_ids)),
    }

    print("\n" + "=" * 64)
    print("REPORT LOADING COMPLETE")
    print("=" * 64)

    return result


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python -m pipeline.load_reports "
            "<canonical.csv>"
        )
        raise SystemExit(1)

    load_reports(sys.argv[1])


if __name__ == "__main__":
    main()
