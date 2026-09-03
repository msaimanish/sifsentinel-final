from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_reports: int
    sif_potential: int
    high_priority: int
    critical_priority: int