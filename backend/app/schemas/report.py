from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    data_source: str | None
    report_type: str | None
    event_date: date | None
    employer: str | None
    city: str | None
    state: str | None
    naics: str | None
    candidate_oil_gas: int
    description: str
    nature: str | None
    event: str | None


class ReportSummary(BaseModel):
    report_id: str
    description: str

    event_date: date | None = None
    employer: str | None = None
    city: str | None = None
    state: str | None = None

    sif_probability: float | None = None
    sif_label: str | None = None

    activity: str | None = None
    hazard: str | None = None

    life_saving_rules: list[str] = Field(default_factory=list)

    priority_score: float | None = None
    priority_band: str | None = None


class PaginatedReports(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    reports: list[ReportSummary]


class SimilarReport(BaseModel):
    report_id: str
    similarity: float

    event_date: date | None = None
    employer: str | None = None
    city: str | None = None
    state: str | None = None
    description: str | None = None

    sif_probability: float | None = None
    sif_label: str | None = None

    life_saving_rules: list[str] = Field(default_factory=list)

    activity: str | None = None
    hazard: str | None = None
    exposure: str | None = None
    barrier: str | None = None
    barrier_failure: str | None = None

    priority_score: float | None = None
    priority_band: str | None = None