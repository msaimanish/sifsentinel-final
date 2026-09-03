from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class ReportIntelligence(Base):
    __tablename__ = "report_intelligence"

    id = Column(Integer, primary_key=True, index=True)

    report_id = Column(String, unique=True, index=True, nullable=False)

    # SIF model output
    sif_probability = Column(Float, nullable=True)
    sif_label = Column(String, nullable=True)

    # Safety intelligence
    life_saving_rules = Column(JSONB, nullable=True)
    activity = Column(String, nullable=True)
    hazard = Column(String, nullable=True)
    exposure = Column(String, nullable=True)
    barrier = Column(String, nullable=True)
    barrier_failure = Column(String, nullable=True)

    # Risk engine
    priority_score = Column(Float, nullable=True)
    priority_band = Column(String, nullable=True)

    # Keep the complete derived row available
    payload = Column(JSONB, nullable=True)
