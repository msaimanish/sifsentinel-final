from math import ceil
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report
from app.models.intelligence import ReportIntelligence

from app.schemas.report import (
    PaginatedReports,
    ReportResponse,
    ReportSummary,
)

from app.services.similarity_service import find_similar_reports
from app.services.analysis_service import build_analysis
from app.schemas.analysis import AnalysisResponse


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


LSR_OPTIONS = [
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


@router.get(
    "",
    response_model=PaginatedReports,
)
def get_reports(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    risk: str | None = None,
    sif: str | None = None,
    lsr: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Server-side report listing, searching, filtering and pagination.
    """

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    # ---------------------------------------------------------
    # BASE QUERY
    # ---------------------------------------------------------

    base = (
        select(Report)
        .outerjoin(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
    )

    filters = []

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    if search and search.strip():
        query = f"%{search.strip()}%"

        filters.append(
            or_(
                cast(Report.report_id, String).ilike(query),
                Report.description.ilike(query),
                Report.employer.ilike(query),
                Report.city.ilike(query),
                Report.state.ilike(query),
                ReportIntelligence.activity.ilike(query),
                ReportIntelligence.hazard.ilike(query),
            )
        )

    # ---------------------------------------------------------
    # RISK FILTER
    # ---------------------------------------------------------

    if risk and risk != "All":
        filters.append(
            ReportIntelligence.priority_band == risk
        )

    # ---------------------------------------------------------
    # SIF FILTER
    # ---------------------------------------------------------

    if sif and sif != "All":
        filters.append(
            ReportIntelligence.sif_label == sif
        )

    # ---------------------------------------------------------
    # LSR FILTER
    # ---------------------------------------------------------

    if lsr and lsr != "All":
        filters.append(
            cast(
                ReportIntelligence.life_saving_rules,
                String,
            ).ilike(f"%{lsr}%")
        )

    # ---------------------------------------------------------
    # TOTAL COUNT
    # ---------------------------------------------------------

    count_statement = (
        select(func.count())
        .select_from(Report)
        .outerjoin(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .where(*filters)
    )

    total = db.scalar(count_statement) or 0

    total_pages = max(
        1,
        ceil(total / page_size),
    )

    # If the requested page is beyond the end,
    # clamp it to the final page.
    page = min(page, total_pages)

    offset = (page - 1) * page_size

    # ---------------------------------------------------------
    # FETCH CURRENT PAGE
    # ---------------------------------------------------------

    statement = (
        select(
            Report.report_id,
            Report.description,
            Report.event_date,
            Report.employer,
            Report.city,
            Report.state,
            ReportIntelligence.sif_probability,
            ReportIntelligence.sif_label,
            ReportIntelligence.activity,
            ReportIntelligence.hazard,
            ReportIntelligence.life_saving_rules,
            ReportIntelligence.priority_score,
            ReportIntelligence.priority_band,
        )
        .outerjoin(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .where(*filters)
        .order_by(
            Report.event_date.desc().nullslast(),
            Report.report_id.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )

    rows = db.execute(statement).all()

    results = []

    for row in rows:
        rules = row.life_saving_rules

        if not isinstance(rules, list):
            rules = []

        results.append(
            ReportSummary(
                report_id=str(row.report_id),
                description=row.description,
                event_date=row.event_date,
                employer=row.employer,
                city=row.city,
                state=row.state,
                sif_probability=row.sif_probability,
                sif_label=row.sif_label,
                activity=row.activity,
                hazard=row.hazard,
                life_saving_rules=rules,
                priority_score=row.priority_score,
                priority_band=row.priority_band,
            )
        )

    return PaginatedReports(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        reports=results,
    )

@router.get("/export")
def export_reports(
    search: str | None = None,
    risk: str | None = None,
    sif: str | None = None,
    lsr: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Export all analysed reports as CSV.

    The current search/filter conditions are preserved,
    but pagination is intentionally ignored.
    """

    filters = []

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    if search and search.strip():
        query = f"%{search.strip()}%"

        filters.append(
            or_(
                cast(Report.report_id, String).ilike(query),
                Report.description.ilike(query),
                Report.employer.ilike(query),
                Report.city.ilike(query),
                Report.state.ilike(query),
                ReportIntelligence.activity.ilike(query),
                ReportIntelligence.hazard.ilike(query),
            )
        )

    # ---------------------------------------------------------
    # RISK FILTER
    # ---------------------------------------------------------

    if risk and risk != "All":
        filters.append(
            ReportIntelligence.priority_band == risk
        )

    # ---------------------------------------------------------
    # SIF FILTER
    # ---------------------------------------------------------

    if sif and sif != "All":
        filters.append(
            ReportIntelligence.sif_label == sif
        )

    # ---------------------------------------------------------
    # LSR FILTER
    # ---------------------------------------------------------

    if lsr and lsr != "All":
        filters.append(
            cast(
                ReportIntelligence.life_saving_rules,
                String,
            ).ilike(f"%{lsr}%")
        )

    # ---------------------------------------------------------
    # ONLY ANALYSED REPORTS
    # ---------------------------------------------------------

    filters.append(
        ReportIntelligence.report_id.is_not(None)
    )

    # ---------------------------------------------------------
    # FETCH ALL ANALYSED REPORTS
    # ---------------------------------------------------------

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
            ReportIntelligence.life_saving_rules,
            ReportIntelligence.priority_score,
            ReportIntelligence.priority_band,
        )
        .join(
            ReportIntelligence,
            ReportIntelligence.report_id == Report.report_id,
        )
        .where(*filters)
        .order_by(
            Report.event_date.desc().nullslast(),
            Report.report_id.desc(),
        )
    )

    rows = db.execute(statement).all()

    # ---------------------------------------------------------
    # BUILD CSV
    # ---------------------------------------------------------

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(
        [
            "Report ID",
            "Event Date",
            "Employer",
            "City",
            "State",
            "Description",
            "SIF Probability",
            "SIF Label",
            "Activity",
            "Hazard",
            "Life-Saving Rules",
            "Priority Score",
            "Priority Band",
        ]
    )

    for row in rows:
        rules = row.life_saving_rules

        if isinstance(rules, list):
            rules_text = "; ".join(str(rule) for rule in rules)
        else:
            rules_text = ""

        writer.writerow(
            [
                str(row.report_id),
                row.event_date.isoformat()
                if row.event_date
                else "",
                row.employer or "",
                row.city or "",
                row.state or "",
                row.description or "",
                row.sif_probability
                if row.sif_probability is not None
                else "",
                row.sif_label or "",
                row.activity or "",
                row.hazard or "",
                rules_text,
                row.priority_score
                if row.priority_score is not None
                else "",
                row.priority_band or "",
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="analysed_reports.csv"'
            )
        },
    )


@router.get(
    "/{report_id}/similar",
)
def get_similar_reports(
    report_id: str,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    report = db.scalar(
        select(Report).where(
            Report.report_id == report_id
        )
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    limit = min(max(limit, 1), 20)

    results = find_similar_reports(
        db=db,
        report_id=report.id,
        limit=limit,
    )

    return {
        "report_id": report.report_id,
        "similar_reports": results,
    }


@router.get(
    "/{report_id}/analysis",
    response_model=AnalysisResponse,
)
def get_report_analysis(
    report_id: str,
    db: Session = Depends(get_db),
):
    result = build_analysis(
        db=db,
        report_id=report_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return result


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = db.scalar(
        select(Report).where(
            Report.report_id == report_id
        )
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report