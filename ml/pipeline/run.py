#!/usr/bin/env python3

import argparse
from pathlib import Path

from pipeline.config import (
    PROCESSED_DIR,
)

from pipeline.ingest import (
    ingest_dataset,
    create_dataset_id,
)

from pipeline.validate import (
    validate_dataset,
)

from pipeline.load_reports import (
    load_reports,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "SIFSentinel dataset processing pipeline"
        )
    )

    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to an OSHA-format CSV dataset",
    )

    parser.add_argument(
        "--dataset-id",
        default=None,
        help="Optional dataset identifier",
    )

    args = parser.parse_args()

    input_path = args.dataset.resolve()

    if args.dataset_id:
        dataset_id = args.dataset_id
    else:
        dataset_id = create_dataset_id(
            input_path
        )

    output_dir = (
        PROCESSED_DIR / dataset_id
    )

    print()

    print("╔" + "═" * 60 + "╗")

    print(
        "║"
        + " SIFSentinel Dataset Pipeline".center(60)
        + "║"
    )

    print("╚" + "═" * 60 + "╝")

    print()

    print(
        f"Dataset ID : {dataset_id}"
    )

    print(
        f"Input      : {input_path}"
    )

    print(
        f"Output     : {output_dir}"
    )

    # ---------------------------------------------------------
    # Stage 1: Ingestion
    # ---------------------------------------------------------

    print()

    print("[1/3] INGESTION")

    canonical_path = ingest_dataset(
        input_path=input_path,
        output_dir=output_dir,
    )

    # ---------------------------------------------------------
    # Stage 2: Validation
    # ---------------------------------------------------------

    print()

    print("[2/3] VALIDATION")

    validate_dataset(
        canonical_path
    )

    # ---------------------------------------------------------
    # Stage 3: Load Reports
    # ---------------------------------------------------------

    print()

    print("[3/3] LOAD REPORTS")

    load_reports(
        canonical_path
    )

    # ---------------------------------------------------------
    # Complete
    # ---------------------------------------------------------

    print()

    print("=" * 64)

    print("PIPELINE STAGE COMPLETE")

    print("=" * 64)

    print()

    print(
        f"Canonical dataset:"
        f"\n  {canonical_path}"
    )

    print()

    print(
        "Reports have been loaded into PostgreSQL."
    )

    print()


if __name__ == "__main__":
    main()