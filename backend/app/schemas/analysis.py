from datetime import date

from pydantic import BaseModel, Field


class AnalysisReport(BaseModel):
    report_id: str
    event_date: date | None
    employer: str | None
    city: str | None
    state: str | None
    naics: str | None
    event: str | None
    nature: str | None
    description: str


class SIFAssessment(BaseModel):
    probability: float | None
    label: str | None
    model_version: str | None


class SafetyFeatures(BaseModel):
    activity: str | None
    hazards: list[str] = Field(default_factory=list)
    exposure: str | None
    barriers: list[str] = Field(default_factory=list)
    barrier_failures: list[str] = Field(default_factory=list)
    life_saving_rules: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    score: float | None = None
    band: str | None = None


class SimilarReport(BaseModel):
    report_id: str
    similarity: float


class AnalysisStatus(BaseModel):
    has_prediction: bool
    has_embedding: bool
    has_intelligence: bool


class AnalysisResponse(BaseModel):
    report: AnalysisReport
    sif_assessment: SIFAssessment
    safety_features: SafetyFeatures
    risk: RiskAssessment
    similar_reports: list[SimilarReport]
    status: AnalysisStatus