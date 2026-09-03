#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


# =========================================================
# IOGP Life-Saving Rules
# =========================================================

LSR_NAMES = [
    "Bypassing Safety Controls",
    "Confined Space",
    "Driving",
    "Energy Isolation",
    "Hot Work",
    "Line of Fire",
    "Safe Mechanical Lifting",
    "Work Authorisation",
    "Working at Height",
]


def normalize(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_any(
    text: str,
    patterns: list[str],
) -> bool:
    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


# =========================================================
# RULES
# =========================================================

WORKING_AT_HEIGHT = [
    r"\bworking from a roof\b",
    r"\bworking on a roof\b",
    r"\broof\b.{0,100}\b(fell|fall|ladder)\b",
    r"\bscaffold\b.{0,100}\b(fell|fall|working|employee)\b",
    r"\bfall(?:ed|ing)?\b.{0,100}\b(?:ladder|scaffold|tower|platform)\b",
    r"\b(?:ladder|scaffold|tower|platform)\b.{0,100}\bfall(?:ed|ing)?\b",
    r"\b\d+\s*(?:ft|feet)\b.{0,80}\b(fell|fall|dropped)\b",
    r"\b(fell|fall(?:ed|ing)?)\b.{0,80}\b\d+\s*(?:ft|feet)\b",
]


DRIVING = [
    r"\bforklift\b.{0,120}\b(struck|hit|backed|collision|collid|ran over|pinned)\b",
    (
        r"\b(forklift|reach forklift|walkie rider|pallet jack|"
        r"powered industrial truck|pit)\b"
        r".{0,120}\b(operator|operating|driving|backing|turning)\b"
    ),
    (
        r"\b(vehicle|truck|pickup|van|car|bus)\b"
        r".{0,120}\b(struck|hit|backed|collision|collid|ran over)\b"
    ),
    (
        r"\b(employee|worker)\b.{0,100}\bstruck\b"
        r".{0,100}\b(vehicle|truck|pickup|car|van|bus)\b"
    ),
    (
        r"\b(backing|reversing)\b.{0,120}"
        r"\b(vehicle|truck|forklift|pickup)\b"
    ),
]


LINE_OF_FIRE = [
    r"\bcaught between\b",
    r"\bpinched between\b",
    r"\btrapped between\b",
    r"\bcrushed between\b",
    r"\bcaught[- ]in\b",
    (
        r"\b(falling|dropped)\b.{0,100}"
        r"\b(pipe|beam|object|load|material|equipment|carrier)\b"
        r".{0,100}\b(employee|worker)\b"
    ),
    (
        r"\b(employee|worker)\b.{0,100}"
        r"\b(struck|hit|crushed)\b"
        r".{0,100}\b(falling|dropped|moving)\b"
    ),
    (
        r"\b(forklift|vehicle|truck|equipment)\b"
        r".{0,100}\b(struck|hit|ran over|backed into)\b"
        r".{0,100}\b(employee|worker)\b"
    ),
    (
        r"\bfinger\b.{0,100}"
        r"\b(amputat|pinched|caught|crushed|trapped)\b"
    ),
    (
        r"\bhand\b.{0,100}"
        r"\b(amputat|pinched|caught|crushed|trapped)\b"
    ),
    (
        r"\bfoot\b.{0,100}"
        r"\b(amputat|pinched|caught|crushed|trapped)\b"
    ),
    (
        r"\bsuspended\b.{0,100}\b(load|object)\b"
        r".{0,100}\b(employee|worker)\b"
    ),
]


SAFE_MECHANICAL_LIFTING = [
    (
        r"\bcrane\b.{0,120}"
        r"\b(lift|lifting|lowering|load|beam|equipment|material)\b"
    ),
    (
        r"\b(lift|lifting|hoist|hoisting)\b.{0,100}"
        r"\b(crane|rig|load|beam|equipment|material)\b"
    ),
    (
        r"\bforklift\b.{0,120}"
        r"\b(lift|lifting|load|beam|carrier|material)\b"
    ),
    (
        r"\b(load|beam|carrier|material)\b.{0,120}"
        r"\b(forklift|crane|hoist)\b"
    ),
    r"\b(overhead crane|bridge crane|gantry crane|rig blocks)\b",
]


ENERGY_ISOLATION = [
    r"\blockout\b",
    r"\block[- ]out\b",
    r"\btagout\b",
    r"\blockout/tagout\b",
    r"\bnot locked out\b",
    r"\bnot de[- ]energized\b",
    (
        r"\benergized\b.{0,120}"
        r"\b(equipment|panel|machine|circuit|line|system)\b"
    ),
    r"\belectrical arc\b",
    r"\barc flash\b",
    r"\bpneumatic ram\b.{0,100}\b(caught|pinched|crushed)\b",
    r"\bstored energy\b",
    r"\bpressurized\b.{0,100}\b(release|struck|failed|hit)\b",
]


HOT_WORK = [
    r"\bwelding\b",
    r"\bwelding operations\b",
    r"\bcutting with a torch\b",
    r"\btorch cutting\b",
    r"\bhot work\b",
    r"\bgrinding\b.{0,100}\b(spark|ignit|fire)\b",
    (
        r"\bcutting\b.{0,100}"
        r"\b(ignite|ignition|natural gas|flammable gas)\b"
    ),
    (
        r"\b(flame|spark)\b.{0,100}"
        r"\b(ignit|fire|explosion)\b"
    ),
]


CONFINED_SPACE = [
    r"\bconfined space\b",
    r"\bentering a tank\b",
    r"\bentered a tank\b",
    r"\binside a tank\b",
    r"\binside a vessel\b",
    r"\bmanhole\b.{0,100}\b(entry|entered|inside)\b",
]


BYPASSING_CONTROLS = [
    (
        r"\bbypass(?:ed|ing)?\b.{0,100}"
        r"\b(safety|guard|interlock|control)\b"
    ),
    (
        r"\bguard\b.{0,100}"
        r"\b(remove|removed|missing|bypass)\b"
    ),
    (
        r"\binterlock\b.{0,100}"
        r"\b(bypass|disabled|defeat)\b"
    ),
    (
        r"\bsafety control\b.{0,100}"
        r"\b(bypass|disabled|defeat)\b"
    ),
    (
        r"\bdisabled\b.{0,100}"
        r"\b(interlock|guard|safety control)\b"
    ),
]


WORK_AUTHORISATION = [
    r"\bpermit to work\b",
    r"\bwork permit\b",
    r"\bhot work permit\b",
    r"\bconfined space permit\b",
    r"\bpermit required\b",
    r"\bnot authorized\b",
    r"\bunauthorized\b.{0,100}\bwork\b",
]


RULES = {
    "Bypassing Safety Controls": BYPASSING_CONTROLS,
    "Confined Space": CONFINED_SPACE,
    "Driving": DRIVING,
    "Energy Isolation": ENERGY_ISOLATION,
    "Hot Work": HOT_WORK,
    "Line of Fire": LINE_OF_FIRE,
    "Safe Mechanical Lifting": SAFE_MECHANICAL_LIFTING,
    "Work Authorisation": WORK_AUTHORISATION,
    "Working at Height": WORKING_AT_HEIGHT,
}


def classify_lsr(
    text: str,
) -> tuple[str, float, str]:

    matched = []
    reasons = []

    for rule_name, patterns in RULES.items():

        if has_any(text, patterns):

            matched.append(rule_name)
            reasons.append(rule_name)

    if not matched:
        return (
            "",
            0.0,
            "no_high_confidence_lsr",
        )

    if len(matched) >= 2:
        confidence = 0.92
    else:
        confidence = 0.90

    return (
        ";".join(matched),
        confidence,
        ";".join(reasons),
    )


def map_lsr(
    canonical_path: str | Path,
    output_path: str | Path,
) -> Path:

    canonical_path = Path(canonical_path)
    output_path = Path(output_path)

    if not canonical_path.exists():
        raise FileNotFoundError(
            f"Canonical dataset not found: {canonical_path}"
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
            "Missing LSR input columns: "
            f"{sorted(missing)}"
        )

    print(
        f"Loaded {len(df):,} OSHA-format reports."
    )

    descriptions = (
        df["description"]
        .fillna("")
        .astype(str)
    )

    natures = (
        df["nature"]
        .fillna("")
        .astype(str)
    )

    events = (
        df["event"]
        .fillna("")
        .astype(str)
    )

    text = (
        descriptions
        + " "
        + natures
        + " "
        + events
    ).map(normalize)

    results = text.apply(classify_lsr)

    labels = pd.DataFrame(
        results.tolist(),
        columns=[
            "life_saving_rules",
            "lsr_confidence",
            "lsr_reason",
        ],
        index=df.index,
    )

    output = pd.concat(
        [
            df[
                [
                    "report_id",
                    "description",
                    "nature",
                    "event",
                ]
            ],
            labels,
        ],
        axis=1,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        output_path,
        index=False,
    )

    with_lsr = (
        output["life_saving_rules"]
        .fillna("")
        .str.len()
        > 0
    )

    print(
        f"\nReports with at least one LSR: "
        f"{with_lsr.sum():,}"
    )

    print("\nLSR counts:")

    exploded = (
        output.loc[
            with_lsr,
            "life_saving_rules",
        ]
        .str.split(";")
        .explode()
    )

    if not exploded.empty:
        print(
            exploded.value_counts()
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
            "Map IOGP Life-Saving Rules "
            "onto a canonical report dataset."
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

    map_lsr(
        args.input,
        args.output,
    )
