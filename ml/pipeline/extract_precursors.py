#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


# =========================================================
# Helpers
# =========================================================

def normalize(text: str) -> str:
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_evidence(
    text: str,
    patterns: list[str],
) -> str:

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            start = max(
                0,
                match.start() - 60,
            )

            end = min(
                len(text),
                match.end() + 100,
            )

            return text[start:end].strip()

    return ""


def has_match(
    text: str,
    patterns: list[str],
) -> bool:

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


# =========================================================
# ACTIVITY
# =========================================================

ACTIVITIES = {
    "Forklift / powered industrial vehicle": [
        r"\bforklift\b",
        r"\bpallet jack\b",
        r"\bwalkie rider\b",
        r"\breach forklift\b",
        r"\bpowered industrial truck\b",
    ],

    "Crane / lifting operation": [
        r"\bcrane\b",
        r"\bhoist(?:ing)?\b",
        r"\brig blocks\b",
    ],

    "Working at height": [
        r"\bladder\b",
        r"\broof\b",
        r"\bscaffold\b",
        r"\btower\b",
        r"\bplatform\b",
    ],

    "Electrical work": [
        r"\belectrical\b",
        r"\bcircuit breaker\b",
        r"\belectrical panel\b",
        r"\btransformer\b",
        r"\barc flash\b",
    ],

    "Machine operation / maintenance": [
        r"\bconveyor\b",
        r"\bsaw\b",
        r"\bpress\b",
        r"\broller\b",
        r"\blathe\b",
        r"\bgrinder\b",
        r"\brouter\b",
        r"\bthreader\b",
        r"\bmachine\b",
    ],

    "Vehicle operation": [
        r"\btruck\b",
        r"\bpickup\b",
        r"\bvan\b",
        r"\bbus\b",
        r"\bvehicle\b",
        r"\bdriving\b",
        r"\bbacking\b",
        r"\breversing\b",
    ],

    "Hot work": [
        r"\bwelding\b",
        r"\btorch\b",
        r"\bhot work\b",
    ],

    "Pipe / oilfield work": [
        r"\bpipe\b",
        r"\bwell\b",
        r"\bpumping unit\b",
        r"\bblowout preventer\b",
        r"\bscrubber\b",
        r"\brig\b",
    ],

    "Material handling": [
        r"\bunloading\b",
        r"\bloading\b",
        r"\bmoving\b.{0,60}\b(load|equipment|material|part)\b",
        r"\bhandling\b",
    ],
}


# =========================================================
# HAZARD
# =========================================================

HAZARDS = {
    "Moving vehicle": [
        r"\bforklift\b",
        r"\bvehicle\b",
        r"\btruck\b",
        r"\bpickup\b",
        r"\bbacking\b",
        r"\breversing\b",
    ],

    "Moving machinery": [
        r"\bconveyor\b",
        r"\bsaw\b",
        r"\bblade\b",
        r"\broller\b",
        r"\bpress\b",
        r"\blathe\b",
        r"\bgrinder\b",
        r"\brouter\b",
        r"\bmachine\b",
    ],

    "Fall from height": [
        r"\bfell\b",
        r"\bfall(?:ed|ing)?\b",
        r"\broof\b",
        r"\bladder\b",
        r"\bscaffold\b",
        r"\btower\b",
    ],

    "Falling / dropped object": [
        r"\bfalling\b.{0,80}\b(object|pipe|beam|load|material|equipment)\b",
        r"\bdropped\b.{0,80}\b(load|object|material)\b",
        r"\bfalling pipe\b",
        r"\bfalling beam\b",
    ],

    "Electrical energy": [
        r"\barc flash\b",
        r"\belectrical arc\b",
        r"\benergized\b",
        r"\belectrical shock\b",
    ],

    "Fire / explosion": [
        r"\bexplosion\b",
        r"\bfire\b",
        r"\bignit(?:ed|ion|e)?\b",
        r"\bflammable\b",
        r"\bmethane\b",
        r"\bnatural gas\b",
    ],

    "Pinch / caught-between": [
        r"\bcaught between\b",
        r"\bpinched between\b",
        r"\btrapped between\b",
        r"\bcaught[- ]in\b",
        r"\bcrushed between\b",
    ],

    "Stored / mechanical energy": [
        r"\bspring[- ]loaded\b",
        r"\bpressurized\b",
        r"\bstored energy\b",
        r"\bpneumatic\b",
        r"\bhydraulic\b",
    ],
}


# =========================================================
# EXPOSURE
# =========================================================

EXPOSURES = {
    "Worker in line of fire": [
        r"\bstruck\b",
        r"\bhit\b",
        r"\bran over\b",
        r"\bcaught between\b",
        r"\bpinched between\b",
        r"\bcrushed between\b",
        r"\bfalling\b.{0,80}\b(employee|worker)\b",
    ],

    "Hand/finger exposed to moving equipment": [
        r"\bfinger\b.{0,100}\b(caught|pinched|crushed|amputat)",
        r"\bhand\b.{0,100}\b(caught|pinched|crushed|amputat)",
    ],

    "Body exposed to vehicle path": [
        (
            r"\b(employee|worker)\b.{0,100}"
            r"\b(struck|hit|ran over)\b"
            r".{0,100}"
            r"\b(forklift|vehicle|truck|pickup|car|van)\b"
        ),
        (
            r"\b(forklift|vehicle|truck|pickup)\b"
            r".{0,100}"
            r"\b(struck|hit|ran over|backed into)\b"
            r".{0,100}"
            r"\b(employee|worker)\b"
        ),
    ],

    "Fall exposure": [
        r"\bfell\b",
        r"\bfall(?:ed|ing)?\b",
    ],

    "Exposure to electrical energy": [
        r"\barc flash\b",
        r"\belectrical arc\b",
        r"\belectrical shock\b",
        r"\benergized\b",
    ],

    "Exposure to fire/explosion": [
        r"\bexplosion\b",
        r"\bfire\b",
        r"\bignit",
        r"\bflammable\b",
    ],

    "Exposure to suspended/falling load": [
        r"\bsuspended\b.{0,80}\b(load|object)\b",
        r"\bfalling\b.{0,100}\b(pipe|beam|load|object|material)\b",
        r"\bdropped\b.{0,100}\b(load|object|material)\b",
    ],
}


# =========================================================
# BARRIER
# =========================================================

BARRIERS = {
    "Vehicle segregation / traffic control": [
        r"\bforklift\b",
        r"\bvehicle\b",
        r"\btruck\b",
        r"\bbacking\b",
        r"\breversing\b",
    ],

    "Machine guarding / hands-clear control": [
        r"\bconveyor\b",
        r"\bsaw\b",
        r"\bblade\b",
        r"\broller\b",
        r"\bpress\b",
        r"\blathe\b",
        r"\bgrinder\b",
        r"\brouter\b",
        r"\bcaught\b",
        r"\bpinched\b",
    ],

    "Fall protection / safe access": [
        r"\broof\b",
        r"\bladder\b",
        r"\bscaffold\b",
        r"\btower\b",
        r"\bplatform\b",
    ],

    "Load control / exclusion zone": [
        r"\bcrane\b",
        r"\bhoist\b",
        r"\bload\b",
        r"\bbeam\b",
        r"\bsuspended\b",
    ],

    "Electrical isolation": [
        r"\blockout\b",
        r"\btagout\b",
        r"\bde[- ]energized\b",
        r"\benergized\b",
        r"\barc flash\b",
    ],

    "Stored-energy control": [
        r"\bspring[- ]loaded\b",
        r"\bpressurized\b",
        r"\bpneumatic\b",
        r"\bhydraulic\b",
        r"\bstored energy\b",
    ],
}


# =========================================================
# BARRIER FAILURE
# =========================================================

BARRIER_FAILURES = {
    "Vehicle segregation / traffic control": [
        (
            "Worker was struck or exposed to a vehicle path",
            [
                r"\bforklift\b.{0,100}\bstruck\b",
                r"\bvehicle\b.{0,100}\bstruck\b",
                r"\bbacked into\b.{0,100}\b(employee|worker)\b",
                r"\bran over\b",
            ],
        ),
    ],

    "Machine guarding / hands-clear control": [
        (
            "Worker entered a machinery hazard zone",
            [
                r"\bcaught\b",
                r"\bpinched\b",
                r"\bcrushed\b",
                r"\bamputat",
            ],
        ),
    ],

    "Fall protection / safe access": [
        (
            "Fall occurred from elevated work or access",
            [
                r"\bfell\b",
                r"\bfall\b",
            ],
        ),
    ],

    "Load control / exclusion zone": [
        (
            "Load moved or fell into the worker's exposure zone",
            [
                r"\bload\b.{0,100}\bfall",
                r"\bbeam\b.{0,100}\bfall",
                r"\bstruck\b",
                r"\bcaught\b",
            ],
        ),
    ],

    "Electrical isolation": [
        (
            "Electrical energy was present during the work",
            [
                r"\barc flash\b",
                r"\belectrical arc\b",
                r"\benergized\b",
            ],
        ),
    ],

    "Stored-energy control": [
        (
            "Stored or mechanical energy was released unexpectedly",
            [
                r"\bspring[- ]loaded\b",
                r"\bpressurized\b",
                r"\bpneumatic\b",
                r"\bhydraulic\b",
                r"\bstored energy\b",
            ],
        ),
    ],
}


# =========================================================
# Extraction helpers
# =========================================================

def extract_category(
    text: str,
    mapping: dict[str, list[str]],
) -> tuple[str, str]:

    labels = []
    evidence = []

    for label, patterns in mapping.items():

        match_evidence = find_evidence(
            text,
            patterns,
        )

        if match_evidence:

            labels.append(label)

            evidence.append(
                f"{label}: {match_evidence}"
            )

    return (
        "; ".join(labels[:3]),
        " | ".join(evidence[:3]),
    )


def extract_barrier(
    text: str,
) -> tuple[str, str, str]:

    for barrier, patterns in BARRIERS.items():

        evidence = find_evidence(
            text,
            patterns,
        )

        if evidence:

            explicit = has_match(
                text,
                [
                    r"\blockout\b",
                    r"\btagout\b",
                    r"\bguard\b",
                    r"\bsafety line\b",
                    r"\bfall protection\b",
                    r"\bsafety harness\b",
                    r"\bspotter\b",
                    r"\btraffic control\b",
                    r"\bexclusion zone\b",
                ],
            )

            status = (
                "observed"
                if explicit
                else "inferred"
            )

            return (
                barrier,
                evidence,
                status,
            )

    return (
        "",
        "",
        "unknown",
    )


def extract_barrier_failure(
    text: str,
    barrier: str,
) -> tuple[str, str, str]:

    if not barrier:

        return (
            "",
            "",
            "unknown",
        )

    candidates = (
        BARRIER_FAILURES
        .get(barrier, [])
    )

    for description, patterns in candidates:

        evidence = find_evidence(
            text,
            patterns,
        )

        if evidence:

            explicit = has_match(
                text,
                [
                    r"\bsnapped\b",
                    r"\bbroke\b",
                    r"\bfailed\b",
                    r"\bmalfunction",
                    r"\bguard was removed\b",
                    r"\bnot locked out\b",
                    r"\bnot de[- ]energized\b",
                    r"\bbypassed\b",
                ],
            )

            status = (
                "observed"
                if explicit
                else "inferred"
            )

            return (
                description,
                evidence,
                status,
            )

    return (
        "",
        "",
        "unknown",
    )


def extract(text: str) -> dict:

    activity, activity_evidence = extract_category(
        text,
        ACTIVITIES,
    )

    hazard, hazard_evidence = extract_category(
        text,
        HAZARDS,
    )

    exposure, exposure_evidence = extract_category(
        text,
        EXPOSURES,
    )

    barrier, barrier_evidence, barrier_status = (
        extract_barrier(text)
    )

    (
        barrier_failure,
        barrier_failure_evidence,
        barrier_failure_status,
    ) = extract_barrier_failure(
        text,
        barrier,
    )

    return {
        "activity": activity,
        "activity_evidence": activity_evidence,

        "hazard": hazard,
        "hazard_evidence": hazard_evidence,

        "exposure": exposure,
        "exposure_evidence": exposure_evidence,

        "barrier": barrier,
        "barrier_evidence": barrier_evidence,
        "barrier_status": barrier_status,

        "barrier_failure": barrier_failure,
        "barrier_failure_evidence":
            barrier_failure_evidence,
        "barrier_failure_status":
            barrier_failure_status,
    }


# =========================================================
# Production pipeline function
# =========================================================

def extract_precursors(
    canonical_path: str | Path,
    output_path: str | Path,
) -> Path:

    canonical_path = Path(canonical_path)
    output_path = Path(output_path)

    if not canonical_path.exists():
        raise FileNotFoundError(
            f"Canonical dataset not found: "
            f"{canonical_path}"
        )

    df = pd.read_csv(
        canonical_path,
        low_memory=False,
    )

    required = {
        "report_id",
        "description",
        "nature",
        "event",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Missing precursor input columns: "
            f"{sorted(missing)}"
        )

    print(
        f"Loaded {len(df):,} reports."
    )

    rows = []

    for _, row in df.iterrows():

        text = normalize(
            " ".join(
                [
                    str(row.get("description", "")),
                    str(row.get("nature", "")),
                    str(row.get("event", "")),
                ]
            )
        )

        features = extract(text)

        rows.append(
            {
                "report_id": str(
                    row["report_id"]
                ),

                "activity":
                    features["activity"],
                "activity_evidence":
                    features["activity_evidence"],

                "hazard":
                    features["hazard"],
                "hazard_evidence":
                    features["hazard_evidence"],

                "exposure":
                    features["exposure"],
                "exposure_evidence":
                    features["exposure_evidence"],

                "barrier":
                    features["barrier"],
                "barrier_evidence":
                    features["barrier_evidence"],
                "barrier_status":
                    features["barrier_status"],

                "barrier_failure":
                    features["barrier_failure"],
                "barrier_failure_evidence":
                    features["barrier_failure_evidence"],
                "barrier_failure_status":
                    features["barrier_failure_status"],
            }
        )

    output = pd.DataFrame(rows)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nReports processed: "
        f"{len(output):,}"
    )

    for field in [
        "activity",
        "hazard",
        "exposure",
        "barrier",
        "barrier_failure",
    ]:

        coverage = (
            output[field]
            .fillna("")
            .str.len()
            > 0
        ).sum()

        percentage = (
            coverage / len(output) * 100
            if len(output)
            else 0.0
        )

        print(
            f"{field:20s}: "
            f"{coverage:6,d} "
            f"({percentage:5.1f}%)"
        )

    print("\nBarrier status:")

    print(
        output["barrier_status"]
        .value_counts()
        .to_string()
    )

    print("\nBarrier failure status:")

    print(
        output[
            "barrier_failure_status"
        ]
        .value_counts()
        .to_string()
    )

    print(
        f"\nSaved: {output_path}"
    )

    return output_path


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Extract SIF precursor features "
            "from a canonical dataset."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
    )

    parser.add_argument(
        "output",
        type=Path,
    )

    args = parser.parse_args()

    extract_precursors(
        args.input,
        args.output,
    )
