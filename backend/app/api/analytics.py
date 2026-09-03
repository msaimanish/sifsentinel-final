from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.intelligence import ReportIntelligence


# ============================================================
# OVERVIEW
# ============================================================

def get_overview(db: Session):
    total_reports = db.scalar(
        select(func.count(Report.id))
    ) or 0

    sif_potential = db.scalar(
        select(func.count(ReportIntelligence.id))
        .where(
            ReportIntelligence.sif_label.in_(
                ["YES", "Yes", "yes", "SIF", "SIF-Potential"]
            )
        )
    ) or 0

    high_priority = db.scalar(
        select(func.count(ReportIntelligence.id))
        .where(
            ReportIntelligence.priority_band.in_(
                ["High", "Critical"]
            )
        )
    ) or 0

    critical_priority = db.scalar(
        select(func.count(ReportIntelligence.id))
        .where(
            ReportIntelligence.priority_band == "Critical"
        )
    ) or 0

    return {
        "total_reports": total_reports,
        "sif_potential": sif_potential,
        "high_priority": high_priority,
        "critical_priority": critical_priority,
    }


# ============================================================
# TRENDS
# ============================================================

def get_trends(db: Session):
    statement = (
        select(
            func.extract(
                "year",
                ReportIntelligence.report_id
            )
        )
    )

    # We use event_date from Report because it is the
    # canonical report date.

    statement = (
        select(
            func.extract(
                "year",
                Report.event_date
            ).label("year"),

            func.count(Report.id).label("reports"),

            func.count(
                ReportIntelligence.id
            ).filter(
                ReportIntelligence.sif_label.in_(
                    ["YES", "Yes", "yes"]
                )
            ).label("sif_potential"),

        )
        .join(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .group_by(
            func.extract(
                "year",
                Report.event_date
            )
        )
        .order_by(
            func.extract(
                "year",
                Report.event_date
            )
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "year": int(row.year),
            "reports": int(row.reports),
            "sif_potential": int(row.sif_potential),
        }
        for row in rows
        if row.year is not None
    ]


# ============================================================
# TOP ACTIVITIES
# ============================================================

def get_activities(
    db: Session,
    limit: int = 10,
):
    statement = (
        select(
            ReportIntelligence.activity.label("activity"),

            func.count(
                ReportIntelligence.id
            ).label("count"),

            func.avg(
                ReportIntelligence.priority_score
            ).label("priority_score"),

        )
        .where(
            ReportIntelligence.activity.is_not(None),
            ReportIntelligence.activity != "",
        )
        .group_by(
            ReportIntelligence.activity
        )
        .order_by(
            func.avg(
                ReportIntelligence.priority_score
            ).desc()
            .nullslast()
        )
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        {
            "activity": row.activity,
            "count": int(row.count),
            "priority_score": (
                round(float(row.priority_score), 4)
                if row.priority_score is not None
                else None
            ),
        }
        for row in rows
    ]


# ============================================================
# TOP LOCATIONS
# ============================================================

def get_locations(
    db: Session,
    limit: int = 10,
):
    statement = (
        select(
            Report.city.label("location"),

            func.count(
                Report.id
            ).label("count"),

            func.avg(
                ReportIntelligence.priority_score
            ).label("priority_score"),

        )
        .join(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .where(
            Report.city.is_not(None),
            Report.city != "",
        )
        .group_by(
            Report.city
        )
        .order_by(
            func.avg(
                ReportIntelligence.priority_score
            ).desc()
            .nullslast()
        )
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        {
            "location": row.location,
            "count": int(row.count),
            "priority_score": (
                round(float(row.priority_score), 4)
                if row.priority_score is not None
                else None
            ),
        }
        for row in rows
    ]


# ============================================================
# LIFE-SAVING RULES
# ============================================================

def get_lsr(
    db: Session,
    limit: int = 10,
):
    rows = db.execute(
        select(
            ReportIntelligence.life_saving_rules,
            ReportIntelligence.priority_score,
        )
        .where(
            ReportIntelligence.life_saving_rules.is_not(None)
        )
    ).all()

    counts = {}

    for rules, priority_score in rows:
        if not rules:
            continue

        if isinstance(rules, str):
            rules = [
                item.strip()
                for item in rules.split(";")
                if item.strip()
            ]

        if not isinstance(rules, list):
            continue

        for rule in rules:
            if rule not in counts:
                counts[rule] = {
                    "count": 0,
                    "priority_scores": [],
                }

            counts[rule]["count"] += 1

            if priority_score is not None:
                counts[rule]["priority_scores"].append(
                    float(priority_score)
                )

    results = []

    for rule, data in counts.items():
        scores = data["priority_scores"]

        results.append(
            {
                "rule": rule,
                "count": data["count"],
                "priority_score": (
                    round(
                        sum(scores) / len(scores),
                        4,
                    )
                    if scores
                    else None
                ),
            }
        )

    results.sort(
        key=lambda x: (
            x["priority_score"]
            if x["priority_score"] is not None
            else 0
        ),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# PRIORITY REPORTS
# ============================================================

def get_priority_reports(
    db: Session,
    limit: int = 10,
):
    statement = (
        select(
            Report.report_id,
            Report.event_date,
            Report.employer,
            Report.city,
            Report.state,
            Report.description,

            ReportIntelligence.sif_probability,
            ReportIntelligence.sif_label,

            ReportIntelligence.activity,
            ReportIntelligence.hazard,
            ReportIntelligence.barrier_failure,

            ReportIntelligence.priority_score,
            ReportIntelligence.priority_band,

        )
        .join(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .where(
            ReportIntelligence.priority_score.is_not(None)
        )
        .order_by(
            ReportIntelligence.priority_score.desc()
        )
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        {
            "report_id": row.report_id,
            "event_date": row.event_date,
            "employer": row.employer,
            "location": row.city,
            "state": row.state,
            "description": row.description,

            "sif_probability": row.sif_probability,
            "sif_label": row.sif_label,

            "activity": row.activity,
            "hazard": row.hazard,
            "barrier_failure": row.barrier_failure,

            "priority_score": row.priority_score,
            "priority_band": row.priority_band,
        }
        for row in rows
    ]

from fastapi import APIRouter, Depends, Query

from app.database import get_db


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
):
    return get_overview(db)


@router.get("/trends")
def trends(
    db: Session = Depends(get_db),
):
    return get_trends(db)


@router.get("/activities")
def activities(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_activities(
        db,
        limit=limit,
    )


@router.get("/locations")
def locations(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_locations(
        db,
        limit=limit,
    )


@router.get("/lsr")
def lsr(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_lsr(
        db,
        limit=limit,
    )


@router.get("/priority-reports")
def priority_reports(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_priority_reports(
        db,
        limit=limit,
    )

# ============================================================
# PRIORITY DISTRIBUTION
# ============================================================

def get_priority_distribution(db: Session):
    statement = (
        select(
            ReportIntelligence.priority_band,
            func.count(
                ReportIntelligence.id
            ).label("count"),
        )
        .where(
            ReportIntelligence.priority_band.is_not(None),
            ReportIntelligence.priority_band != "",
        )
        .group_by(
            ReportIntelligence.priority_band
        )
        .order_by(
            func.count(
                ReportIntelligence.id
            ).desc()
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "band": row.priority_band,
            "count": int(row.count),
        }
        for row in rows
    ]


@router.get("/priority-distribution")
def priority_distribution(
    db: Session = Depends(get_db),
):
    return get_priority_distribution(db)